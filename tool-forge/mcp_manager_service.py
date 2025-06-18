#!/usr/bin/env python3
"""
MCP Manager Service - Google Cloud Run Service
Dynamically creates and deploys MCP servers for individual agents
"""

import asyncio
import json
import logging
import os
import tempfile
import zipfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import yaml
import aiohttp
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import run_v2
from google.auth import default
import subprocess
import io

# Import metrics functionality
try:
    from alchemist_shared.middleware import (
        setup_metrics_middleware,
        start_background_metrics_collection,
        stop_background_metrics_collection
    )
    METRICS_AVAILABLE = True
except ImportError:
    logging.warning("Metrics middleware not available - install alchemist-shared package")
    METRICS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase
if not firebase_admin._apps:
    # Check if we're running locally or in cloud
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET') or 'alchemist-e69bb.appspot.com'
    
    if credentials_path and os.path.exists(credentials_path):
        # Local development - use credentials file
        print(f"Using Firebase credentials file: {credentials_path}")
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })
    else:
        # Cloud deployment - use default service account
        print("Using default service account for Firebase authentication")
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })

db = firestore.client()
bucket = storage.bucket()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Tool Forge service...")
    
    # Start metrics collection if available
    if METRICS_AVAILABLE:
        await start_background_metrics_collection("tool-forge")
        logger.info("Metrics collection started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Tool Forge service...")
    
    # Stop metrics collection
    if METRICS_AVAILABLE:
        await stop_background_metrics_collection()
        logger.info("Metrics collection stopped")


# FastAPI app
app = FastAPI(
    title="MCP Manager Service", 
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "tool-forge")
    logger.info("Metrics middleware enabled")

# Pydantic models
class MCPServerStatus(BaseModel):
    agent_id: str
    status: str  # "queued", "building", "deploying", "running", "error", "stopped"
    service_url: Optional[str] = None
    created_at: Any  # Can be str or firestore.SERVER_TIMESTAMP
    last_updated: Any  # Can be str or firestore.SERVER_TIMESTAMP
    error_message: Optional[str] = None
    deployment_id: Optional[str] = None
    current_step: Optional[str] = None
    progress: Optional[int] = None  # 0-100

class DeploymentRequest(BaseModel):
    agent_id: str
    description: Optional[str] = None

class DeploymentJob(BaseModel):
    deployment_id: str
    agent_id: str
    status: str  # "queued", "building", "deploying", "completed", "failed"
    created_at: Any  # Can be str or firestore.SERVER_TIMESTAMP
    started_at: Optional[Any] = None  # Can be str or firestore.SERVER_TIMESTAMP
    completed_at: Optional[Any] = None  # Can be str or firestore.SERVER_TIMESTAMP
    current_step: str
    progress: int  # 0-100
    logs: List[str] = []
    error_message: Optional[str] = None

class DeploymentLogger:
    """Handles logging for deployment jobs"""
    
    def __init__(self, deployment_id: str, agent_id: str):
        self.deployment_id = deployment_id
        self.agent_id = agent_id
        self.logs = []
        
    def log(self, message: str, level: str = "INFO"):
        """Add a log entry"""
        timestamp = firestore.SERVER_TIMESTAMP
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        # Also log to console
        if level == "ERROR":
            logger.error(f"[{self.agent_id}] {message}")
        elif level == "WARNING":
            logger.warning(f"[{self.agent_id}] {message}")
        else:
            logger.info(f"[{self.agent_id}] {message}")
            
    async def save_logs_to_storage(self):
        """Save logs to Cloud Storage"""
        try:
            log_content = "\n".join(self.logs)
            blob_path = f"deployment_logs/{self.agent_id}/{self.deployment_id}.log"
            blob = bucket.blob(blob_path)
            blob.upload_from_string(log_content, content_type='text/plain')
            self.log(f"Logs saved to storage: {blob_path}")
        except Exception as e:
            logger.error(f"Failed to save logs to storage: {e}")
            
    async def update_job_status(self, status: str, step: str, progress: int, error_message: str = None):
        """Update deployment job status in Firestore"""
        try:
            job_ref = db.collection('alchemist_agents').document(self.agent_id).collection('deployments').document(self.deployment_id)
            update_data = {
                'status': status,
                'current_step': step,
                'progress': progress,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'logs': self.logs[-10:]  # Keep last 10 log entries in Firestore
            }
            
            if status == "completed":
                update_data['completed_at'] = firestore.SERVER_TIMESTAMP
            elif status == "failed":
                update_data['completed_at'] = firestore.SERVER_TIMESTAMP
                update_data['error_message'] = error_message
                
            job_ref.update(update_data)
            
            # Also update server status
            await self._update_server_status(status, step, progress, error_message)
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            
    async def _update_server_status(self, status: str, step: str, progress: int, error_message: str = None):
        """Update MCP server status"""
        try:
            # Map deployment status to server status
            server_status = {
                "queued": "creating",
                "building": "creating", 
                "deploying": "creating",
                "completed": "running",
                "failed": "error"
            }.get(status, status)
            
            status_ref = db.collection('alchemist_agents').document(self.agent_id)
            update_data = {
                'status': server_status,
                'current_step': step,
                'progress': progress,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'deployment_id': self.deployment_id
            }
            
            if error_message:
                update_data['error_message'] = error_message
                
            status_ref.update({'mcp_server_status': update_data})
            
        except Exception as e:
            logger.error(f"Failed to update server status: {e}")

class MCPManagerService:
    """Manages MCP server deployments on Google Cloud Run"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        # Configuration for Cloud Run deployments
        self.run_client = run_v2.ServicesClient()
        
    async def start_deployment(self, agent_id: str, description: str = None) -> str:
        """Start an asynchronous deployment and return deployment ID immediately"""
        deployment_id = str(uuid.uuid4())
        
        # Create initial status entries
        await self._create_initial_status(agent_id, deployment_id)
        await self._create_deployment_job(deployment_id, agent_id)
        
        # Return deployment ID immediately - deployment will run in background
        return deployment_id
        
    async def _create_initial_status(self, agent_id: str, deployment_id: str):
        """Create initial server status entry"""
        status = MCPServerStatus(
            agent_id=agent_id,
            status="queued",
            created_at=firestore.SERVER_TIMESTAMP,
            last_updated=firestore.SERVER_TIMESTAMP,
            deployment_id=deployment_id,
            current_step="Queued for deployment",
            progress=0
        )
        await self._save_server_status(status)
        
    async def _create_deployment_job(self, deployment_id: str, agent_id: str):
        """Create deployment job entry"""
        job = DeploymentJob(
            deployment_id=deployment_id,
            agent_id=agent_id,
            status="queued",
            created_at=firestore.SERVER_TIMESTAMP,
            current_step="Queued for deployment",
            progress=0
        )
        
        doc_ref = db.collection('alchemist_agents').document(agent_id).collection('deployments').document(deployment_id)
        doc_ref.set(job.model_dump())
        
    async def deploy_mcp_server_async(self, agent_id: str, deployment_id: str, description: str = None):
        """Background task to deploy MCP server asynchronously"""
        deploy_logger = DeploymentLogger(deployment_id, agent_id)
        
        try:
            deploy_logger.log(f"Starting deployment for agent {agent_id}")
            await deploy_logger.update_job_status("building", "Validating configuration", 10)

            # Fetch agent data and MCP config URL
            agent_data = db.collection('alchemist_agents').document(agent_id).get().to_dict()
            if not agent_data or 'mcp_config' not in agent_data:
                raise Exception(f"No MCP config found for agent {agent_id}")
            
            mcp_config_url = agent_data['mcp_config']['public_url']
            deploy_logger.log(f"Using MCP config URL: {mcp_config_url}")
            
            # Download and validate MCP config
            config_data = await self._download_mcp_config(mcp_config_url, deploy_logger)
            await deploy_logger.update_job_status("building", "MCP configuration downloaded", 20)
                        
            # Step 2: Create Docker image for this agent
            deploy_logger.log("Building Docker image")
            await deploy_logger.update_job_status("building", "Building Docker image", 30)
            image_uri = await self._build_agent_image(agent_id, mcp_config_url, deploy_logger)
            await deploy_logger.update_job_status("building", "Docker image built successfully", 60)
            
            # Step 3: Deploy to Cloud Run
            deploy_logger.log("Deploying to Cloud Run")
            await deploy_logger.update_job_status("deploying", "Deploying to Cloud Run", 70)
            service_url = await self._deploy_to_cloud_run(agent_id, image_uri, mcp_config_url, deploy_logger)
            await deploy_logger.update_job_status("deploying", "Cloud Run deployment completed", 90)
            
            # Step 4: Verify deployment
            deploy_logger.log("Verifying deployment")
            await self._verify_deployment(service_url, deploy_logger)
            
            # Update final status
            await deploy_logger.update_job_status("completed", "Deployment completed successfully", 100)
            
            # Update comprehensive server status with integration summary
            await self._update_integration_summary(agent_id, service_url, mcp_config_url, config_data, deployment_id, deploy_logger)
            
            deploy_logger.log(f"Successfully deployed MCP server for agent {agent_id} at {service_url}")
            
        except Exception as e:
            error_msg = str(e)
            deploy_logger.log(f"Deployment failed: {error_msg}", "ERROR")
            await deploy_logger.update_job_status("failed", "Deployment failed", 0, error_msg)
            
        finally:
            # Save logs to storage
            await deploy_logger.save_logs_to_storage()
    
    async def _verify_deployment(self, service_url: str, deploy_logger: DeploymentLogger):
        """Verify that the deployed service is responding"""
        try:
            deploy_logger.log("Checking service health")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/health", timeout=30) as response:
                    if response.status == 200:
                        deploy_logger.log("Service health check passed")
                    else:
                        deploy_logger.log(f"Service health check failed with status {response.status}", "WARNING")
        except Exception as e:
            deploy_logger.log(f"Service health check failed: {e}", "WARNING")
    
    async def _update_integration_summary(self, agent_id: str, service_url: str, mcp_config_url: str, config_data: Dict, deployment_id: str, deploy_logger: DeploymentLogger):
        """Update comprehensive integration summary for agentEditor"""
        try:
            deploy_logger.log("Updating integration summary")
            
            # Extract tool information from config
            tools_summary = []
            if 'tools' in config_data:
                for tool in config_data['tools']:
                    tool_info = {
                        'name': tool.get('name', 'Unknown'),
                        'description': tool.get('description', ''),
                        'method': tool.get('requestTemplate', {}).get('method', 'GET'),
                        'url_template': tool.get('requestTemplate', {}).get('url', ''),
                        'args_count': len(tool.get('args', []))
                    }
                    tools_summary.append(tool_info)
            
            # Create comprehensive integration summary
            integration_summary = {
                'status': 'active',
                'service_url': service_url,
                'mcp_config_url': mcp_config_url,
                'deployment_id': deployment_id,
                'deployed_at': firestore.SERVER_TIMESTAMP,
                'last_updated':firestore.SERVER_TIMESTAMP,
                'tools_count': len(tools_summary),
                'tools': tools_summary,
                'server_info': {
                    'name': config_data.get('server', {}).get('name', f'MCP Server - {agent_id}'),
                    'version': config_data.get('server', {}).get('version', '1.0.0'),
                    'description': config_data.get('server', {}).get('description', 'Dynamically deployed MCP server')
                },
                'endpoints': {
                    'health': f"{service_url}/health",
                    'tools': f"{service_url}/tools",
                    'execute': f"{service_url}/tools/{{tool_name}}/execute"
                }
            }
            
            # Update both mcp_server_status and api_integration fields
            status_ref = db.collection('alchemist_agents').document(agent_id)
            update_data = {
                'mcp_server_status': {
                    'agent_id': agent_id,
                    'status': 'running',
                    'service_url': service_url,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'last_updated': firestore.SERVER_TIMESTAMP,
                    'deployment_id': deployment_id,
                    'current_step': 'Deployment completed',
                    'progress': 100
                },
                'api_integration': integration_summary
            }
            
            status_ref.update(update_data)
            deploy_logger.log("Integration summary updated successfully")
            
        except Exception as e:
            deploy_logger.log(f"Failed to update integration summary: {e}", "ERROR")
            # Don't fail the deployment if summary update fails
    
    async def _download_mcp_config(self, config_url: str, deploy_logger: DeploymentLogger) -> Dict:
        """Download and validate MCP configuration from URL"""
        try:
            deploy_logger.log(f"Downloading MCP config from: {config_url}")
            
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
                    
                    deploy_logger.log(f"Successfully downloaded and validated MCP config")
                    deploy_logger.log(f"Found {len(config_data.get('tools', []))} tools in config")
                    
                    return config_data
                    
        except Exception as e:
            deploy_logger.log(f"Failed to download MCP config: {e}", "ERROR")
            raise
    
    async def _build_agent_image(self, agent_id: str, mcp_config_url: str, deploy_logger: DeploymentLogger) -> str:
        """Build Docker image for the agent's MCP server"""
        
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
COPY firebase-credentials.json .

# Set environment variables
ENV AGENT_ID={agent_id}
ENV MCP_CONFIG_URL={mcp_config_url}
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-credentials.json
ENV FIREBASE_STORAGE_BUCKET={os.getenv('FIREBASE_STORAGE_BUCKET')}
ENV PORT=8080

# Expose port
EXPOSE 8080

# Create a wrapper script that starts the MCP server with HTTP transport
COPY start_server.py .
CMD ["python", "start_server.py"]
"""
        
        # Create start_server.py for HTTP transport
        start_server_content = '''
import os
import json
import aiohttp
import yaml
from generic_mcp_server import MCPServer
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
agent_id = os.getenv('AGENT_ID')
mcp_config_url = os.getenv('MCP_CONFIG_URL')
port = int(os.getenv('PORT', 8080))

if not agent_id:
    logger.error("AGENT_ID environment variable not set")
    exit(1)

if not mcp_config_url:
    logger.error("MCP_CONFIG_URL environment variable not set")
    exit(1)

# Download MCP configuration
async def download_config():
    logger.info(f"Downloading MCP config from: {mcp_config_url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(mcp_config_url, timeout=30) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                config_text = await response.text()
                
                # Parse config
                if mcp_config_url.endswith('.yaml') or mcp_config_url.endswith('.yml'):
                    return yaml.safe_load(config_text)
                elif mcp_config_url.endswith('.json'):
                    return json.loads(config_text)
                else:
                    try:
                        return yaml.safe_load(config_text)
                    except:
                        return json.loads(config_text)
                        
    except Exception as e:
        logger.error(f"Failed to download config: {e}")
        raise

# Global variables
mcp_server = None
config_data = None

# Create FastAPI app
app = FastAPI(title=f"MCP Server - {agent_id}")

@app.on_event("startup")
async def startup_event():
    global mcp_server, config_data
    try:
        # Download and load config
        config_data = await download_config()
        logger.info(f"Downloaded config with {len(config_data.get('tools', []))} tools")
        
        # Initialize MCP server with downloaded config
        mcp_server = MCPServer(config_content=yaml.dump(config_data))
        logger.info("MCP server initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "agent_id": agent_id, "config_url": mcp_config_url}

# List tools endpoint
@app.get("/tools")
async def list_tools():
    try:
        if not config_data:
            return {"tools": [], "message": "Configuration not loaded"}
        
        tools = []
        for tool_config in config_data.get('tools', []):
            tools.append({
                "name": tool_config.get('name'),
                "description": tool_config.get('description'),
                "args": tool_config.get('args', [])
            })
        
        return {"tools": tools, "agent_id": agent_id}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Execute tool endpoint
@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: Request, arguments: dict = None):
    try:
        if not mcp_server or not config_data:
            raise HTTPException(status_code=503, detail="MCP server not initialized")
        
        # Find the tool in config
        tool_config = None
        for tool in config_data.get('tools', []):
            if tool.get('name') == tool_name:
                tool_config = tool
                break
        
        if not tool_config:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Merge query parameters with body arguments
        # Query parameters take precedence over body parameters
        query_params = dict(request.query_params)
        merged_arguments = {**(arguments or {}), **query_params}
        
        logger.info(f"🔧 Tool {tool_name} - Body args: {arguments}")
        logger.info(f"🔧 Tool {tool_name} - Query params: {query_params}")
        logger.info(f"🔧 Tool {tool_name} - Merged args: {merged_arguments}")
        
        # Execute using the MCP server's execute_tool method
        from generic_mcp_server import MCPTool
        tool_obj = MCPTool(**tool_config)
        result = await mcp_server.execute_tool(tool_obj, merged_arguments)
        
        return {"result": result, "tool_name": tool_name, "agent_id": agent_id}
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"Starting MCP server for agent {agent_id} on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
'''
        
        # Build image using Cloud Build
        image_name = f"mcp-server-{agent_id}"
        image_uri = f"gcr.io/{self.project_id}/{image_name}:latest"
        
        # Create build directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write files
            with open(f"{temp_dir}/Dockerfile", "w") as f:
                f.write(dockerfile_content)
            
            with open(f"{temp_dir}/start_server.py", "w") as f:
                f.write(start_server_content)
            
            # Copy other necessary files
            import shutil
            shutil.copy("generic_mcp_server.py", temp_dir)
            shutil.copy("requirements.txt", temp_dir)
            shutil.copy("firebase-credentials.json", temp_dir)
            
            # Submit to Cloud Build
            await self._submit_cloud_build(temp_dir, image_uri, agent_id, deploy_logger)
        
        return image_uri
    
    async def _submit_cloud_build(self, build_dir: str, image_uri: str, agent_id: str, deploy_logger: DeploymentLogger):
        """Submit build to Google Cloud Build"""
        build_config = {
            "steps": [
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "build",
                        "-t", image_uri,
                        "."
                    ]
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["push", image_uri]
                }
            ],
            "images": [image_uri],
            "timeout": "3600s"
        }
        
        # Write cloudbuild.yaml
        with open(f"{build_dir}/cloudbuild.yaml", "w") as f:
            yaml.dump(build_config, f)
        
        # Submit build using gcloud command
        cmd = [
            "gcloud", "builds", "submit",
            "--config", f"{build_dir}/cloudbuild.yaml",
            "--timeout", "3600s",
            "--project", self.project_id,
            build_dir
        ]
        
        deploy_logger.log(f"Submitting build to Cloud Build: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = f"Cloud Build failed: {stderr.decode()}"
            deploy_logger.log(error_msg, "ERROR")
            raise Exception(error_msg)
        
        deploy_logger.log(f"Cloud Build completed for agent {agent_id}")
        deploy_logger.log(f"Build output: {stdout.decode()}")
    
    async def _deploy_to_cloud_run(self, agent_id: str, image_uri: str, mcp_config_url: str, deploy_logger: DeploymentLogger) -> str:
        """Deploy the image to Cloud Run"""
        
        service_name = f"mcp-server-{agent_id.lower().replace('_', '-')}"
        deploy_logger.log(f"Deploying service: {service_name}")
        
        # Cloud Run service configuration
        service_config = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "labels": {
                    "mcp-agent-id": agent_id,
                    "managed-by": "mcp-manager"
                }
            },
            "spec": {
                "template": {
                    "metadata": {
                        "labels": {
                            "mcp-agent-id": agent_id
                        },
                        "annotations": {
                            "autoscaling.knative.dev/minScale": "1",
                            "autoscaling.knative.dev/maxScale": "10"
                        }
                    },
                    "spec": {
                        "containerConcurrency": 1000,
                        "containers": [
                            {
                                "image": image_uri,
                                "ports": [{"containerPort": 8080}],
                                "env": [
                                    {"name": "AGENT_ID", "value": agent_id},
                                    {"name": "MCP_CONFIG_URL", "value": mcp_config_url},
                                    {"name": "GOOGLE_APPLICATION_CREDENTIALS", "value": "/app/firebase-credentials.json"},
                                    {"name": "FIREBASE_STORAGE_BUCKET", "value": os.getenv('FIREBASE_STORAGE_BUCKET')}
                                ],
                                "resources": {
                                    "limits": {
                                        "cpu": "1000m",
                                        "memory": "512Mi"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        # Deploy using gcloud command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(service_config, f)
            config_file = f.name
        
        try:
            # Step 1: Deploy the service
            cmd = [
                "gcloud", "run", "services", "replace",
                config_file,
                "--region", self.region,
                "--project", self.project_id
            ]
            
            deploy_logger.log(f"Deploying to Cloud Run: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = f"Cloud Run deployment failed: {stderr.decode()}"
                deploy_logger.log(error_msg, "ERROR")
                raise Exception(error_msg)
            
            deploy_logger.log(f"Service deployed successfully")
            deploy_logger.log(f"Deployment output: {stdout.decode()}")
            
            # Step 2: Allow unauthenticated access
            deploy_logger.log("Setting IAM policy to allow unauthenticated access")
            iam_cmd = [
                "gcloud", "run", "services", "add-iam-policy-binding",
                service_name,
                "--member=allUsers",
                "--role=roles/run.invoker",
                "--region", self.region,
                "--project", self.project_id
            ]
            
            iam_process = await asyncio.create_subprocess_exec(
                *iam_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            iam_stdout, iam_stderr = await iam_process.communicate()
            
            if iam_process.returncode != 0:
                deploy_logger.log(f"Warning: Failed to set IAM policy: {iam_stderr.decode()}", "WARNING")
            else:
                deploy_logger.log("IAM policy set successfully")
            
            # Get service URL
            service_url = await self._get_service_url(service_name)
            
            deploy_logger.log(f"Deployed MCP server for agent {agent_id} at {service_url}")
            return service_url
            
        finally:
            os.unlink(config_file)
    
    async def _get_service_url(self, service_name: str) -> str:
        """Get the URL of a deployed Cloud Run service"""
        cmd = [
            "gcloud", "run", "services", "describe",
            service_name,
            "--region", self.region,
            "--project", self.project_id,
            "--format", "value(status.url)"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Failed to get service URL: {stderr.decode()}")
        
        return stdout.decode().strip()
    
    async def _save_server_status(self, status: MCPServerStatus):
        """Save server status to Firestore"""
        doc_ref = db.collection('alchemist_agents').document(status.agent_id)
        doc_ref.update({'mcp_server_status': status.model_dump()})
    
    async def get_server_status(self, agent_id: str) -> Optional[MCPServerStatus]:
        """Get status of an MCP server"""
        try:
            doc_ref = db.collection('alchemist_agents').document(agent_id)
            doc = doc_ref.get()
            
            if doc.exists:
                doc_data = doc.to_dict()
                if 'mcp_server_status' not in doc_data:
                    return None
                
                status_data = doc_data['mcp_server_status']
                
                # Ensure required fields are present with defaults
                validated_data = {
                    'agent_id': agent_id,  # Always use the provided agent_id
                    'status': status_data.get('status', 'unknown'),
                    'created_at': status_data.get('created_at', firestore.SERVER_TIMESTAMP),
                    'last_updated': status_data.get('last_updated', firestore.SERVER_TIMESTAMP),
                    'service_url': status_data.get('service_url'),
                    'error_message': status_data.get('error_message'),
                    'deployment_id': status_data.get('deployment_id'),
                    'current_step': status_data.get('current_step'),
                    'progress': status_data.get('progress')
                }
                
                return MCPServerStatus(**validated_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting server status for {agent_id}: {e}")
            return None
    
    async def get_deployment_job(self, agent_id: str, deployment_id: str) -> Optional[DeploymentJob]:
        """Get deployment job details"""
        try:
            doc_ref = db.collection('alchemist_agents').document(agent_id).collection('deployments').document(deployment_id)
            doc = doc_ref.get()
            
            if doc.exists:
                job_data = doc.to_dict()
                
                # Ensure required fields are present with defaults
                validated_data = {
                    'deployment_id': job_data.get('deployment_id', deployment_id),
                    'agent_id': job_data.get('agent_id', agent_id),
                    'status': job_data.get('status', 'unknown'),
                    'created_at': job_data.get('created_at', firestore.SERVER_TIMESTAMP),
                    'current_step': job_data.get('current_step', 'Unknown'),
                    'progress': job_data.get('progress', 0),
                    'started_at': job_data.get('started_at'),
                    'completed_at': job_data.get('completed_at'),
                    'logs': job_data.get('logs', []),
                    'error_message': job_data.get('error_message')
                }
                
                return DeploymentJob(**validated_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting deployment job {deployment_id} for {agent_id}: {e}")
            return None
    
    async def get_deployment_logs(self, agent_id: str, deployment_id: str) -> Optional[str]:
        """Get deployment logs from storage"""
        try:
            blob_path = f"deployment_logs/{agent_id}/{deployment_id}.log"
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                return blob.download_as_text()
            return None
        except Exception as e:
            logger.error(f"Failed to get deployment logs: {e}")
            return None
    
    async def delete_server(self, agent_id: str) -> bool:
        """Delete an MCP server"""
        try:
            service_name = f"mcp-server-{agent_id.lower().replace('_', '-')}"
            
            # Delete Cloud Run service
            cmd = [
                "gcloud", "run", "services", "delete",
                service_name,
                "--region", self.region,
                "--project", self.project_id,
                "--quiet"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            # Delete from Firestore
            db.collection('alchemist_agents').document(agent_id).update({'mcp_server_status': {}})
            #db.collection('mcp_agents').document(agent_id).delete()
            
            # Delete from Storage
            #blob = bucket.blob(f"mcp_configs/{agent_id}/mcp_config.yaml")
            #if blob.exists():
            #    blob.delete()
            
            logger.info(f"Deleted MCP server for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete MCP server for agent {agent_id}: {e}")
            return False

# Initialize the manager service
manager = MCPManagerService()

# API Endpoints
@app.post("/deploy")
async def deploy_mcp_server(request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy a new MCP server for an agent (async)"""
    deployment_id = await manager.start_deployment(
        request.agent_id, 
        request.description
    )
    
    # Start background deployment task
    background_tasks.add_task(
        manager.deploy_mcp_server_async,
        request.agent_id,
        deployment_id,
        request.description
    )
    
    return {
        "message": "Deployment started",
        "deployment_id": deployment_id,
        "agent_id": request.agent_id,
        "status": "queued"
    }

@app.get("/deployments/{agent_id}/{deployment_id}", response_model=DeploymentJob)
async def get_deployment_status(agent_id: str, deployment_id: str):
    """Get deployment job status"""
    job = await manager.get_deployment_job(agent_id, deployment_id)
    if not job:
        raise HTTPException(status_code=404, detail="Deployment job not found")
    return job

@app.get("/deployments/{agent_id}/{deployment_id}/logs")
async def get_deployment_logs(agent_id: str, deployment_id: str):
    """Get deployment logs"""
    # Get the job first to validate it exists
    job = await manager.get_deployment_job(agent_id, deployment_id)
    if not job:
        raise HTTPException(status_code=404, detail="Deployment job not found")
    
    logs = await manager.get_deployment_logs(agent_id, deployment_id)
    if logs is None:
        # If no logs in storage yet, return current logs from Firestore
        return {"logs": "\n".join(job.logs)}
    
    return {"logs": logs}

@app.get("/servers/{agent_id}", response_model=MCPServerStatus)
async def get_server_status(agent_id: str):
    """Get status of a specific MCP server"""
    status = await manager.get_server_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail="Server not found")
    return status

@app.get("/agents/{agent_id}/integration-summary")
async def get_integration_summary(agent_id: str):
    """Get comprehensive integration summary for agentEditor"""
    try:
        doc_ref = db.collection('alchemist_agents').document(agent_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        doc_data = doc.to_dict()
        
        # Return integration summary if it exists
        if 'api_integration' in doc_data:
            integration_data = doc_data['api_integration']
            
            # Add MCP server status if available
            if 'mcp_server_status' in doc_data:
                integration_data['server_status'] = doc_data['mcp_server_status']
            
            return integration_data
        else:
            # Return empty summary if no integration exists
            return {
                'status': 'not_configured',
                'message': 'No API integration configured for this agent',
                'tools_count': 0,
                'tools': []
            }
            
    except Exception as e:
        logger.error(f"Error getting integration summary for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration summary")

@app.get("/agents/{agent_id}/tools")
async def get_agent_tools(agent_id: str):
    """Get available tools for an agent from its deployed MCP server"""
    try:
        # Get server status first
        status = await manager.get_server_status(agent_id)
        if not status or status.status != 'running' or not status.service_url:
            raise HTTPException(status_code=404, detail="MCP server not running for this agent")
        
        # Fetch tools from the deployed MCP server
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{status.service_url}/tools", timeout=30) as response:
                if response.status == 200:
                    tools_data = await response.json()
                    return tools_data
                else:
                    raise HTTPException(status_code=502, detail="Failed to fetch tools from MCP server")
                    
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to MCP server: {e}")
    except Exception as e:
        logger.error(f"Error getting tools for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent tools")

@app.post("/agents/{agent_id}/tools/{tool_name}/test")
async def test_agent_tool(agent_id: str, tool_name: str, arguments: dict = None):
    """Test a specific tool for an agent"""
    try:
        # Get server status first
        status = await manager.get_server_status(agent_id)
        if not status or status.status != 'running' or not status.service_url:
            raise HTTPException(status_code=404, detail="MCP server not running for this agent")
        
        # Execute tool on the deployed MCP server
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{status.service_url}/tools/{tool_name}/execute",
                json=arguments or {},
                timeout=60
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "result": result,
                        "agent_id": agent_id,
                        "tool_name": tool_name
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "agent_id": agent_id,
                        "tool_name": tool_name
                    }
                    
    except aiohttp.ClientError as e:
        return {
            "success": False,
            "error": f"Connection failed: {e}",
            "agent_id": agent_id,
            "tool_name": tool_name
        }
    except Exception as e:
        logger.error(f"Error testing tool {tool_name} for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test tool")

@app.delete("/servers/{agent_id}")
async def delete_server(agent_id: str):
    """Delete an MCP server"""
    success = await manager.delete_server(agent_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete server")
    return {"message": f"Server {agent_id} deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring services"""
    try:
        # Check environment variables
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
        
        # Check Firebase connection
        firebase_healthy = True
        try:
            db.collection('test').limit(1).get()
        except Exception as e:
            firebase_healthy = False
        
        # Check Storage bucket
        bucket_healthy = True
        try:
            bucket.exists()
        except Exception as e:
            bucket_healthy = False
        
        health_status = {
            "service": "tool-forge",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "project_config": {
                    "status": "healthy" if project_id else "unhealthy",
                    "project_id": project_id
                },
                "firebase": {
                    "status": "healthy" if firebase_healthy else "unhealthy",
                    "connected": firebase_healthy
                },
                "storage": {
                    "status": "healthy" if bucket_healthy else "unhealthy",
                    "bucket": storage_bucket,
                    "connected": bucket_healthy
                },
                "active_deployments": {
                    "status": "healthy"
                }
            }
        }
        
        # Determine overall status
        if not project_id or not firebase_healthy or not bucket_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "service": "tool-forge",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Export the ASGI app for Cloud Run
asgi_app = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 