#!/usr/bin/env python3
"""
Unified Agent Deployer for Universal Agent System

This module provides a single, unified deployment system that:
- Uses the universal agent template with dynamic Firestore configuration
- Applies LLM-based optimizations automatically for any domain
- Simplifies deployment to just requiring an agent_id
- Uses environment variables for configuration
"""

import os
import json
import logging
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from config_loader import load_agent_config

# Configure logging to show output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # This ensures logs go to stdout
    ]
)
logger = logging.getLogger(__name__)


class UniversalAgentDeployer:
    """
    Unified deployer for universal agents with dynamic optimization.
    
    This deployer:
    1. Uses environment variables for PROJECT_ID and other config
    2. Takes only agent_id as input parameter
    3. Uses the universal agent template with dynamic Firestore configuration
    4. Applies LLM-based optimizations automatically
    5. Builds and deploys to Google Cloud Run
    """
    
    def __init__(self):
        """Initialize the universal agent deployer."""
        # Load from .env file first
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get configuration from .env file
        self.project_id = os.getenv('PROJECT_ID') or os.getenv('project_id')
        if not self.project_id:
            raise ValueError("project_id must be set in .env file")
        
        self.region = os.getenv('REGION') or os.getenv('region', 'us-central1')
        
        # Check if running in container (Cloud Run) or locally
        if os.path.exists('/app/universal-agent'):
            # Running in Cloud Run container
            self.template_dir = Path('/app/universal-agent')
        else:
            # Running locally
            self.template_dir = Path(__file__).parent.parent / 'universal-agent'
        
        # Validate template directory exists
        if not self.template_dir.exists():
            raise ValueError(f"Universal agent template directory not found: {self.template_dir}")
        
        logger.info(f"Initialized Universal Agent Deployer for project: {self.project_id}")
    
    def deploy_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Deploy a universal agent with dynamic configuration and optimizations.
        
        Args:
            agent_id: The agent ID to deploy
            
        Returns:
            Deployment result with service URL and status
        """
        try:
            logger.info(f"🚀 Starting universal agent deployment for: {agent_id}")
            logger.info(f"📁 Template directory: {self.template_dir}")
            logger.info(f"🏗️ Project ID: {self.project_id}")
            logger.info(f"🌍 Region: {self.region}")
            
            # Step 1: Load and validate agent configuration
            logger.info("📋 Step 1: Loading and validating agent configuration...")
            agent_config = self._load_agent_config(agent_id)
            logger.info(f"✅ Agent config loaded successfully")
            
            # Step 2: Create deployment workspace
            logger.info("📂 Step 2: Creating deployment workspace...")
            deployment_dir = self._create_deployment_workspace(agent_id)
            logger.info(f"✅ Deployment workspace created: {deployment_dir}")
            
            try:
                # Step 3: Generate optimized agent code
                logger.info("🛠️ Step 3: Generating optimized agent code...")
                self._generate_agent_code(deployment_dir, agent_config)
                logger.info("✅ Agent code generation completed")
                
                # Step 4: Create deployment files
                logger.info("📄 Step 4: Creating deployment files...")
                self._create_deployment_files(deployment_dir, agent_config)
                logger.info("✅ Deployment files created")
                
                # Step 5: Build and deploy container
                logger.info("🐳 Step 5: Building and deploying container...")
                service_url = self._build_and_deploy(deployment_dir, agent_id)
                logger.info(f"✅ Container deployed successfully: {service_url}")
                
                # Step 6: Update agent status in Firestore
                logger.info("💾 Step 6: Updating agent status in Firestore...")
                self._update_agent_deployment_status(agent_id, 'completed', service_url)
                logger.info("✅ Agent status updated in Firestore")
                
                logger.info(f"🎉 Universal agent deployment completed: {service_url}")
                
                return {
                    'status': 'success',
                    'agent_id': agent_id,
                    'service_url': service_url,
                    'deployment_type': 'universal',
                    'optimizations_applied': bool(agent_config.get('_domain_info')),
                    'deployed_at': datetime.now(timezone.utc).isoformat()
                }
                
            finally:
                # Clean up deployment workspace
                if deployment_dir.exists():
                    shutil.rmtree(deployment_dir)
                    logger.info(f"Cleaned up deployment workspace: {deployment_dir}")
                
        except Exception as e:
            logger.error(f"Universal agent deployment failed for {agent_id}: {str(e)}")
            self._update_agent_deployment_status(agent_id, 'failed', None, str(e))
            raise
    
    def _load_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Load agent configuration with optimizations from Firestore."""
        try:
            logger.info(f"Loading configuration for agent: {agent_id}")
            config = load_agent_config(agent_id)
            
            # Validate required configuration
            if not config.get('agent_id'):
                raise ValueError("Agent configuration missing agent_id")
            
            logger.info(f"Configuration loaded with {len(config.get('_tool_optimizations', {}))} tool optimizations")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load agent configuration: {str(e)}")
            raise
    
    def _create_deployment_workspace(self, agent_id: str) -> Path:
        """Create a temporary deployment workspace."""
        workspace = Path(tempfile.mkdtemp(prefix=f"agent-{agent_id}-"))
        logger.info(f"Created deployment workspace: {workspace}")
        return workspace
    
    def _generate_agent_code(self, deployment_dir: Path, agent_config: Dict[str, Any]):
        """Generate optimized agent code in the deployment directory."""
        try:
            logger.info(f"📦 Generating optimized agent code from template: {self.template_dir}")
            
            # Verify template directory exists
            if not self.template_dir.exists():
                raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
            
            # Copy universal agent template files
            template_files = [
                ('main.py', 'main.py'),  # (source, destination)
                ('config_loader.py', 'config_loader.py'), 
                ('mcp_tool.py', 'mcp_tool.py'),
                ('embedded_vector_search.py', 'embedded_vector_search.py'),
                ('knowledge_service.py', 'knowledge_service.py'),
                ('requirements.txt', 'requirements.txt'),
                ('Dockerfile', 'Dockerfile')
            ]
            
            logger.info(f"📋 Template files to copy: {[f[0] for f in template_files]}")
            
            # Copy optional files if they exist
            optional_files = [
                'firebase-credentials.json',
                '.gitignore',
                '.dockerignore'
            ]
            
            # Copy template files
            copied_files = 0
            for src_name, dst_name in template_files:
                src_file = self.template_dir / src_name
                if src_file.exists():
                    dst_file = deployment_dir / dst_name
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"✅ Copied template file: {src_name} -> {dst_name}")
                    copied_files += 1
                else:
                    logger.warning(f"⚠️ Template file not found: {src_name}")
            
            logger.info(f"📊 Copied {copied_files}/{len(template_files)} template files")
            
            # Copy optional files if they exist
            optional_copied = 0
            for file_name in optional_files:
                src_file = self.template_dir / file_name
                if src_file.exists():
                    dst_file = deployment_dir / file_name
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"✅ Copied optional file: {file_name}")
                    optional_copied += 1
                else:
                    logger.debug(f"Optional file not found: {file_name}")
            
            logger.info(f"📊 Copied {optional_copied}/{len(optional_files)} optional files")
            
            # Copy config and services directories
            dirs_copied = 0
            for dir_name in ['config', 'services']:
                src_dir = self.template_dir / dir_name
                if src_dir.exists():
                    dst_dir = deployment_dir / dir_name
                    shutil.copytree(src_dir, dst_dir)
                    logger.info(f"✅ Copied directory: {dir_name}")
                    dirs_copied += 1
                else:
                    logger.debug(f"Optional directory not found: {dir_name}")
            
            logger.info(f"📊 Copied {dirs_copied}/2 directories")
            
            # Create environment configuration
            self._create_environment_config(deployment_dir, agent_config)
            
            logger.info("Agent code generation completed")
            
        except Exception as e:
            logger.error(f"Failed to generate agent code: {str(e)}")
            raise
    
    def _create_environment_config(self, deployment_dir: Path, agent_config: Dict[str, Any]):
        """Create environment configuration for the agent."""
        try:
            # Create .env file for the deployed agent
            openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('openai_api_key', '')
            env_content = f"""# Universal Agent Environment Configuration
AGENT_ID={agent_config['agent_id']}
PROJECT_ID={self.project_id}
OPENAI_API_KEY={openai_key}
FIREBASE_CREDENTIALS=/app/firebase-credentials.json
"""
            
            env_file = deployment_dir / '.env'
            env_file.write_text(env_content)
            
            logger.info("Environment configuration created")
            
        except Exception as e:
            logger.error(f"Failed to create environment config: {str(e)}")
            raise
    
    def _create_deployment_files(self, deployment_dir: Path, agent_config: Dict[str, Any]):
        """Create deployment files (Dockerfile is copied from template)."""
        try:
            
            # Copy Firebase credentials if they exist
            # First check in the universal-agent template directory
            template_firebase_creds = self.template_dir / 'firebase-credentials.json'
            
            # Then check environment/config paths
            env_firebase_creds = (os.getenv('FIREBASE_CREDENTIALS') or 
                                os.getenv('firebase_credentials') or 
                                os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or
                                'firebase-credentials.json')
            
            firebase_creds_copied = False
            
            # Try template directory first (universal-agent/firebase-credentials.json)
            if template_firebase_creds.exists():
                dst_creds = deployment_dir / 'firebase-credentials.json'
                shutil.copy2(template_firebase_creds, dst_creds)
                logger.info(f"Firebase credentials copied from template: {template_firebase_creds}")
                firebase_creds_copied = True
            # Try environment-specified path
            elif os.path.exists(env_firebase_creds):
                dst_creds = deployment_dir / 'firebase-credentials.json'
                shutil.copy2(env_firebase_creds, dst_creds)
                logger.info(f"Firebase credentials copied from environment: {env_firebase_creds}")
                firebase_creds_copied = True
            else:
                logger.info("No Firebase credentials file found, using Application Default Credentials")
                
            if not firebase_creds_copied:
                logger.warning("Firebase credentials not found. Deployment may fail without proper authentication.")
            
            logger.info("Deployment files created")
            
        except Exception as e:
            logger.error(f"Failed to create deployment files: {str(e)}")
            raise
    
    
    def _build_and_deploy(self, deployment_dir: Path, agent_id: str) -> str:
        """Build container and deploy to Cloud Run."""
        try:
            # Use a unique service name to avoid conflicts
            service_name = f"agent-{agent_id}"  # Use first 8 chars of agent_id
            image_name = f"gcr.io/{self.project_id}/agent-{agent_id}"
            
            logger.info(f"Building container image: {image_name}")
            
            # Build container image
            build_cmd = [
                'gcloud', 'builds', 'submit',
                '--project', self.project_id,
                '--tag', image_name,
                str(deployment_dir)
            ]
            
            logger.info(f"🔨 Building container with command: {' '.join(build_cmd)}")
            logger.info(f"📁 Build context directory: {deployment_dir}")
            
            result = subprocess.run(build_cmd, capture_output=True, text=True, cwd=deployment_dir)
            if result.returncode != 0:
                logger.error(f"❌ Container build failed:")
                logger.error(f"Command: {' '.join(build_cmd)}")
                logger.error(f"Return code: {result.returncode}")
                logger.error(f"Stdout: {result.stdout}")
                logger.error(f"Stderr: {result.stderr}")
                raise Exception(f"Container build failed with return code {result.returncode}. See logs for details.")
            
            logger.info("✅ Container image built successfully")
            logger.info(f"📦 Built image: {image_name}")
            
            # Deploy to Cloud Run
            logger.info(f"☁️ Deploying to Cloud Run service: {service_name}")
            
            # Get the OpenAI API key for the deployed container
            openai_key = (os.getenv('OPENAI_API_KEY') or os.getenv('openai_api_key', ''))
            if not openai_key:
                raise Exception("OPENAI_API_KEY not found in environment variables")
            
            # Prepare environment variables for the container
            env_vars = f'AGENT_ID={agent_id},PROJECT_ID={self.project_id},OPENAI_API_KEY={openai_key}'
            logger.info(f"🔧 Setting environment variables: AGENT_ID={agent_id}, PROJECT_ID={self.project_id}")
            
            deploy_cmd = [
                'gcloud', 'run', 'deploy', service_name,
                '--image', image_name,
                '--project', self.project_id,
                '--region', self.region,
                '--platform', 'managed',
                '--allow-unauthenticated',
                '--memory', '2Gi',
                '--cpu', '1',
                '--timeout', '300',
                '--concurrency', '80',
                '--min-instances', '0',
                '--max-instances', '10',
                '--set-env-vars', env_vars,
                '--format', 'json'
            ]
            
            logger.info(f"🚀 Deploying with command: {' '.join(deploy_cmd[:8])}... (truncated)")
            
            result = subprocess.run(deploy_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ Cloud Run deployment failed:")
                logger.error(f"Command: {' '.join(deploy_cmd)}")
                logger.error(f"Return code: {result.returncode}")
                logger.error(f"Stdout: {result.stdout}")
                logger.error(f"Stderr: {result.stderr}")
                raise Exception(f"Cloud Run deployment failed with return code {result.returncode}. See logs for details.")
            
            # Parse service URL from deployment result
            try:
                deploy_result = json.loads(result.stdout)
                service_url = deploy_result['status']['url']
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse deployment result: {result.stdout}")
                raise Exception(f"Failed to parse Cloud Run deployment result: {str(e)}")
            
            logger.info(f"Universal agent deployed successfully: {service_url}")
            return service_url
            
        except Exception as e:
            logger.error(f"Build and deploy failed: {str(e)}")
            raise
    
    def _update_agent_deployment_status(self, agent_id: str, status: str, service_url: Optional[str], error: Optional[str] = None):
        """Update agent deployment status in Firestore."""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Initialize Firebase if not already done
            try:
                firebase_app = firebase_admin.get_app()
            except ValueError:
                firebase_creds = (os.getenv('FIREBASE_CREDENTIALS') or 
                                os.getenv('firebase_credentials') or 
                                'firebase-credentials.json')
                if os.path.exists(firebase_creds):
                    cred = credentials.Certificate(firebase_creds)
                    firebase_app = firebase_admin.initialize_app(cred, {'projectId': self.project_id})
                else:
                    firebase_app = firebase_admin.initialize_app()
            
            db = firestore.client(firebase_app)
            
            # Update agent document
            agent_ref = db.collection('alchemist_agents').document(agent_id)
            
            update_data = {
                'universal_deployment': {
                    'status': status,
                    'deployment_type': 'universal',
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
            }
            
            if service_url:
                update_data['universal_deployment']['service_url'] = service_url
            
            if error:
                update_data['universal_deployment']['error'] = error
            
            agent_ref.update(update_data)
            
            logger.info(f"Updated agent deployment status: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update agent deployment status: {str(e)}")
            # Don't raise here as this is a non-critical operation
    
    def get_deployment_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status for an agent."""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Initialize Firebase if not already done
            try:
                firebase_app = firebase_admin.get_app()
            except ValueError:
                firebase_creds = (os.getenv('FIREBASE_CREDENTIALS') or 
                                os.getenv('firebase_credentials') or 
                                'firebase-credentials.json')
                if os.path.exists(firebase_creds):
                    cred = credentials.Certificate(firebase_creds)
                    firebase_app = firebase_admin.initialize_app(cred, {'projectId': self.project_id})
                else:
                    firebase_app = firebase_admin.initialize_app()
            
            db = firestore.client(firebase_app)
            
            # Get agent document
            agent_ref = db.collection('alchemist_agents').document(agent_id)
            agent_doc = agent_ref.get()
            
            if agent_doc.exists:
                agent_data = agent_doc.to_dict()
                return agent_data.get('universal_deployment')
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            return None


def deploy_universal_agent(agent_id: str) -> Dict[str, Any]:
    """
    Convenience function to deploy a universal agent.
    
    Args:
        agent_id: The agent ID to deploy
        
    Returns:
        Deployment result
    """
    deployer = UniversalAgentDeployer()
    return deployer.deploy_agent(agent_id)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python agent_deployer.py <agent_id>")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    
    try:
        result = deploy_universal_agent(agent_id)
        print(f"✅ Deployment successful!")
        print(f"Service URL: {result['service_url']}")
        print(f"Agent ID: {result['agent_id']}")
        print(f"Optimizations applied: {result['optimizations_applied']}")
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        sys.exit(1)