#!/usr/bin/env python3
"""
Universal Agent Deployment Service

A Cloud Run service that orchestrates universal agent deployments with real-time progress tracking.
This service uses the new universal agent system with LLM-based optimizations.
"""

import os
import logging
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

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

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Agent Launcher service...")
    
    # Start metrics collection if available
    if METRICS_AVAILABLE:
        await start_background_metrics_collection("agent-launcher")
        logger.info("Metrics collection started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Launcher service...")
    
    # Stop metrics collection
    if METRICS_AVAILABLE:
        await stop_background_metrics_collection()
        logger.info("Metrics collection stopped")


# Initialize FastAPI app
app = FastAPI(
    title="Universal Agent Deployment Service", 
    description="Deploy agents using the universal system with LLM-based optimizations",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware if available
if METRICS_AVAILABLE:
    setup_metrics_middleware(app, "agent-launcher")
    logger.info("Metrics middleware enabled")

# Initialize Firebase
try:
    firebase_app = firebase_admin.get_app()
except ValueError:
    firebase_creds_path = (os.getenv('FIREBASE_CREDENTIALS') or 
                          os.getenv('firebase_credentials') or 
                          os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or
                          'firebase-credentials.json')
    
    # Check both local and container paths
    local_creds = firebase_creds_path
    container_creds = '/app/firebase-credentials.json'
    
    if os.path.exists(local_creds):
        cred = credentials.Certificate(local_creds)
        firebase_app = firebase_admin.initialize_app(cred)
    elif os.path.exists(container_creds):
        cred = credentials.Certificate(container_creds)
        firebase_app = firebase_admin.initialize_app(cred)
    else:
        firebase_app = firebase_admin.initialize_app()

db = firestore.client(firebase_app)

# Models
class DeploymentStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DeploymentRequest(BaseModel):
    agent_id: str

class DeploymentResponse(BaseModel):
    deployment_id: str
    status: DeploymentStatus
    message: str

class DeploymentStatusResponse(BaseModel):
    deployment_id: str
    agent_id: str
    status: DeploymentStatus
    progress_percentage: int
    current_step: str
    created_at: datetime
    updated_at: datetime
    service_url: Optional[str] = None
    error_message: Optional[str] = None
    deployment_type: str = "universal"
    optimizations_applied: Optional[bool] = None

# Universal Deployment Manager
class UniversalDeploymentManager:
    def __init__(self):
        self.active_deployments: Dict[str, Dict[str, Any]] = {}
        
        # Import modules are now available locally in the same directory
        logger.info("UniversalDeploymentManager initialized")
        
    async def queue_deployment(self, request: DeploymentRequest) -> str:
        deployment_id = str(uuid.uuid4())
        
        # Get project_id from .env file
        project_id = os.getenv('PROJECT_ID') or os.getenv('project_id', 'alchemist-e69bb')
        region = os.getenv('REGION') or os.getenv('region', 'us-central1')
        
        deployment_record = {
            'deployment_id': deployment_id,
            'agent_id': request.agent_id,
            'project_id': project_id,
            'region': region,
            'status': DeploymentStatus.QUEUED,
            'progress_percentage': 0,
            'current_step': 'Queued for universal deployment',
            'deployment_type': 'universal',
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }
        
        # Store in Firestore
        deployment_ref = db.collection('agent_deployments').document(deployment_id)
        deployment_ref.set(deployment_record)
        
        # Update agent document with universal deployment status
        agent_ref = db.collection('alchemist_agents').document(request.agent_id)
        agent_ref.update({
            'universal_deployment': {
                'deployment_id': deployment_id,
                'status': DeploymentStatus.QUEUED,
                'deployment_type': 'universal',
                'updated_at': firestore.SERVER_TIMESTAMP
            }
        })
        
        # Add to active deployments
        self.active_deployments[deployment_id] = deployment_record
        
        logger.info(f"Queued universal deployment {deployment_id} for agent {request.agent_id}")
        return deployment_id
    
    async def update_deployment_status(self, deployment_id: str, update_data: Dict[str, Any]):
        try:
            if deployment_id in self.active_deployments:
                self.active_deployments[deployment_id].update(update_data)
            
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            deployment_ref = db.collection('agent_deployments').document(deployment_id)
            deployment_ref.set(update_data, merge=True)
            
            # Also update agent document
            if 'agent_id' in self.active_deployments.get(deployment_id, {}):
                agent_id = self.active_deployments[deployment_id]['agent_id']
                agent_ref = db.collection('alchemist_agents').document(agent_id)
                
                agent_update = {
                    'universal_deployment': {
                        'deployment_id': deployment_id,
                        'status': update_data.get('status'),
                        'deployment_type': 'universal',
                        'updated_at': firestore.SERVER_TIMESTAMP
                    }
                }
                
                if 'service_url' in update_data:
                    agent_update['universal_deployment']['service_url'] = update_data['service_url']
                
                if 'error_message' in update_data:
                    agent_update['universal_deployment']['error'] = update_data['error_message']
                
                if 'optimizations_applied' in update_data:
                    agent_update['universal_deployment']['optimizations_applied'] = update_data['optimizations_applied']
                
                agent_ref.update(agent_update)
            
        except Exception as e:
            logger.error(f"Failed to update deployment status: {str(e)}")
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        try:
            deployment_ref = db.collection('agent_deployments').document(deployment_id)
            deployment_doc = deployment_ref.get()
            
            if deployment_doc.exists:
                return deployment_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            return None
    
    async def process_universal_deployment(self, deployment_id: str, deployment: Dict[str, Any]):
        """Execute universal agent deployment with progress tracking"""
        try:
            logger.info(f"Starting universal agent deployment {deployment_id}")
            
            # Step 1: Initialize
            await self.update_deployment_status(deployment_id, {
                'status': DeploymentStatus.PROCESSING,
                'progress_percentage': 5,
                'current_step': 'Initializing universal deployment'
            })
            
            # Import the universal deployer (now in same directory)
            try:
                from agent_deployer import UniversalAgentDeployer
                logger.info("Successfully imported UniversalAgentDeployer")
            except ImportError as e:
                logger.error(f"Failed to import UniversalAgentDeployer: {str(e)}")
                raise Exception(f"Failed to import universal deployer: {str(e)}")
            
            # Step 2: Load Configuration with LLM Optimizations
            await self.update_deployment_status(deployment_id, {
                'progress_percentage': 15,
                'current_step': 'Loading configuration with LLM optimizations'
            })
            
            deployer = UniversalAgentDeployer()
            
            # Step 3: Validate Agent Configuration
            await self.update_deployment_status(deployment_id, {
                'progress_percentage': 25,
                'current_step': 'Validating agent configuration'
            })
            
            # Step 4: Generate Optimized Code
            await self.update_deployment_status(deployment_id, {
                'progress_percentage': 40,
                'current_step': 'Generating universal agent code with dynamic optimizations'
            })
            
            # Step 5: Build Container Image
            await self.update_deployment_status(deployment_id, {
                'progress_percentage': 60,
                'current_step': 'Building universal container image'
            })
            
            # Step 6: Deploy to Cloud Run
            await self.update_deployment_status(deployment_id, {
                'progress_percentage': 80,
                'current_step': 'Deploying universal agent to Cloud Run'
            })
            
            # Execute the universal deployment
            result = deployer.deploy_agent(deployment['agent_id'])
            
            # Step 7: Complete
            await self.update_deployment_status(deployment_id, {
                'status': DeploymentStatus.COMPLETED,
                'progress_percentage': 100,
                'current_step': 'Universal deployment completed successfully',
                'service_url': result['service_url'],
                'deployment_type': 'universal',
                'optimizations_applied': result.get('optimizations_applied', False)
            })
            
            # Remove from active deployments
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
            
            logger.info(f"Universal deployment {deployment_id} completed successfully")
            logger.info(f"Service URL: {result['service_url']}")
            
        except Exception as e:
            logger.error(f"Universal deployment {deployment_id} failed: {str(e)}")
            
            await self.update_deployment_status(deployment_id, {
                'status': DeploymentStatus.FAILED,
                'current_step': 'Universal deployment failed',
                'error_message': str(e)
            })
            
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]

deployment_manager = UniversalDeploymentManager()

# API Routes
@app.get("/")
async def root():
    return {
        "service": "Universal Agent Deployment Service",
        "status": "running",
        "version": "2.0.0",
        "description": "Deploy agents using the universal system with LLM-based optimizations"
    }

@app.post("/api/deploy", response_model=DeploymentResponse)
async def deploy_agent(request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy a universal agent with LLM-based optimizations"""
    try:
        # Validate required environment variables
        project_id = "alchemist-e69bb"  # Use hardcoded project ID
        openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('openai_api_key')
        
        # PROJECT_ID validation removed - using hardcoded value
        
        if not openai_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        
        deployment_id = await deployment_manager.queue_deployment(request)
        
        # Start deployment in background
        background_tasks.add_task(
            deployment_manager.process_universal_deployment,
            deployment_id,
            deployment_manager.active_deployments[deployment_id]
        )
        
        return DeploymentResponse(
            deployment_id=deployment_id,
            status=DeploymentStatus.QUEUED,
            message="Universal agent deployment queued successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue universal deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deployment/{deployment_id}/status", response_model=DeploymentStatusResponse)
async def get_deployment_status(deployment_id: str):
    """Get deployment status and progress"""
    try:
        deployment_data = await deployment_manager.get_deployment_status(deployment_id)
        
        if not deployment_data:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return DeploymentStatusResponse(
            deployment_id=deployment_id,
            agent_id=deployment_data['agent_id'],
            status=deployment_data['status'],
            progress_percentage=deployment_data.get('progress_percentage', 0),
            current_step=deployment_data.get('current_step', 'Unknown'),
            created_at=deployment_data.get('created_at', datetime.now(timezone.utc)),
            updated_at=deployment_data.get('updated_at', datetime.now(timezone.utc)),
            service_url=deployment_data.get('service_url'),
            error_message=deployment_data.get('error_message'),
            deployment_type=deployment_data.get('deployment_type', 'universal'),
            optimizations_applied=deployment_data.get('optimizations_applied')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deployments")
async def list_deployments(
    status: Optional[DeploymentStatus] = None,
    agent_id: Optional[str] = None,
    limit: int = 50
):
    """List deployments with optional filtering"""
    try:
        # Start with base query
        if agent_id and not status:
            query = db.collection('agent_deployments').where('agent_id', '==', agent_id).limit(limit)
        elif status and not agent_id:
            query = db.collection('agent_deployments').where('status', '==', status.value).limit(limit)
        elif not agent_id and not status:
            query = db.collection('agent_deployments').limit(limit)
        else:
            # Both filters - filter in memory to avoid index requirement
            query = db.collection('agent_deployments').where('agent_id', '==', agent_id).limit(limit * 2)
        
        deployments = []
        for doc in query.stream():
            deployment_data = doc.to_dict()
            deployment_data['deployment_id'] = doc.id
            
            # Filter by status in memory if both filters are applied
            if status and agent_id:
                if deployment_data.get('status') != status.value:
                    continue
            
            deployments.append(deployment_data)
            
            # Limit results in memory if needed
            if len(deployments) >= limit:
                break
        
        # Sort by created_at in memory (descending)
        deployments.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        return {
            "deployments": deployments,
            "count": len(deployments),
            "active_count": len(deployment_manager.active_deployments),
            "deployment_type": "universal"
        }
        
    except Exception as e:
        logger.error(f"Failed to list deployments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/deployment/{deployment_id}")
async def cancel_deployment(deployment_id: str):
    """Cancel a deployment"""
    try:
        await deployment_manager.update_deployment_status(deployment_id, {
            'status': DeploymentStatus.FAILED,
            'current_step': 'Deployment cancelled by user'
        })
        
        if deployment_id in deployment_manager.active_deployments:
            del deployment_manager.active_deployments[deployment_id]
        
        return {"message": f"Deployment {deployment_id} cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Failed to cancel deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent/{agent_id}/deployment-status")
async def get_agent_deployment_status(agent_id: str):
    """Get the latest deployment status for a specific agent"""
    try:
        # Get the latest deployment for this agent
        query = (db.collection('agent_deployments')
                .where('agent_id', '==', agent_id)
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(1))
        
        deployments = list(query.stream())
        
        if not deployments:
            raise HTTPException(status_code=404, detail="No deployments found for this agent")
        
        deployment_doc = deployments[0]
        deployment_data = deployment_doc.to_dict()
        deployment_data['deployment_id'] = deployment_doc.id
        
        return {
            "agent_id": agent_id,
            "latest_deployment": deployment_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent deployment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring services"""
    try:
        # Check environment variables
        project_id = "alchemist-e69bb"  # Use hardcoded project ID
        openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('openai_api_key')
        
        # Check Firebase connection
        firebase_healthy = True
        try:
            db.collection('test').limit(1).get()
        except Exception as e:
            firebase_healthy = False
        
        health_status = {
            "service": "agent-launcher",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0.0",
            "components": {
                "project_config": {
                    "status": "healthy" if project_id else "unhealthy",
                    "project_id": project_id
                },
                "openai": {
                    "status": "healthy" if openai_key else "unhealthy",
                    "configured": bool(openai_key)
                },
                "firebase": {
                    "status": "healthy" if firebase_healthy else "unhealthy",
                    "connected": firebase_healthy
                },
                "active_deployments": {
                    "count": len(deployment_manager.active_deployments),
                    "status": "healthy"
                }
            }
        }
        
        # Determine overall status
        if not project_id or not openai_key or not firebase_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "service": "agent-launcher",
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@app.get("/healthz")
async def health_check_legacy():
    """Legacy health check endpoint for backward compatibility"""
    result = await health_check()
    return result

if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting Universal Agent Deployment Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )