"""
Tool Forge Service Routes - Status and Health endpoints only (deployments handled by Cloud Run Jobs)
"""

import json
import logging
import os
import subprocess
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from google.cloud import run_v2
from google.cloud.run_v2.types import RunJobRequest

# Import alchemist-shared components
from alchemist_shared.database.firebase_client import get_firestore_client, FirebaseClient
from firebase_admin.firestore import SERVER_TIMESTAMP
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.constants.collections import Collections, DocumentFields, StatusValues
from alchemist_shared.models.agent_models import Agent, AgentStatus
from alchemist_shared.services import get_ea3_orchestrator, ConversationContext
from alchemist_shared.services.agent_lifecycle_service import get_agent_lifecycle_service
from alchemist_shared.events import get_story_event_publisher
from alchemist_shared.models.base_models import TimestampedModel

logger = logging.getLogger(__name__)

try:
    from alchemist_shared.auth.firebase_auth import get_current_user
    FIREBASE_AUTH_AVAILABLE = True
except ImportError:
    logger.warning("Firebase auth not available from alchemist-shared")
    FIREBASE_AUTH_AVAILABLE = False

# Create router
router = APIRouter()

# Initialize settings
settings = BaseSettings()

# Pydantic models
class MCPServerStatus(TimestampedModel):
    """MCP Server status with identity tracking"""
    agent_id: str
    status: str
    url: Optional[str] = None
    deployment_id: Optional[str] = None
    config_path: Optional[str] = None
    error: Optional[str] = None
    description: Optional[str] = None
    
    # Identity and journey tracking
    identity_version: Optional[str] = None
    journey_phase: Optional[str] = None
    capabilities: Optional[List[str]] = None

class DeployRequest(BaseModel):
    """MCP deployment request with identity context"""
    agent_id: str
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    
    # Identity and journey context
    agent_name: Optional[str] = None
    agent_purpose: Optional[str] = None
    capabilities: Optional[List[str]] = None
    story_context: Optional[Dict[str, Any]] = None

class ServerListResponse(BaseModel):
    """Response for listing MCP servers"""
    servers: List[MCPServerStatus]
    total: int

def get_db():
    """Get Firestore database client using alchemist-shared"""
    return get_firestore_client()

# Trigger Cloud Run Job for new deployments
async def trigger_deployment_job(deployment_id: str) -> bool:
    """Trigger a Cloud Run Job using the Cloud Run API"""
    try:
        # Use alchemist-shared to get project ID
        try:
            from alchemist_shared.config.environment import get_project_id
            project_id = get_project_id() or os.getenv('GOOGLE_CLOUD_PROJECT')
        except ImportError:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        job_name = "mcp-deployment-job"
        
        if not project_id:
            logger.error("No project ID available")
            return False
        
        logger.info(f"Triggering Cloud Run Job {job_name} for deployment {deployment_id} via API")
        
        # Use Cloud Run API client instead of gcloud CLI
        client = run_v2.JobsClient()
        
        # Build the job resource name
        job_resource_name = f"projects/{project_id}/locations/{region}/jobs/{job_name}"
        
        # Create the request with environment variables
        request = RunJobRequest(
            name=job_resource_name,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        env=[
                            run_v2.EnvVar(name="DEPLOYMENT_ID", value=deployment_id)
                        ]
                    )
                ]
            )
        )
        
        # Execute the job
        operation = client.run_job(request=request)
        
        # Extract execution name from metadata
        if hasattr(operation, 'metadata') and hasattr(operation.metadata, 'name'):
            execution_name = operation.metadata.name.split('/')[-1]  # Get just the execution name
            logger.info(f"Job execution triggered successfully: {execution_name}")
        else:
            logger.info(f"Job execution triggered successfully via API")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to trigger deployment job via API: {e}")
        return False

# Simple deployment status manager
class DeploymentStatusManager:
    """Manages deployment status without processing logic"""
    
    def __init__(self):
        self.firebase_client = FirebaseClient()
        self.db = self.firebase_client.db

# Global status manager instance
status_manager = DeploymentStatusManager()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tool-forge",
        "deployment_mode": "cloud_run_jobs"
    }

@router.post("/")
async def handle_eventarc_event(request: Request):
    """Handle Eventarc events from Firestore document creation"""
    try:
        # Log request headers for debugging
        ce_type = request.headers.get("ce-type", "unknown")
        ce_source = request.headers.get("ce-source", "unknown")
        ce_subject = request.headers.get("ce-subject", "unknown")
        logger.info(f"Received Eventarc event - Type: {ce_type}, Source: {ce_source}, Subject: {ce_subject}")
        
        # Log all CloudEvents headers for debugging
        ce_headers = {k: v for k, v in request.headers.items() if k.lower().startswith('ce-')}
        logger.info(f"CloudEvents headers: {ce_headers}")
        
        # Get the raw body and handle potential encoding issues
        event_data = {}
        try:
            body = await request.body()
            if body:
                # Try to decode as UTF-8, with error handling
                try:
                    body_str = body.decode('utf-8')
                    # Handle empty or whitespace-only content
                    if body_str.strip():
                        event_data = json.loads(body_str)
                    else:
                        logger.info("Received empty event body")
                except UnicodeDecodeError:
                    # If UTF-8 fails, try latin-1 as fallback
                    body_str = body.decode('latin-1', errors='replace')
                    if body_str.strip():
                        event_data = json.loads(body_str)
                except json.JSONDecodeError as e:
                    logger.info(f"Event body is not JSON (possibly binary): {str(e)[:100]}")
            else:
                logger.info("Received event with empty body")
        except Exception as decode_error:
            logger.info(f"Event body decode info: {decode_error}")
        
        # Check if this is a Firestore document creation event
        if ce_type == "google.cloud.firestore.document.v1.created":
            logger.info("Detected Firestore document creation event")
            
            # The document path is usually in ce-subject header for Firestore events
            # Format: documents/mcp_deployments/DEPLOYMENT_ID
            document_path = ce_subject
            
            # Also check if mcp_deployments is in any of the headers
            if "mcp_deployments" in ce_subject or "mcp_deployments" in ce_source:
                logger.info(f"Processing MCP deployment event - Subject: {ce_subject}")
                
                # Extract deployment ID from document path
                try:
                    # ce_subject format: documents/mcp_deployments/DEPLOYMENT_ID
                    if "mcp_deployments/" in document_path:
                        deployment_id = document_path.split("mcp_deployments/")[-1]
                    else:
                        # Fallback: try to extract from source
                        deployment_id = ce_source.split("/")[-1]
                    
                    logger.info(f"Extracted deployment ID: {deployment_id}")
                    
                    # Trigger Cloud Run Job for this deployment
                    job_triggered = await trigger_deployment_job(deployment_id)
                    
                    # Record MCP deployment lifecycle event
                    try:
                        lifecycle_service = get_agent_lifecycle_service()
                        if lifecycle_service:
                            await lifecycle_service.record_mcp_deployment_triggered(
                                deployment_id=deployment_id,
                                user_id="system",
                                metadata={
                                    'mcp_deployment': True,
                                    'job_triggered': job_triggered,
                                    'trigger_source': 'eventarc'
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Failed to record MCP deployment lifecycle event: {e}")
                    
                    if job_triggered:
                        return {"status": "job_triggered", "deployment_id": deployment_id}
                    else:
                        return {"status": "job_trigger_failed", "deployment_id": deployment_id}
                        
                except Exception as e:
                    logger.error(f"Failed to extract deployment ID or trigger job: {e}")
                    return {"status": "error", "message": str(e)}
            else:
                logger.info(f"Ignoring Firestore event from other collection - Source: {ce_source}, Subject: {ce_subject}")
        
        # Legacy: Extract document information from the event data (if present)
        if event_data and "data" in event_data:
            data = event_data.get("data", {})
            document_name = data.get("name", "")
            
            if "mcp_deployments" in document_name:
                try:
                    deployment_id = document_name.split("/")[-1]
                    logger.info(f"Processing MCP deployment event for document: {document_name}, ID: {deployment_id}")
                    
                    # Trigger Cloud Run Job for this deployment
                    job_triggered = await trigger_deployment_job(deployment_id)
                    
                    if job_triggered:
                        return {"status": "job_triggered", "deployment_id": deployment_id}
                    else:
                        return {"status": "job_trigger_failed", "deployment_id": deployment_id}
                        
                except Exception as e:
                    logger.error(f"Failed to extract deployment ID or trigger job: {e}")
                    return {"status": "error", "message": str(e)}
        
        return {"status": "event_acknowledged", "type": ce_type}
        
    except Exception as e:
        logger.error(f"Error handling Eventarc event: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/deployments/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    """Get deployment status by ID"""
    try:
        if not status_manager:
            raise HTTPException(status_code=500, detail="Status manager not initialized")
        
        db = status_manager.db
        deployment_ref = db.collection(Collections.MCP_DEPLOYMENTS).document(deployment_id)
        deployment_doc = deployment_ref.get()
        
        if deployment_doc.exists:
            return {"deployment": {"id": deployment_doc.id, **deployment_doc.to_dict()}}
        else:
            raise HTTPException(status_code=404, detail="Deployment not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deployments")
async def list_deployments(limit: int = 50, status: Optional[str] = None):
    """List recent deployments"""
    try:
        if not status_manager:
            raise HTTPException(status_code=500, detail="Status manager not initialized")
        
        db = status_manager.db
        deployments_ref = db.collection(Collections.MCP_DEPLOYMENTS)
        
        # Apply status filter if provided
        if status:
            query = deployments_ref.where(filter=('status', '==', status))
        else:
            query = deployments_ref
        
        # Order by creation time and limit results
        query = query.order_by('created_at', direction='DESCENDING').limit(limit)
        
        deployments = []
        for doc in query.get():
            deployments.append({"id": doc.id, **doc.to_dict()})
        
        return {
            "deployments": deployments,
            "total": len(deployments),
            "status_filter": status
        }
        
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-mcp-deployment")
async def trigger_mcp_deployment_legacy(request: Request):
    """Legacy endpoint for backward compatibility - redirects to main handler"""
    logger.info("Received request at legacy /trigger-mcp-deployment endpoint, redirecting to main handler")
    return await handle_eventarc_event(request)

