#!/usr/bin/env python3
"""
MCP Deployment Job - Cloud Run Job for handling individual MCP server deployments
This runs as a standalone job triggered by Eventarc events
"""

import asyncio
import json
import logging
import os
import tempfile
import zipfile
import uuid
import subprocess
import io
import shutil
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import yaml
import aiohttp
import requests

# Import alchemist-shared components
from alchemist_shared.database.firebase_client import get_firestore_client, FirebaseClient
from firebase_admin.firestore import SERVER_TIMESTAMP
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.constants.collections import Collections, DocumentFields, StatusValues

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPDeploymentJob:
    """Cloud Run Job for processing a single MCP deployment"""
    
    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id
        self.firebase_client = FirebaseClient()
        self.db = self.firebase_client.db
        
        # Use alchemist-shared to get project ID
        try:
            from alchemist_shared.config.environment import get_project_id
            self.project_id = get_project_id() or os.getenv('GOOGLE_CLOUD_PROJECT')
        except ImportError:
            self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        if not self.project_id:
            raise Exception("GOOGLE_CLOUD_PROJECT environment variable or alchemist-shared project ID not available")
    
    async def process_deployment(self):
        """Main method to process the deployment"""
        try:
            logger.info(f"Starting deployment job for deployment ID: {self.deployment_id}")
            
            # Get deployment data
            deployment_data = await self._get_deployment_data()
            if not deployment_data:
                raise Exception(f"Deployment {self.deployment_id} not found")
            
            agent_id = deployment_data.get('agent_id')
            if not agent_id:
                raise Exception("No agent_id found in deployment data")
            
            logger.info(f"Processing deployment for agent: {agent_id}")
            
            # Update status to processing
            await self._update_deployment_status(
                'processing', 
                10, 
                'Job started - validating configuration...'
            )
            
            # Get agent configuration
            agent_data = await self._get_agent_config(agent_id)
            if not agent_data:
                raise Exception(f"Agent {agent_id} not found")
            
            # Execute the deployment
            await self._execute_deployment(agent_id, deployment_data, agent_data)
            
            logger.info(f"Deployment {self.deployment_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Deployment {self.deployment_id} failed: {e}")
            await self._update_deployment_status(
                'failed',
                0,
                f'Deployment failed: {str(e)}',
                error_message=str(e)
            )
            raise
    
    async def _get_deployment_data(self) -> Optional[Dict[str, Any]]:
        """Get deployment data from Firestore"""
        try:
            deployment_ref = self.db.collection(Collections.MCP_DEPLOYMENTS).document(self.deployment_id)
            deployment_doc = deployment_ref.get()
            
            if deployment_doc.exists:
                return deployment_doc.to_dict()
            else:
                logger.error(f"Deployment {self.deployment_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get deployment data: {e}")
            return None
    
    async def _get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration from Firestore"""
        try:
            agent_ref = self.db.collection(Collections.AGENTS).document(agent_id)
            agent_doc = agent_ref.get()
            
            if agent_doc.exists:
                return agent_doc.to_dict()
            else:
                logger.error(f"Agent {agent_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get agent config: {e}")
            return None
    
    async def _execute_deployment(self, agent_id: str, deployment_data: Dict[str, Any], agent_data: Dict[str, Any]):
        """Execute the actual deployment process"""
        try:
            # Step 1: Validate configuration (20%)
            await self._update_deployment_status(
                'processing', 
                20, 
                'Validating API configurations...'
            )
            
            # Check if agent has MCP config
            if 'mcp_config' not in agent_data:
                raise Exception("No MCP configuration found for agent")
            
            mcp_config_url = agent_data['mcp_config']['public_url']
            logger.info(f"Using MCP config URL: {mcp_config_url}")
            
            # Download and validate config
            config_data = await self._download_mcp_config(mcp_config_url)
            
            # Step 2: Build MCP server (60%)
            await self._update_deployment_status(
                'processing', 
                60, 
                'Building MCP server container...'
            )
            
            # Build Docker image
            image_uri = await self._build_agent_image(agent_id, mcp_config_url)
            
            # Step 3: Deploy to cloud (80%)
            await self._update_deployment_status(
                'processing', 
                80, 
                'Deploying to cloud infrastructure...'
            )
            
            # Deploy to Cloud Run
            service_url = await self._deploy_to_cloud_run(agent_id, image_uri, mcp_config_url)
            
            # Step 4: Verify deployment (100%)
            await self._update_deployment_status(
                'processing', 
                95, 
                'Verifying deployment...'
            )
            
            # Test the deployed service
            if await self._verify_deployment(service_url):
                await self._update_deployment_status(
                    'deployed', 
                    100, 
                    'Deployment completed successfully',
                    service_url=service_url
                )
                logger.info(f"Deployment {self.deployment_id} completed successfully: {service_url}")
            else:
                raise Exception("Deployment verification failed")
                
        except Exception as e:
            logger.error(f"Deployment execution failed: {e}")
            raise e
    
    async def _download_mcp_config(self, config_url: str) -> Dict:
        """Download and validate MCP configuration"""
        try:
            logger.info(f"Downloading MCP config from: {config_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(config_url, timeout=30) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download config: HTTP {response.status}")
                    
                    config_text = await response.text()
                    
                    # Parse YAML config
                    if config_url.endswith('.yaml') or config_url.endswith('.yml'):
                        config_data = yaml.safe_load(config_text)
                    elif config_url.endswith('.json'):
                        config_data = json.loads(config_text)
                    else:
                        # Try YAML first, then JSON
                        try:
                            config_data = yaml.safe_load(config_text)
                        except:
                            config_data = json.loads(config_text)
                    
                    # Basic validation
                    if not isinstance(config_data, dict):
                        raise Exception("Config must be a dictionary/object")
                    
                    if 'tools' not in config_data:
                        raise Exception("Config must contain 'tools' section")
                    
                    logger.info(f"Successfully downloaded and validated MCP config")
                    logger.info(f"Found {len(config_data.get('tools', []))} tools in config")
                    
                    return config_data
                    
        except Exception as e:
            logger.error(f"Failed to download MCP config: {e}")
            raise
    
    async def _build_agent_image(self, agent_id: str, mcp_config_url: str) -> str:
        """Build Docker image for the agent's MCP server"""
        
        logger.info("Starting Docker image build")
        
        # Create build directory
        build_dir = f"/tmp/{agent_id}_build"
        os.makedirs(build_dir, exist_ok=True)
        
        try:
            # Create Dockerfile for this agent
            dockerfile_content = f"""
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the generic MCP server
COPY generic_mcp_server.py .

# Set environment variables
ENV AGENT_ID={agent_id}
ENV MCP_CONFIG_URL={mcp_config_url}
ENV GOOGLE_CLOUD_PROJECT={self.project_id}
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the server
CMD ["python", "generic_mcp_server.py"]
"""
            
            # Write Dockerfile
            with open(f"{build_dir}/Dockerfile", "w") as f:
                f.write(dockerfile_content)
            
            # Create requirements.txt
            requirements_content = """
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
aiohttp==3.9.1
PyYAML==6.0.1
google-cloud-firestore==2.13.1
google-cloud-storage==2.10.0
requests==2.31.0
"""
            
            with open(f"{build_dir}/requirements.txt", "w") as f:
                f.write(requirements_content)
            
            # Create generic MCP server Python file
            server_content = '''
import os
import asyncio
import logging
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="MCP Server", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "agent_id": os.getenv("AGENT_ID")}

@app.get("/tools")
async def list_tools():
    return {"tools": [], "agent_id": os.getenv("AGENT_ID")}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''
            
            with open(f"{build_dir}/generic_mcp_server.py", "w") as f:
                f.write(server_content)
            
            # Build image using Cloud Build
            image_name = f"gcr.io/{self.project_id}/mcp-{agent_id}:latest"
            
            logger.info(f"Building image: {image_name}")
            
            # Use Cloud Build to build the image
            await self._build_image_with_cloud_build(build_dir, image_name)
            
            logger.info(f"Successfully built image: {image_name}")
            return image_name
            
        finally:
            # Clean up build directory
            shutil.rmtree(build_dir, ignore_errors=True)
    
    async def _build_image_with_cloud_build(self, build_dir: str, image_name: str):
        """Build Docker image using gcloud builds submit"""
        try:
            logger.info(f"Building image with gcloud builds submit: {image_name}")
            
            # Use gcloud builds submit command
            build_command = [
                "gcloud", "builds", "submit",
                "--tag", image_name,
                "--timeout", "1200s",  # 20 minutes timeout for jobs
                "--project", self.project_id,
                build_dir
            ]
            
            logger.info(f"Running command: {' '.join(build_command)}")
            
            # Run the command asynchronously
            process = await asyncio.create_subprocess_exec(
                *build_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode() if stderr else stdout.decode()
                logger.error(f"gcloud builds submit failed: {error_output}")
                raise Exception(f"Cloud Build failed: {error_output}")
            
            logger.info(f"Cloud Build completed successfully for image: {image_name}")
            logger.info(f"Build output: {stdout.decode()}")
            
        except Exception as e:
            logger.error(f"Cloud Build failed: {e}")
            raise Exception(f"Docker build failed: {e}")
    
    async def _deploy_to_cloud_run(self, agent_id: str, image_uri: str, mcp_config_url: str) -> str:
        """Deploy the built image to Google Cloud Run"""
        
        logger.info(f"Deploying to Cloud Run: {image_uri}")
        
        service_name = f"mcp-{agent_id}"
        
        try:
            # Use gcloud run deploy command
            deploy_command = [
                "gcloud", "run", "deploy", service_name,
                "--image", image_uri,
                "--platform", "managed",
                "--region", self.region,
                "--allow-unauthenticated",
                "--set-env-vars", f"AGENT_ID={agent_id},MCP_CONFIG_URL={mcp_config_url}",
                "--memory", "512Mi",
                "--cpu", "1",
                "--max-instances", "10",
                "--project", self.project_id,
                "--format", "value(status.url)"
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
                logger.error(f"gcloud run deploy failed: {error_output}")
                raise Exception(f"Cloud Run deployment failed: {error_output}")
            
            service_url = stdout.decode().strip()
            logger.info(f"Service deployed successfully at: {service_url}")
            
            return service_url
            
        except Exception as e:
            logger.error(f"Cloud Run deployment failed: {e}")
            raise Exception(f"Cloud Run deployment failed: {e}")
    
    async def _verify_deployment(self, service_url: str) -> bool:
        """Verify that the deployed service is healthy"""
        try:
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
                                logger.info(f"Deployment verification successful for {service_url}")
                                return True
                            else:
                                logger.warning(f"Health check returned HTTP {response.status}")
                    except Exception as e:
                        logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
                
                logger.error("All health check attempts failed")
                return False
                
        except Exception as e:
            logger.error(f"Deployment verification failed: {e}")
            return False
    
    async def _update_deployment_status(self, status: str, progress: int, 
                                       current_step: str, error_message: str = None, 
                                       service_url: str = None):
        """Update deployment status in Firestore"""
        try:
            deployment_ref = self.db.collection(Collections.MCP_DEPLOYMENTS).document(self.deployment_id)
            
            update_data = {
                'status': status,
                'progress': progress,
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
            
            # Also update progress_steps if they exist
            deployment_doc = deployment_ref.get()
            if deployment_doc.exists:
                deployment_data = deployment_doc.to_dict()
                progress_steps = deployment_data.get('progress_steps', [])
                
                # Update the appropriate step based on progress
                step_mapping = {
                    20: 'validating',
                    60: 'building', 
                    80: 'deploying',
                    100: 'testing'
                }
                
                current_step_name = step_mapping.get(progress)
                if current_step_name:
                    for step in progress_steps:
                        if step.get('step') == current_step_name:
                            step['status'] = 'completed' if status == 'deployed' or progress >= 100 else 'running'
                            step['message'] = current_step
                            break
                    
                    deployment_ref.update({'progress_steps': progress_steps})
            
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
    
    logger.info(f"Starting MCP deployment job for deployment ID: {deployment_id}")
    
    try:
        # Create and run the deployment job
        job = MCPDeploymentJob(deployment_id)
        await job.process_deployment()
        
        logger.info(f"Deployment job completed successfully for {deployment_id}")
        
    except Exception as e:
        logger.error(f"Deployment job failed for {deployment_id}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())