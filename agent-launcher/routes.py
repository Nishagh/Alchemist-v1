"""
Agent Launcher Service Routes - Status and Health endpoints only (deployments handled by Cloud Run Jobs)
"""

import json
import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from enum import Enum

# Import alchemist-shared components
try:
    from alchemist_shared.database.firebase_client import get_firestore_client, FirebaseClient
    from firebase_admin.firestore import SERVER_TIMESTAMP
    from alchemist_shared.config.base_settings import BaseSettings
    from alchemist_shared.constants.collections import Collections, DocumentFields, StatusValues
    from alchemist_shared.config.environment import get_project_id
    ALCHEMIST_SHARED_AVAILABLE = True
except ImportError:
    logging.warning("Alchemist-shared components not available - install alchemist-shared package")
    ALCHEMIST_SHARED_AVAILABLE = False
    import firebase_admin
    from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize settings
settings = BaseSettings() if ALCHEMIST_SHARED_AVAILABLE else None

# Initialize Firebase
if ALCHEMIST_SHARED_AVAILABLE:
    firebase_client = FirebaseClient()
    db = firebase_client.db
else:
    try:
        firebase_app = firebase_admin.get_app()
    except ValueError:
        firebase_app = firebase_admin.initialize_app()
    db = firestore.client(firebase_app)

# Models
class DeploymentStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

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
        logger.info("UniversalDeploymentManager initialized")
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        try:
            deployment_collection = Collections.AGENT_DEPLOYMENTS if ALCHEMIST_SHARED_AVAILABLE else 'agent_deployments'
            deployment_ref = db.collection(deployment_collection).document(deployment_id)
            deployment_doc = deployment_ref.get()
            
            if deployment_doc.exists:
                return deployment_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            return None
    
    async def trigger_deployment_job(self, deployment_id: str):
        """Trigger Cloud Run Job for agent deployment"""
        try:
            logger.info(f"Triggering Cloud Run Job for deployment {deployment_id}")
            
            # Get project ID
            if ALCHEMIST_SHARED_AVAILABLE:
                project_id = get_project_id()
            else:
                project_id = os.getenv('PROJECT_ID', 'alchemist-e69bb')
            
            region = os.getenv('REGION', 'us-central1')
            
            # Use the pre-deployed agent-deployment-job
            job_name = "agent-deployment-job"
            
            # Execute the job with the deployment_id as environment variable
            execute_command = [
                "gcloud", "run", "jobs", "execute", job_name,
                "--region", region,
                "--project", project_id,
                "--update-env-vars", f"DEPLOYMENT_ID={deployment_id}",
                "--format", "value(metadata.name)"
            ]
            
            logger.info(f"Executing job: {' '.join(execute_command)}")
            
            process = await asyncio.create_subprocess_exec(
                *execute_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode() if stderr else stdout.decode()
                logger.error(f"Failed to execute job: {error_output}")
                raise Exception(f"Failed to execute Cloud Run Job: {error_output}")
            
            logger.info(f"Successfully triggered Cloud Run Job task for deployment {deployment_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger deployment job: {str(e)}")
            raise

deployment_manager = UniversalDeploymentManager()

# API Routes
@router.get("/")
async def root():
    return {
        "service": "Universal Agent Deployment Service",
        "status": "running",
        "version": "2.0.0",
        "description": "Processes agent deployments triggered by Firestore events from agent-studio"
    }

@router.post("/api/deploy")
async def deploy_agent():
    """Deploy a universal agent with LLM-based optimizations"""
    try:
        # This endpoint is deprecated - deployments should be triggered by agent-studio
        # creating documents in the agent_deployments collection
        raise HTTPException(
            status_code=410, 
            detail="This endpoint is deprecated. Deployments are now triggered by creating documents in the agent_deployments collection through agent-studio."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy endpoint called but deprecated: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/deployment/{deployment_id}/status", response_model=DeploymentStatusResponse)
async def get_deployment_status(deployment_id: str):
    """Get deployment status and progress"""
    try:
        deployment_data = await deployment_manager.get_deployment_status(deployment_id)
        
        if not deployment_data:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return DeploymentStatusResponse(
            deployment_id=deployment_id,
            agent_id=deployment_data['agent_id'],
            status=deployment_data.get('deployment_status', 'unknown'),
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

@router.get("/api/deployments")
async def list_deployments(
    status: Optional[DeploymentStatus] = None,
    agent_id: Optional[str] = None,
    limit: int = 50
):
    """List deployments with optional filtering"""
    try:
        deployment_collection = Collections.AGENT_DEPLOYMENTS if ALCHEMIST_SHARED_AVAILABLE else 'agent_deployments'
        
        # Start with base query
        if agent_id and not status:
            query = db.collection(deployment_collection).where('agent_id', '==', agent_id).limit(limit)
        elif status and not agent_id:
            query = db.collection(deployment_collection).where('deployment_status', '==', status.value).limit(limit)
        elif not agent_id and not status:
            query = db.collection(deployment_collection).limit(limit)
        else:
            # Both filters - filter in memory to avoid index requirement
            query = db.collection(deployment_collection).where('agent_id', '==', agent_id).limit(limit * 2)
        
        deployments = []
        for doc in query.stream():
            deployment_data = doc.to_dict()
            deployment_data['deployment_id'] = doc.id
            
            # Filter by status in memory if both filters are applied
            if status and agent_id:
                if deployment_data.get('deployment_status') != status.value:
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

@router.delete("/api/deployment/{deployment_id}")
async def cancel_deployment(deployment_id: str):
    """Cancel a deployment"""
    try:
        # Note: Don't update Firestore here to avoid triggering more events
        # The cancellation should be handled by the job itself or externally
        
        if deployment_id in deployment_manager.active_deployments:
            del deployment_manager.active_deployments[deployment_id]
        
        return {"message": f"Deployment {deployment_id} cancellation requested"}
        
    except Exception as e:
        logger.error(f"Failed to cancel deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/agent/{agent_id}/deployment-status")
async def get_agent_deployment_status(agent_id: str):
    """Get the latest deployment status for a specific agent"""
    try:
        deployment_collection = Collections.AGENT_DEPLOYMENTS if ALCHEMIST_SHARED_AVAILABLE else 'agent_deployments'
        
        # Get the latest deployment for this agent
        query = (db.collection(deployment_collection)
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

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring services"""
    try:
        # Check environment variables using alchemist-shared
        if ALCHEMIST_SHARED_AVAILABLE:
            project_id = get_project_id()
            openai_key = settings.openai_api_key
        else:
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

@router.get("/healthz")
async def health_check_legacy():
    """Legacy health check endpoint for backward compatibility"""
    result = await health_check()
    return result

@router.post("/trigger-agent-deployment")
async def trigger_agent_deployment(request: Request):
    """Eventarc trigger endpoint for agent deployments"""
    try:
        # Handle CloudEvent format with potential binary data
        content_type = request.headers.get('content-type', '')
        logger.info(f"Received Eventarc trigger with content-type: {content_type}")
        
        # Try to parse the CloudEvent
        try:
            if 'application/json' in content_type:
                event_data = await request.json()
            else:
                # Handle binary content or other formats
                body = await request.body()
                if body:
                    # Try to decode as UTF-8, with error handling
                    try:
                        body_str = body.decode('utf-8')
                        event_data = json.loads(body_str)
                    except UnicodeDecodeError:
                        # Handle binary data - extract from headers if available
                        logger.warning("Received binary data, attempting to extract from headers")
                        # Check for CloudEvent headers
                        ce_source = request.headers.get('ce-source', '')
                        ce_subject = request.headers.get('ce-subject', '')
                        
                        if ce_subject and 'agent_deployments' in ce_subject:
                            # Extract deployment ID from ce-subject header
                            # Format: documents/agent_deployments/DEPLOYMENT_ID
                            parts = ce_subject.split('/')
                            if len(parts) >= 3 and 'agent_deployments' in parts:
                                deployment_id = parts[-1]
                                logger.info(f"Extracted deployment_id from headers: {deployment_id}")
                                
                                # Trigger the deployment job
                                await deployment_manager.trigger_deployment_job(deployment_id)
                                
                                return {
                                    "status": "success", 
                                    "deployment_id": deployment_id,
                                    "message": "Agent deployment job triggered successfully (from headers)"
                                }
                        
                        logger.error("Could not extract deployment ID from binary data or headers")
                        return {"status": "error", "message": "Could not parse binary CloudEvent data"}
                else:
                    event_data = {}
        except Exception as parse_error:
            logger.error(f"Failed to parse CloudEvent: {parse_error}")
            return {"status": "error", "message": f"Failed to parse CloudEvent: {str(parse_error)}"}
        
        logger.info(f"Parsed Eventarc event: {event_data}")
        
        # Extract deployment ID from the document path in standard CloudEvent format
        document_name = event_data.get('data', {}).get('value', {}).get('name', '')
        if not document_name:
            # Try alternative CloudEvent formats
            document_name = event_data.get('subject', '') or event_data.get('source', '')
        
        if not document_name:
            logger.error("No document name found in event data")
            return {"status": "error", "message": "No document name found"}
        
        # Extract deployment_id from document path
        parts = document_name.split('/')
        if len(parts) < 2 or 'agent_deployments' not in parts:
            logger.error(f"Invalid document path: {document_name}")
            return {"status": "error", "message": "Invalid document path"}
        
        # Get deployment_id (last part of the path)
        deployment_id = parts[-1]
        logger.info(f"Extracted deployment_id: {deployment_id}")
        
        # Check deployment status to prevent duplicate job executions
        deployment_data = await deployment_manager.get_deployment_status(deployment_id)
        if deployment_data:
            current_status = deployment_data.get('deployment_status', 'unknown')
            logger.info(f"Deployment {deployment_id} current status: {current_status}")
            
            # Only trigger job for queued deployments to prevent duplicates
            if current_status != 'queued':
                logger.info(f"Deployment {deployment_id} status is '{current_status}', skipping duplicate trigger")
                return {
                    "status": "skipped", 
                    "deployment_id": deployment_id,
                    "current_status": current_status,
                    "message": f"Deployment already {current_status}, skipping duplicate trigger"
                }
        else:
            logger.warning(f"Deployment document {deployment_id} not found")
        
        # Trigger the deployment job only for queued deployments
        await deployment_manager.trigger_deployment_job(deployment_id)
        
        return {
            "status": "success", 
            "deployment_id": deployment_id,
            "message": "Agent deployment job triggered successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to process Eventarc trigger: {e}")
        return {"status": "error", "message": str(e)}