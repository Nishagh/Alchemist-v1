#!/usr/bin/env python3
"""
Agent Deployment Job - Cloud Run Job for handling individual agent deployments
This runs as a standalone job triggered by Eventarc events from Firestore agent_deployments collection
Uses deploy-ai-agent.sh script for actual deployment
"""

import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import alchemist-shared components
try:
    from alchemist_shared.database.firebase_client import get_firestore_client, FirebaseClient
    from firebase_admin.firestore import SERVER_TIMESTAMP
    from alchemist_shared.config.base_settings import BaseSettings
    from alchemist_shared.constants.collections import Collections, DocumentFields, StatusValues
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

# Log import status
if not ALCHEMIST_SHARED_AVAILABLE:
    logger.warning("Alchemist-shared components not available - install alchemist-shared package")

class AgentDeploymentJob:
    """Cloud Run Job for processing a single agent deployment using deploy-ai-agent.sh"""
    
    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id
        
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
            raise Exception("GOOGLE_CLOUD_PROJECT environment variable or alchemist-shared project ID not available")
    
    async def process_deployment(self):
        """Main method to process the deployment"""
        try:
            logger.info(f"Starting agent deployment job for deployment ID: {self.deployment_id}")
            
            # Get deployment data
            deployment_data = await self._get_deployment_data()
            if not deployment_data:
                raise Exception(f"Deployment {self.deployment_id} not found")
            
            agent_id = deployment_data.get('agent_id')
            if not agent_id:
                raise Exception("No agent_id found in deployment data")
            
            logger.info(f"Processing deployment for agent: {agent_id}")
            
            # Initial validation and status update
            await self._update_deployment_status(
                'processing', 
                5, 
                'Job started - validating agent configuration...'
            )
            
            # Get agent configuration
            agent_data = await self._get_agent_config(agent_id)
            if not agent_data:
                raise Exception(f"Agent {agent_id} not found")
            
            # Validate agent has required configuration
            system_prompt = agent_data.get('system_prompt')
            if not system_prompt:
                raise Exception("No system prompt found for agent")
            
            logger.info(f"Agent config validated - Model: {agent_data.get('model', 'gpt-4')}")
            
            # Execute the deployment (progress is handled by the Python deployment script)
            await self._execute_deployment(agent_id)
            
            logger.info(f"Agent deployment {self.deployment_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Agent deployment {self.deployment_id} failed: {e}")
            await self._update_deployment_status(
                'failed',
                0,
                f'Agent deployment failed: {str(e)}',
                error_message=str(e)
            )
            raise
    
    async def _get_deployment_data(self) -> Optional[Dict[str, Any]]:
        """Get deployment data from Firestore"""
        try:
            collection_name = Collections.AGENT_DEPLOYMENTS if ALCHEMIST_SHARED_AVAILABLE else 'agent_deployments'
            deployment_ref = self.db.collection(collection_name).document(self.deployment_id)
            deployment_doc = deployment_ref.get()
            
            if deployment_doc.exists:
                return deployment_doc.to_dict()
            else:
                logger.error(f"Agent deployment {self.deployment_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get deployment data: {e}")
            return None
    
    async def _get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration from Firestore"""
        try:
            collection_name = Collections.AGENTS if ALCHEMIST_SHARED_AVAILABLE else 'agents'
            agent_ref = self.db.collection(collection_name).document(agent_id)
            agent_doc = agent_ref.get()
            
            if agent_doc.exists:
                return agent_doc.to_dict()
            else:
                logger.error(f"Agent {agent_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get agent config: {e}")
            return None
    
    async def _execute_deployment(self, agent_id: str):
        """Execute deployment using deploy_agent_with_progress.py script"""
        try:
            # The Python deployment script handles all progress updates internally
            logger.info(f"Starting Python deployment script for agent {agent_id}")
            
            # Execute deploy_agent_with_progress.py script
            deploy_command = [
                "python", 
                "/app/agent-launcher/deploy_agent_with_progress.py",
                self.deployment_id,
                agent_id
            ]
            
            logger.info(f"Running command: {' '.join(deploy_command)}")
            
            # Run the command asynchronously
            process = await asyncio.create_subprocess_exec(
                *deploy_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode() if stderr else stdout.decode()
                logger.error(f"Python deployment script failed: {error_output}")
                raise Exception(f"Agent deployment failed: {error_output}")
            
            # Parse service URL from output
            output = stdout.decode()
            logger.info(f"Deploy script output: {output}")
            
            # Extract service URL from output (script outputs SERVICE_URL=https://...)
            service_url = None
            for line in output.split('\n'):
                if line.startswith('SERVICE_URL='):
                    service_url = line.split('=', 1)[1].strip()
                    break
            
            if not service_url:
                # Fallback: construct expected service URL
                service_url = f"https://agent-{agent_id}-{self.project_id}.{self.region}.run.app"
                logger.warning(f"Could not parse service URL from output, using expected URL: {service_url}")
            
            # Update agent document with deployment info (progress is handled by the Python script)
            await self._update_agent_deployment_info(agent_id, service_url)
            
            logger.info(f"Agent {agent_id} deployed successfully at: {service_url}")
            
        except Exception as e:
            logger.error(f"Agent deployment execution failed: {e}")
            raise e
    
    async def _update_agent_deployment_info(self, agent_id: str, service_url: str):
        """Update agent document with deployment information"""
        try:
            collection_name = Collections.AGENTS if ALCHEMIST_SHARED_AVAILABLE else 'agents'
            agent_ref = self.db.collection(collection_name).document(agent_id)
            
            update_data = {
                'deployment_status': 'deployed',
                'active_deployment_id': self.deployment_id,
                'service_url': service_url,
                'last_deployed_at': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP
            }
            
            agent_ref.update(update_data)
            logger.info(f"Updated agent {agent_id} with deployment info")
            
        except Exception as e:
            logger.error(f"Failed to update agent deployment info: {e}")
            # Don't fail the deployment for this
    
    async def _update_deployment_status(self, status: str, progress: int, 
                                       current_step: str, error_message: str = None, 
                                       service_url: str = None):
        """Update deployment status in Firestore"""
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
                
            if status in ['deployed', 'failed']:
                update_data['completed_at'] = SERVER_TIMESTAMP
                
            deployment_ref.update(update_data)
            
        except Exception as e:
            logger.error(f"Failed to update deployment status: {e}")

async def main():
    """Main entry point for the Cloud Run Job"""
    
    # Get deployment ID from environment variable (set by Eventarc)
    deployment_id = os.getenv('DEPLOYMENT_ID')
    
    if not deployment_id:
        # Try to get from command line arguments
        if len(sys.argv) > 1:
            deployment_id = sys.argv[1]
        else:
            logger.error("No deployment ID provided. Set DEPLOYMENT_ID environment variable or pass as argument.")
            sys.exit(1)
    
    logger.info(f"Starting agent deployment job for deployment ID: {deployment_id}")
    
    try:
        # Create and run the deployment job
        job = AgentDeploymentJob(deployment_id)
        await job.process_deployment()
        
        logger.info(f"Agent deployment job completed successfully for {deployment_id}")
        
    except Exception as e:
        logger.error(f"Agent deployment job failed for {deployment_id}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())