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
            if await self._verify_deployment(service_url, agent_id):
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
import yaml
import json
import aiohttp
from fastapi import FastAPI, HTTPException, Body, Request
from pydantic import BaseModel
import uvicorn
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server", version="1.0.0")

# Global variable to store loaded MCP config
mcp_config: Optional[Dict[str, Any]] = None

async def load_mcp_config():
    """Load MCP configuration from the URL"""
    global mcp_config
    
    config_url = os.getenv("MCP_CONFIG_URL")
    if not config_url:
        logger.error("MCP_CONFIG_URL environment variable not set")
        return
    
    try:
        logger.info(f"Loading MCP config from: {config_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config_url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Failed to download config: HTTP {response.status}")
                    return
                
                config_text = await response.text()
                
                # Parse YAML config
                if config_url.endswith('.yaml') or config_url.endswith('.yml'):
                    mcp_config = yaml.safe_load(config_text)
                elif config_url.endswith('.json'):
                    mcp_config = json.loads(config_text)
                else:
                    # Try YAML first, then JSON
                    try:
                        mcp_config = yaml.safe_load(config_text)
                    except:
                        mcp_config = json.loads(config_text)
                
                logger.info(f"Successfully loaded MCP config with {len(mcp_config.get('tools', []))} tools")
                
    except Exception as e:
        logger.error(f"Failed to load MCP config: {e}")
        mcp_config = None

@app.on_event("startup")
async def startup_event():
    """Load MCP configuration on startup"""
    await load_mcp_config()

@app.get("/health")
async def health():
    return {"status": "healthy", "agent_id": os.getenv("AGENT_ID")}

@app.get("/tools")
async def list_tools():
    """Return the list of available tools from MCP config"""
    if mcp_config is None:
        return {"tools": [], "agent_id": os.getenv("AGENT_ID"), "error": "MCP config not loaded"}
    
    tools = mcp_config.get("tools", [])
    return {"tools": tools, "agent_id": os.getenv("AGENT_ID"), "config_loaded": True}

@app.get("/config")
async def get_config():
    """Return the full MCP configuration"""
    if mcp_config is None:
        raise HTTPException(status_code=503, detail="MCP config not loaded")
    
    return mcp_config

@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: Request, request_data: Dict[str, Any] = Body(default={})):
    """Execute a specific tool using the MCP configuration"""
    if mcp_config is None:
        raise HTTPException(status_code=503, detail="MCP config not loaded")
    
    # Find the tool in the config
    tool_config = None
    for tool in mcp_config.get("tools", []):
        if tool.get("name") == tool_name:
            tool_config = tool
            break
    
    if not tool_config:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        # Get request template from tool config
        request_template = tool_config.get("requestTemplate", {})
        url = request_template.get("url")
        method = request_template.get("method", "GET")
        headers = request_template.get("headers", [])
        security = request_template.get("security", {})
        
        if not url:
            raise HTTPException(status_code=500, detail=f"No URL configured for tool '{tool_name}'")
        
        # Prepare request parameters based on tool arguments and their positions
        tool_args = tool_config.get("args", [])
        query_params = {}
        body_params = {}
        
        # Collect all available parameters from query params and request body
        all_params = {}
        
        # Add query parameters
        for key, value in request.query_params.items():
            all_params[key] = value
        
        # Add body parameters
        if request_data:
            all_params.update(request_data)
        
        logger.info(f"Tool {tool_name}: Available params: {all_params}")
        logger.info(f"Tool {tool_name}: Tool args schema: {tool_args}")
        
        # Process arguments based on their position in the tool schema
        for arg in tool_args:
            arg_name = arg.get("name")
            position = arg.get("position", "body")
            
            if arg_name in all_params:
                value = all_params[arg_name]
                if position == "query":
                    query_params[arg_name] = value
                elif position == "path":
                    # Replace path parameters in URL
                    url = url.replace(f"{{{arg_name}}}", str(value))
                else:  # body or default
                    body_params[arg_name] = value
        
        logger.info(f"Tool {tool_name}: Final query_params: {query_params}")
        logger.info(f"Tool {tool_name}: Final body_params: {body_params}")
        logger.info(f"Tool {tool_name}: Final URL: {url}")
        
        # Prepare headers
        request_headers = {}
        for header in headers:
            request_headers[header.get("key")] = header.get("value")
        
        # Add security headers (Bearer token)
        if security and security.get("id") == "BearerAuth":
            # Get the credential from server config or environment
            server_config = mcp_config.get("server", {})
            security_schemes = server_config.get("securitySchemes", [])
            
            for scheme in security_schemes:
                if scheme.get("id") == "BearerAuth":
                    credential = scheme.get("defaultCredential")
                    if credential:
                        request_headers["Authorization"] = f"Bearer {credential}"
                    break
        
        # Make the HTTP request to the actual API
        async with aiohttp.ClientSession() as session:
            request_kwargs = {
                "url": url,
                "headers": request_headers,
                "params": query_params if query_params else None
            }
            
            if method.upper() in ["POST", "PUT", "PATCH"] and body_params:
                request_kwargs["json"] = body_params
                if "Content-Type" not in request_headers:
                    request_headers["Content-Type"] = "application/json"
            
            async with session.request(method.upper(), **request_kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"API request failed: {error_text}"
                    )
                
                response_data = await response.json()
                
                # Apply response template if configured
                response_template = tool_config.get("responseTemplate", {})
                prepend_body = response_template.get("prependBody", "")
                
                if prepend_body:
                    # Format the response with prepended information
                    formatted_response = f"{prepend_body}\\n\\n```json\\n{json.dumps(response_data, indent=2)}\\n```"
                    return {"result": formatted_response, "raw_data": response_data}
                else:
                    return response_data
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

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
    
    async def _verify_deployment(self, service_url: str, agent_id: str) -> bool:
        """Verify that the deployed service is healthy and gather server information"""
        try:
            logger.info(f"Verifying deployment at {service_url}")
            
            # Wait a bit for the service to start
            await asyncio.sleep(10)
            
            async with aiohttp.ClientSession() as session:
                # Try multiple times with backoff
                max_retries = 5
                health_check_passed = False
                
                for attempt in range(max_retries):
                    try:
                        async with session.get(f"{service_url}/health", timeout=30) as response:
                            if response.status == 200:
                                logger.info(f"Deployment verification successful for {service_url}")
                                health_check_passed = True
                                break
                            else:
                                logger.warning(f"Health check returned HTTP {response.status}")
                    except Exception as e:
                        logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
                
                if not health_check_passed:
                    logger.error("All health check attempts failed")
                    return False
                
                # If health check passed, gather server information for mcp_servers collection
                await self._create_mcp_server_document(service_url, agent_id, session)
                
                return True
                
        except Exception as e:
            logger.error(f"Deployment verification failed: {e}")
            return False
    
    async def _create_mcp_server_document(self, service_url: str, agent_id: str, session: aiohttp.ClientSession):
        """Create or update the mcp_servers document with server information"""
        try:
            logger.info(f"Creating MCP server document for agent {agent_id}")
            
            # Discover available endpoints
            endpoints = await self._discover_endpoints(service_url, session)
            
            # Fetch tools information
            tools_info = await self._fetch_tools_info(service_url, session)
            
            # Fetch server configuration
            config_info = await self._fetch_config_info(service_url, session)
            
            # Create server document data
            server_data = {
                'agent_id': agent_id,
                'service_url': service_url,
                'status': 'active',
                'endpoints': endpoints,
                'tools': tools_info.get('tools', []),
                'tools_count': len(tools_info.get('tools', [])),
                'config_loaded': tools_info.get('config_loaded', False),
                'server_info': {
                    'deployment_id': self.deployment_id,
                    'project_id': self.project_id,
                    'region': self.region,
                    'last_verified': SERVER_TIMESTAMP
                },
                'mcp_config': config_info,
                'created_at': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP
            }
            
            # Add error information if tools failed to load
            if 'error' in tools_info:
                server_data['error'] = tools_info['error']
                server_data['status'] = 'error'
            
            # Store in Firestore
            server_ref = self.db.collection('mcp_servers').document(agent_id)
            server_ref.set(server_data, merge=True)
            
            logger.info(f"Created MCP server document for agent {agent_id} with {len(tools_info.get('tools', []))} tools")
            
        except Exception as e:
            logger.error(f"Failed to create MCP server document: {e}")
            # Don't fail the deployment for this
    
    async def _discover_endpoints(self, service_url: str, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Discover available endpoints on the MCP server"""
        endpoints = []
        
        # Standard endpoints to check
        standard_endpoints = [
            {'path': '/health', 'method': 'GET', 'description': 'Health check endpoint'},
            {'path': '/tools', 'method': 'GET', 'description': 'List available MCP tools'},
            {'path': '/config', 'method': 'GET', 'description': 'Get MCP configuration'},
            {'path': '/', 'method': 'GET', 'description': 'Root endpoint'},
            {'path': '/docs', 'method': 'GET', 'description': 'API documentation'},
            {'path': '/openapi.json', 'method': 'GET', 'description': 'OpenAPI specification'}
        ]
        
        for endpoint in standard_endpoints:
            try:
                async with session.get(f"{service_url}{endpoint['path']}", timeout=10) as response:
                    endpoint_info = {
                        'path': endpoint['path'],
                        'method': endpoint['method'],
                        'description': endpoint['description'],
                        'status_code': response.status,
                        'available': response.status < 500,
                        'content_type': response.headers.get('content-type', 'unknown')
                    }
                    endpoints.append(endpoint_info)
                    
            except Exception as e:
                endpoints.append({
                    'path': endpoint['path'],
                    'method': endpoint['method'],
                    'description': endpoint['description'],
                    'status_code': None,
                    'available': False,
                    'error': str(e)
                })
        
        return endpoints
    
    async def _fetch_tools_info(self, service_url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Fetch tools information from the MCP server"""
        try:
            async with session.get(f"{service_url}/tools", timeout=30) as response:
                if response.status == 200:
                    tools_data = await response.json()
                    return tools_data
                else:
                    logger.warning(f"Tools endpoint returned HTTP {response.status}")
                    return {'tools': [], 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            logger.error(f"Failed to fetch tools info: {e}")
            return {'tools': [], 'error': str(e)}
    
    async def _fetch_config_info(self, service_url: str, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch configuration information from the MCP server"""
        try:
            async with session.get(f"{service_url}/config", timeout=30) as response:
                if response.status == 200:
                    config_data = await response.json()
                    return config_data
                else:
                    logger.info(f"Config endpoint returned HTTP {response.status} (may not be available)")
                    return None
                    
        except Exception as e:
            logger.info(f"Config endpoint not available: {e}")
            return None
    
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