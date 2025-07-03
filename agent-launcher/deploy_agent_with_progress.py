#!/usr/bin/env python3
"""
Agent Deployment Script with Firestore Progress Integration
Replaces deploy-ai-agent.sh with Python implementation that provides real-time deployment progress updates
"""

import asyncio
import logging
import os
import tempfile
import shutil
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import alchemist-shared components
try:
    from alchemist_shared.database.firebase_client import get_firestore_client, FirebaseClient
    from firebase_admin.firestore import SERVER_TIMESTAMP
    from alchemist_shared.config.base_settings import BaseSettings
    from alchemist_shared.constants.collections import Collections
    from alchemist_shared.config.environment import get_project_id
    ALCHEMIST_SHARED_AVAILABLE = True
except ImportError:
    ALCHEMIST_SHARED_AVAILABLE = False
    import firebase_admin
    from firebase_admin import credentials, firestore
    from firebase_admin.firestore import SERVER_TIMESTAMP
    
    # Define fallback collections when alchemist_shared is not available
    class Collections:
        AGENT_DEPLOYMENTS = 'agent_deployments'
        AGENTS = 'agents'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentDeploymentWithProgress:
    """Agent deployment with integrated Firestore progress tracking"""
    
    def __init__(self, deployment_id: str, agent_id: str):
        self.deployment_id = deployment_id
        self.agent_id = agent_id
        
        if ALCHEMIST_SHARED_AVAILABLE:
            self.firebase_client = FirebaseClient()
            self.db = self.firebase_client.db
            self.project_id = get_project_id() or os.getenv('GOOGLE_CLOUD_PROJECT')
        else:
            # Fallback Firebase initialization
            try:
                firebase_app = firebase_admin.get_app()
            except ValueError:
                firebase_app = firebase_admin.initialize_app()
            self.db = firestore.client(firebase_app)
            self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        if not self.project_id:
            raise Exception("GOOGLE_CLOUD_PROJECT environment variable required")
        
        self.service_name = f"agent-{self.agent_id}"
        self.image_name = f"gcr.io/{self.project_id}/{self.service_name}"
    
    async def deploy_agent(self) -> str:
        """Main deployment method that returns service URL"""
        try:
            logger.info(f"Starting deployment of agent {self.agent_id}")
            
            # Step 1: Environment setup and validation (10%)
            await self._update_progress(10, "Setting up deployment environment...")
            await self._setup_environment()
            
            # Step 2: Prepare build context (20%)
            await self._update_progress(20, "Preparing build context...")
            build_dir = await self._prepare_build_context()
            
            try:
                # Step 3: Build Docker image (50%)
                await self._update_progress(30, "Building Docker image with Cloud Build...")
                await self._build_docker_image(build_dir)
                
                # Step 4: Deploy to Cloud Run (80%)
                await self._update_progress(60, "Deploying to Cloud Run...")
                service_url = await self._deploy_to_cloud_run()
                
                # Step 5: Verify deployment (95%)
                await self._update_progress(80, "Verifying deployment...")
                await self._verify_deployment(service_url)
                
                # Step 6: Complete (100%)
                await self._update_progress(100, "Deployment completed successfully", service_url=service_url)
                
                logger.info(f"Agent {self.agent_id} deployed successfully at: {service_url}")
                return service_url
                
            finally:
                # Clean up build directory
                if 'build_dir' in locals():
                    shutil.rmtree(build_dir, ignore_errors=True)
                    
        except Exception as e:
            logger.error(f"Agent deployment failed: {e}")
            await self._update_progress(0, f"Deployment failed: {str(e)}", status="failed", error_message=str(e))
            raise
    
    async def _setup_environment(self):
        """Setup and validate deployment environment"""
        # Check if gcloud is available
        try:
            process = await asyncio.create_subprocess_exec(
                "gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 or not stdout.decode().strip():
                raise Exception("gcloud authentication required")
                
        except Exception as e:
            raise Exception(f"gcloud CLI not available or not authenticated: {e}")
        
        # Set project
        process = await asyncio.create_subprocess_exec(
            "gcloud", "config", "set", "project", self.project_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        logger.info(f"Environment setup complete for project {self.project_id}")
    
    async def _prepare_build_context(self) -> str:
        """Prepare build context directory with all required files"""
        build_dir = tempfile.mkdtemp(prefix=f"agent-{self.agent_id}-build-")
        
        try:
            # Determine if running locally or in container
            if os.path.exists("/app/shared"):
                # Running in container
                base_path = "/app"
            else:
                # Running locally - find the Alchemist-v1 root directory
                current_dir = os.getcwd()
                if "agent-launcher" in current_dir:
                    base_path = os.path.dirname(current_dir)
                else:
                    base_path = current_dir
            
            # Copy shared library
            shared_src = os.path.join(base_path, "shared")
            shared_dst = os.path.join(build_dir, "shared")
            if os.path.exists(shared_src):
                shutil.copytree(shared_src, shared_dst)
                logger.info(f"Copied shared library to build context from {shared_src}")
            else:
                raise Exception(f"Shared library not found at {shared_src}")
            
            # Copy agent-launcher directory
            agent_launcher_src = os.path.join(base_path, "agent-launcher")
            agent_launcher_dst = os.path.join(build_dir, "agent-launcher")
            if os.path.exists(agent_launcher_src):
                shutil.copytree(agent_launcher_src, agent_launcher_dst)
                logger.info(f"Copied agent-launcher to build context from {agent_launcher_src}")
            else:
                raise Exception(f"Agent-launcher not found at {agent_launcher_src}")
            
            # Copy Dockerfile.agent-template
            dockerfile_src = os.path.join(base_path, "Dockerfile.agent-template")
            dockerfile_dst = os.path.join(build_dir, "Dockerfile")
            if os.path.exists(dockerfile_src):
                shutil.copy2(dockerfile_src, dockerfile_dst)
                logger.info(f"Copied Dockerfile to build context from {dockerfile_src}")
            else:
                raise Exception(f"Dockerfile.agent-template not found at {dockerfile_src}")
            
            # Copy optimized .dockerignore for agent builds
            dockerignore_src = os.path.join(base_path, ".dockerignore.agent-template")
            dockerignore_dst = os.path.join(build_dir, ".dockerignore")
            if os.path.exists(dockerignore_src):
                shutil.copy2(dockerignore_src, dockerignore_dst)
                logger.info(f"Copied optimized .dockerignore for agent builds from {dockerignore_src}")
            else:
                logger.warning(f".dockerignore.agent-template not found at {dockerignore_src}, build may include unnecessary files")
            
            logger.info(f"Build context prepared at: {build_dir}")
            return build_dir
            
        except Exception as e:
            shutil.rmtree(build_dir, ignore_errors=True)
            raise Exception(f"Failed to prepare build context: {e}")
    
    async def _build_docker_image(self, build_dir: str):
        """Build Docker image using Cloud Build with predefined cloudbuild.yaml"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Determine base path (same logic as _prepare_build_context)
        if os.path.exists("/app/shared"):
            base_path = "/app"
        else:
            current_dir = os.getcwd()
            if "agent-launcher" in current_dir:
                base_path = os.path.dirname(current_dir)
            else:
                base_path = current_dir
        
        # Copy the predefined cloudbuild.yaml for agent-template
        cloudbuild_src = os.path.join(base_path, "cloudbuild.agent-template.yaml")
        cloudbuild_dst = os.path.join(build_dir, "cloudbuild.yaml")
        
        if os.path.exists(cloudbuild_src):
            shutil.copy2(cloudbuild_src, cloudbuild_dst)
            logger.info(f"Using predefined cloudbuild.yaml for agent-template from {cloudbuild_src}")
                
        # Submit build with substitutions
        logger.info(f"Building image: {self.image_name}")
        
        process = await asyncio.create_subprocess_exec(
            "gcloud", "builds", "submit",
            "--config", cloudbuild_dst,
            "--substitutions", f"_AGENT_ID={self.agent_id},_TIMESTAMP={timestamp}",
            "--timeout", "1200s",
            build_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_output = stderr.decode() if stderr else stdout.decode()
            raise Exception(f"Cloud Build failed: {error_output}")
        
        logger.info(f"Successfully built image: {self.image_name}")
    
    async def _deploy_to_cloud_run(self) -> str:
        """Deploy the built image to Google Cloud Run"""
        logger.info(f"Deploying to Cloud Run: {self.service_name}")
        
        # Prepare environment variables
        env_vars = [
            f"AGENT_ID={self.agent_id}",
            f"GOOGLE_CLOUD_PROJECT={self.project_id}",
            f"ENVIRONMENT=production"
        ]
        
        # Add OpenAI API key if available
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                settings = BaseSettings()
                openai_key = settings.openai_api_key
                if openai_key:
                    env_vars.append(f"OPENAI_API_KEY={openai_key}")
            except:
                pass
        else:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                env_vars.append(f"OPENAI_API_KEY={openai_key}")
        
        # Deploy to Cloud Run
        deploy_command = [
            "gcloud", "run", "deploy", self.service_name,
            "--image", f"{self.image_name}:latest",
            "--platform", "managed",
            "--region", self.region,
            "--allow-unauthenticated",
            "--set-env-vars", ",".join(env_vars),
            "--memory", "2Gi",
            "--cpu", "2",
            "--max-instances", "5",  # Respect quota limits
            "--timeout", "3600",
            "--concurrency", "80",
            "--format", "value(status.url)"
        ]
        
        logger.info(f"Running deployment command...")
        
        process = await asyncio.create_subprocess_exec(
            *deploy_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_output = stderr.decode() if stderr else stdout.decode()
            raise Exception(f"Cloud Run deployment failed: {error_output}")
        
        service_url = stdout.decode().strip()
        if not service_url:
            # Fallback: construct expected service URL
            service_url = f"https://{self.service_name}-{self.project_id}.{self.region}.run.app"
        
        logger.info(f"Successfully deployed to: {service_url}")
        return service_url
    
    async def _verify_deployment(self, service_url: str):
        """Verify that the deployed service is healthy"""
        import aiohttp
        
        logger.info(f"Verifying deployment at {service_url}")
        
        # Wait a bit for the service to start
        await asyncio.sleep(10)
        
        async with aiohttp.ClientSession() as session:
            # Try multiple times with backoff
            max_retries = 5
            
            for attempt in range(max_retries):
                try:
                    async with session.get(f"{service_url}/health", timeout=30) as response:
                        if response.status == 200:
                            logger.info(f"Deployment verification successful")
                            return
                        else:
                            logger.warning(f"Health check returned HTTP {response.status}")
                except Exception as e:
                    logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
            
            raise Exception("Deployment verification failed - health check did not pass")
    
    async def _update_progress(self, progress: int, current_step: str, 
                             status: str = "processing", service_url: str = None, 
                             error_message: str = None):
        """Update deployment progress in Firestore"""
        try:
            collection_name = Collections.AGENT_DEPLOYMENTS if ALCHEMIST_SHARED_AVAILABLE else 'agent_deployments'
            deployment_ref = self.db.collection(collection_name).document(self.deployment_id)
            
            update_data = {
                'deployment_status': status,
                'progress_percentage': progress,
                'current_step': current_step,
                'updated_at': SERVER_TIMESTAMP
            }
            
            if error_message:
                update_data['error_message'] = error_message
                
            if service_url:
                update_data['service_url'] = service_url
                
            if status in ['deployed', 'failed'] or progress == 100:
                update_data['completed_at'] = SERVER_TIMESTAMP
                if progress == 100:
                    update_data['deployment_status'] = 'deployed'
                
            deployment_ref.update(update_data)
            logger.info(f"Updated progress: {progress}% - {current_step}")
            
        except Exception as e:
            logger.error(f"Failed to update deployment progress: {e}")
            # Don't fail the deployment for progress update issues

async def main():
    """Main entry point for the deployment script"""
    
    if len(sys.argv) != 3:
        logger.error("Usage: python deploy_agent_with_progress.py <deployment_id> <agent_id>")
        sys.exit(1)
    
    deployment_id = sys.argv[1]
    agent_id = sys.argv[2]
    
    logger.info(f"Starting agent deployment: deployment_id={deployment_id}, agent_id={agent_id}")
    
    try:
        deployer = AgentDeploymentWithProgress(deployment_id, agent_id)
        service_url = await deployer.deploy_agent()
        
        logger.info(f"Agent deployment completed successfully: {service_url}")
        print(f"SERVICE_URL={service_url}")  # Output for parsing by calling script
        
    except Exception as e:
        logger.error(f"Agent deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())