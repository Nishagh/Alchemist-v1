"""
Alchemist API Routes

This module organizes all API routes for the Alchemist system,
following the conversation-centric architecture.
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import io
import base64

from fastapi import FastAPI, Request, HTTPException, Depends, File, UploadFile, Form, Header, Query
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel
from firebase_admin import firestore, storage
from firebase_admin.firestore import SERVER_TIMESTAMP
import yaml
import requests
import json
from openai import OpenAI

# Import Alchemist components
from alchemist.services.storage_service import default_storage
from alchemist.services.openai_init import initialize_openai, get_openai_service
from alchemist.agents.orchestrator_agent import OrchestratorAgent
from alchemist.config.firebase_config import get_storage_bucket
from firebase_admin import auth

# Initialize logging first
logger = logging.getLogger(__name__)

# Import eA³ (Epistemic Autonomy) services (required)
try:
    from alchemist_shared.services import (
        get_ea3_orchestrator, ConversationContext
    )
    from alchemist_shared.events import get_story_event_publisher
    EA3_SERVICES_AVAILABLE = True
except ImportError:
    logger.warning("eA³ services not available")
    EA3_SERVICES_AVAILABLE = False

# Import metrics routes
try:
    from metrics_routes import router as metrics_router
    METRICS_ROUTES_AVAILABLE = True
except ImportError:
    logger.warning("Metrics routes not available")
    METRICS_ROUTES_AVAILABLE = False

# (Logger already initialized above)

# Initialize OpenAI API
initialize_openai()

# Note: File validation functions for API specifications have been moved to tool-forge service

# Data models
class AgentCreationRequest(BaseModel):
    agent_type: str
    agent_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None

class AgentActionRequest(BaseModel):
    agent_id: str
    action: str
    payload: Dict[str, Any] = {}
    userId: Optional[str] = None

class ProfilePictureRequest(BaseModel):
    agent_id: str
    style: Optional[str] = "professional"
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"

# User authentication dependency
async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> str:
    """
    Validate the Firebase ID token from Authorization header and extract user ID.
    This function will be used as a dependency for routes that require user authentication.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )
    
    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization scheme. Use 'Bearer <token>'"
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use 'Bearer <token>'"
        )
    
    # LOCAL DEVELOPMENT ONLY: Allow test tokens for local development
    # This bypass is ONLY for localhost and should NEVER be used in production
    is_local_development = os.getenv("ENVIRONMENT") != "production"
    
    if is_local_development and token.startswith("dev-test-"):
        # Extract user ID from test token format: dev-test-{user_id}
        test_user_id = token.replace("dev-test-", "")
        if test_user_id:
            logger.info(f"[DEV MODE] Using test authentication for user: {test_user_id}")
            return test_user_id
    
    # Verify the Firebase ID token
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        logger.debug(f"Authenticated user: {user_id}")
        return user_id
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Firebase ID token"
        )
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Failed to verify authentication token"
        )

def register_routes(app: FastAPI):
    """
    Register all API routes with the FastAPI app
    """
    
    # Include metrics router if available
    if METRICS_ROUTES_AVAILABLE:
        app.include_router(metrics_router)
        logger.info("Metrics routes registered")
    
    # Health endpoint for monitoring
    @app.get("/health")
    @app.options("/health")
    async def health_check(request: Request):
        """Health check endpoint for monitoring services"""
        if request.method == "OPTIONS":
            return Response(
                content="",
                media_type="text/plain",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "1200"
                }
            )
        
        try:            
            # Basic health status
            health_status = {
                "service": "agent-engine",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "service": "agent-engine",
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            )

    # Status endpoint
    @app.get("/api/status")
    async def get_api_status():
        """Check API connection status"""
        return {"status": "success", "message": "API is running"}

    # Agent Management Endpoints
    @app.get("/api/agents")
    async def list_agents(user_id: str = Depends(get_current_user)):
        """Get a list of all agents for the authenticated user."""
        try:
            agents = await default_storage.list_agents(userId=user_id)
            return {"status": "success", "agents": agents}
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.options("/api/agents")
    async def options_agents(request: Request):
        """Handle OPTIONS requests for agent creation endpoint"""
        return Response(
            content="",
            media_type="text/plain",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "1200"
            }
        )

    @app.post("/api/agents")
    async def create_agent(request: Request, user_id: str = Depends(get_current_user)):
        """Create a new agent."""
        try:
            # Get request body as JSON
            body = await request.json()
            
            # Generate agent ID if not provided
            agent_id = body.get('agent_id') or str(uuid4())
            
            # Create agent configuration with flexible field mapping
            agent_config = {
                'agent_id': agent_id,
                'id': agent_id,  # Also include 'id' field for compatibility
                'name': body.get('name', ''),
                'description': body.get('description', ''),
                'instructions': body.get('instructions', ''),
                'personality': body.get('personality', ''),
                'agent_type': body.get('agent_type', 'general'),
                'config': body.get('config', {}),
                'owner_id': user_id,  # Use owner_id as per DocumentFields
                'userId': user_id,  # Keep userId for backward compatibility
                'created_at': body.get('created_at') or firestore.SERVER_TIMESTAMP,
                'updated_at': body.get('updated_at') or firestore.SERVER_TIMESTAMP,
                'status': body.get('status', 'draft')
            }
            
            # Save to Firestore
            agent_ref = default_storage.db.collection('agents').document(agent_id)
            agent_ref.set(agent_config)
            
            logger.info(f"Created agent {agent_id} for user {user_id}")
            
            # Create response data without SERVER_TIMESTAMP (not JSON serializable)
            response_data = {k: v for k, v in agent_config.items() 
                           if k not in ['created_at', 'updated_at']}
            response_data['created_at'] = datetime.now().isoformat()
            response_data['updated_at'] = datetime.now().isoformat()
            
            return {
                "status": "success", 
                "id": agent_id,
                "agent_id": agent_id,
                "data": response_data
            }
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )
            
    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str, user_id: str = Depends(get_current_user)):
        """Get details for a specific agent."""
        try:
            agent = await default_storage.get_agent_config(agent_id)
            if not agent:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            # Verify the user owns this agent
            if agent.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent"}
                )
                
            return {"status": "success", "agent": agent}
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.put("/api/agents/{agent_id}")
    async def update_agent(agent_id: str, request: Dict[str, Any], user_id: str = Depends(get_current_user)):
        """Update an existing agent."""
        try:
            # Check if agent exists
            existing_agent = await default_storage.get_agent_config(agent_id)
            if not existing_agent:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            # Verify the user owns this agent
            if existing_agent.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to update this agent"}
                )
            
            # Update agent configuration
            config_updates = request.get("config", {})
            if "userId" in request:
                config_updates["userId"] = request["userId"]
            
            update_success = await default_storage.update_agent_config(agent_id, config_updates)
            
            if not update_success:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Failed to update agent configuration"}
                )
            
            # Get updated agent config
            updated_agent = await default_storage.get_agent_config(agent_id)
            
            logger.info(f"Updated agent {agent_id} for user {user_id}")
            return {
                "status": "success",
                "agent_id": agent_id,
                "agent": updated_agent
            }
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.options("/api/agents/{agent_id}/conversations")
    async def options_agent_conversations(agent_id: str, request: Request):
        """Handle OPTIONS requests for agent conversations endpoint"""
        return Response(
            content="",
            media_type="text/plain",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "1200"
            }
        )

    @app.get("/api/agents/{agent_id}/conversations")
    async def get_conversations(agent_id: str, user_id: str = Depends(get_current_user)):
        """Get conversations for an agent."""
        try:
            # Check if agent exists
            existing_agent = await default_storage.get_agent_config(agent_id)
            if not existing_agent:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            # Verify the user owns this agent
            if existing_agent.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent"}
                )
            result = []
            # Query the conversations collection to find those associated with this agent
            conversation_ref = default_storage.db.collection('conversations').document(agent_id)
            conversation_docs = conversation_ref.get()
            
            if conversation_docs.exists:
                logger.debug(f"Retrieved conversation {agent_id}")
                messages = await default_storage.get_messages(agent_id)
                for message in messages:
                        message_data = {
                            "id": message.get("id", str(uuid4())),
                            "conversation_id": agent_id,
                            "content": message.get("content", ""),
                            "role": message.get("role", "unknown"),
                            "timestamp": message.get("timestamp", datetime.now().isoformat())
                        }                            
                        result.append(message_data)
                return {"status": "success", "conversations": result}
            else:
                logger.warning(f"Conversation {agent_id} not found")
                return {"status": "success", "conversations": []}

        except Exception as e:
            logger.error(f"Error getting conversations for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    # Alchemist Direct Interaction Endpoint
    @app.options("/api/alchemist/interact")
    async def options_alchemist_interact(request: Request):
        """Handle OPTIONS requests for alchemist interact endpoint"""
        return Response(
            content="",
            media_type="text/plain",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "1200"
            }
        )

    @app.post("/api/alchemist/interact")
    async def interact_with_alchemist(request: Request, user_id: str = Depends(get_current_user)):
        """
        Direct interaction with the Alchemist agent.
        
        This endpoint allows for interaction with the hardcoded Alchemist agent,
        which can help with agent creation and management.
        """
        try:
            # Get request body as JSON
            body = await request.json()
            
            # Extract message from request
            message = body.get("message")
            agent_id = body.get("agent_id")
            logger.info(f"Interacting with Alchemist agent {agent_id}")
            
            if not message:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "message is required"}
                )
                
            if not agent_id:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "agent_id is required"}
                )
            # Get agent configuration if it exists
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                logger.info(f"Agent config {agent_id} not found, creating new")
                agent_config = await default_storage.create_agent_config(agent_id, message, user_id)
                
                # Initialize agent's life-story for eA³ (Epistemic Autonomy, Accountability, Alignment) - optional
                if EA3_SERVICES_AVAILABLE:
                    try:
                        ea3_orchestrator = await get_ea3_orchestrator()
                        core_objective = f"Assist users as a helpful AI agent specializing in: {message}"
                        
                        life_story_created = await ea3_orchestrator.create_agent_life_story(
                            agent_id=agent_id,
                            core_objective=core_objective,
                            agent_config=agent_config
                        )
                        
                        if life_story_created:
                            logger.info(f"Initialized life-story for new agent {agent_id}")
                        else:
                            logger.warning(f"Failed to initialize life-story for agent {agent_id} - continuing without eA³ features")
                    except Exception as e:
                        logger.warning(f"eA³ life-story initialization failed for agent {agent_id}: {e}")
                else:
                    logger.debug(f"eA³ services not available - skipping life-story initialization for agent {agent_id}")
            else:
                logger.info(f"Agent config {agent_id} found")
                # Verify the user owns this agent
                if agent_config.get("userId") and agent_config.get("userId") != user_id:
                    return JSONResponse(
                        status_code=403,
                        content={"status": "error", "message": "You do not have permission to interact with this agent"}
                    )
                    
            orchestrator = OrchestratorAgent(agent_id)
                        
            # Add user message to conversation
            await default_storage.add_message(
                conversation_id=agent_id,
                message={
                    "role": "user",
                    "content": message,
                }
            )
            
            input_data = {
                'message': message,
                'agent_id': agent_id,
                'user_id': user_id,
            }
            
            result = await orchestrator.process(input_data)
            
            # eA³ (Epistemic Autonomy, Accountability, Alignment) processing with async story events - optional
            if EA3_SERVICES_AVAILABLE:
                try:
                    ea3_orchestrator = await get_ea3_orchestrator()
                    
                    # Create conversation context for life-story integration
                    conversation_context = ConversationContext(
                        agent_id=agent_id,
                        user_message=message,
                        agent_response=result.get("response", ""),
                        conversation_id=agent_id,  # Using agent_id as conversation_id for now
                        user_id=user_id,
                        timestamp=datetime.now(),
                        confidence=0.8,
                        metadata={
                            "platform": "alchemist",
                            "interaction_type": "chat",
                            "orchestrator_steps": len(result.get("thought_process", []))
                        }
                    )
                    
                    # Process conversation into agent's life-story (CNE + RbR)
                    coherence_maintained, ea3_assessment = await ea3_orchestrator.process_conversation(conversation_context)
                    
                    # Publish story event asynchronously for microservices coordination
                    story_publisher = get_story_event_publisher()
                    
                    # Publish conversation event for other services to process
                    asyncio.create_task(
                        story_publisher.publish_conversation_event(
                            agent_id=agent_id,
                            user_message=message,
                            agent_response=result.get("response", ""),
                            conversation_id=agent_id,
                            source_service="agent-engine",
                            metadata={
                                "coherence_maintained": coherence_maintained,
                                "ea3_assessment": {
                                    "autonomy_score": ea3_assessment.epistemic_autonomy_score if ea3_assessment else 0.5,
                                    "alignment_score": ea3_assessment.alignment_score if ea3_assessment else 0.5,
                                    "coherence_score": ea3_assessment.overall_coherence if ea3_assessment else 0.5
                                } if ea3_assessment else None,
                                "platform": "alchemist",
                                "interaction_type": "chat",
                                "orchestrator_steps": len(result.get("thought_process", []))
                            }
                        )
                    )
                    logger.debug(f"Published story event for conversation with agent {agent_id}")
                    
                    if not coherence_maintained:
                        logger.warning(f"Agent {agent_id}: Narrative coherence compromised - RbR triggered")
                        
                        # Trigger autonomous reflection for major coherence issues
                        if ea3_assessment and ea3_assessment.overall_coherence < 0.7:
                            await ea3_orchestrator.trigger_autonomous_reflection(
                                agent_id=agent_id,
                                trigger_reason="major_coherence_loss_during_conversation"
                            )
                    
                    # Log eA³ status for monitoring
                    if ea3_assessment:
                        logger.info(
                            f"Agent {agent_id} eA³ Status - "
                            f"Autonomy: {ea3_assessment.epistemic_autonomy_score:.3f}, "
                            f"Accountability: {ea3_assessment.accountability_score:.3f}, "
                            f"Alignment: {ea3_assessment.alignment_score:.3f}, "
                            f"Coherence: {ea3_assessment.overall_coherence:.3f}"
                        )
                except Exception as e:
                    logger.warning(f"eA³ processing failed for agent {agent_id}: {e}")
            else:
                logger.debug(f"eA³ services not available - skipping advanced processing for agent {agent_id}")
            
            # Add assistant message to conversation
            if result.get("message_to_add"):
                message_to_add = result.get("message_to_add")
                await default_storage.add_message(
                    conversation_id=agent_id,
                    message=message_to_add
                )
            
            # Update conversation timestamp
            await default_storage.update_conversation(
                conversation_id=agent_id,
                data={"updated_at": firestore.SERVER_TIMESTAMP}
            )
            
            return {
                "status": "success",
                "conversation_id": agent_id,
                "response": result.get("response", ""),
                "thought_process": result.get("thought_process", [])
            }
        except Exception as e:
            logger.error(f"Error interacting with Alchemist: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.get("/api/agents/{agent_id}/life-story")
    async def get_agent_life_story(agent_id: str, user_id: str = Depends(get_current_user)):
        """
        Get the agent's complete life-story for accountability and transparency
        
        This provides the full eA³ (Epistemic Autonomy, Accountability, Alignment) trace
        showing how the agent has developed its beliefs and made decisions over time.
        """
        try:
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent's life-story"}
                )
            
            if not EA3_SERVICES_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": "eA³ services not available"}
                )
            
            # Get accountability trace from eA³ orchestrator
            ea3_orchestrator = await get_ea3_orchestrator()
            accountability_trace = await ea3_orchestrator.get_accountability_trace(agent_id)
            
            if "error" in accountability_trace:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": accountability_trace["error"]}
                )
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "life_story": accountability_trace
            }
            
        except Exception as e:
            logger.error(f"Error getting life-story for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.get("/api/agents/{agent_id}/ea3-status")
    async def get_agent_ea3_status(agent_id: str, user_id: str = Depends(get_current_user)):
        """
        Get the agent's current eA³ (Epistemic Autonomy, Accountability, Alignment) status
        """
        try:
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent's eA³ status"}
                )
            
            if not EA3_SERVICES_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": "eA³ services not available"}
                )
            
            # Get eA³ status from orchestrator
            ea3_orchestrator = await get_ea3_orchestrator()
            
            # Get comprehensive eA³ assessment
            ea3_assessment = await ea3_orchestrator._assess_agent_ea3(agent_id)
            
            # Check alignment drift
            alignment_check = await ea3_orchestrator.check_alignment_drift(agent_id)
            
            # Check narrative coherence
            coherence_check = await ea3_orchestrator.force_narrative_coherence_check(agent_id)
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "ea3_status": {
                    "alignment": {
                        "alignment_score": ea3_assessment.alignment_score,
                        "drift_detected": alignment_check.get("drift_detected", False),
                        "last_check": datetime.now().isoformat(),
                        "core_objectives_maintained": alignment_check.get("core_objectives_maintained", True)
                    },
                    "coherence": {
                        "narrative_coherence": ea3_assessment.overall_coherence,
                        "consistency_score": coherence_check.get("consistency_score", ea3_assessment.overall_coherence),
                        "contradiction_count": coherence_check.get("contradiction_count", 0),
                        "last_revision": coherence_check.get("last_revision", datetime.now().isoformat())
                    },
                    "autonomy_score": ea3_assessment.epistemic_autonomy_score,
                    "accountability_score": ea3_assessment.accountability_score,
                    "overall_ea3_health": (ea3_assessment.epistemic_autonomy_score + ea3_assessment.accountability_score + ea3_assessment.alignment_score) / 3.0,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting eA³ status for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.post("/api/agents/{agent_id}/trigger-reflection")
    async def trigger_agent_reflection(agent_id: str, user_id: str = Depends(get_current_user)):
        """
        Manually trigger autonomous reflection for the agent
        
        This allows users to initiate the recursive belief revision process manually
        """
        try:
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to trigger reflection for this agent"}
                )
            
            if not EA3_SERVICES_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": "eA³ services not available"}
                )
            
            # Trigger autonomous reflection
            ea3_orchestrator = await get_ea3_orchestrator()
            success = await ea3_orchestrator.trigger_autonomous_reflection(
                agent_id=agent_id,
                trigger_reason="manual_user_request"
            )
            
            if success:
                return {
                    "status": "success",
                    "message": f"Autonomous reflection triggered for agent {agent_id}",
                    "agent_id": agent_id
                }
            else:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Failed to trigger reflection"}
                )
            
        except Exception as e:
            logger.error(f"Error triggering reflection for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.get("/api/agents/{agent_id}/coherence-trends")
    async def get_agent_coherence_trends(agent_id: str, user_id: str = Depends(get_current_user)):
        """
        Get historical coherence trend data for the agent
        """
        try:
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent's coherence trends"}
                )
            
            if not EA3_SERVICES_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": "eA³ services not available"}
                )
            
            # Get coherence trends from eA³ orchestrator
            ea3_orchestrator = await get_ea3_orchestrator()
            trends = await ea3_orchestrator.get_coherence_trends(agent_id)
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"Error getting coherence trends for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.get("/api/agents/{agent_id}/conflicts")
    async def get_agent_conflicts(agent_id: str, user_id: str = Depends(get_current_user)):
        """
        Get active narrative conflicts for the agent
        """
        try:
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent's conflicts"}
                )
            
            if not EA3_SERVICES_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": "eA³ services not available"}
                )
            
            # Get conflicts from eA³ orchestrator
            ea3_orchestrator = await get_ea3_orchestrator()
            conflicts = await ea3_orchestrator.get_narrative_conflicts(agent_id)
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "conflicts": conflicts
            }
            
        except Exception as e:
            logger.error(f"Error getting conflicts for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )
            
    @app.get("/api/agents/{agent_id}/prompt")
    async def get_agent_prompt(agent_id: str, user_id: str = Depends(get_current_user)):
        """Get the prompt for an agent."""
        try:
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent"}
                )
            
            system_prompt = await default_storage.get_agent_prompt(agent_id)
            return {"status": "success", "prompt": system_prompt}
        except Exception as e:
            logger.error(f"Error getting agent prompt for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}  
            )

    # Knowledge Base API endpoints
    @app.get("/api/agents/{agent_id}/knowledge")
    async def get_knowledge_base_files(agent_id: str, user_id: str = Depends(get_current_user)):
        """Get knowledge base files for an agent."""
        try:
            # Check if agent exists
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            # Verify the user owns this agent
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent's knowledge base"}
                )
            
            # Get knowledge base files from agent config
            knowledge_base = agent_config.get("knowledge_base", [])
            
            # Process the knowledge base to ensure consistent format
            files = []
            for file in knowledge_base:
                if isinstance(file, str):
                    try:
                        file_obj = json.loads(file)
                        files.append(file_obj)
                    except json.JSONDecodeError:
                        # Skip files that can't be parsed
                        continue
                elif isinstance(file, dict):
                    files.append(file)
            
            return {"status": "success", "files": files}
        except Exception as e:
            logger.error(f"Error getting knowledge base for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    # Note: API specification upload endpoint has been moved to tool-forge service
    # Frontend now calls TOOL_FORGE_URL/api/agents/{agent_id}/config instead

    # Umwelt API endpoint
    @app.get("/api/agents/{agent_id}/umwelt")
    async def get_agent_umwelt(agent_id: str, user_id: str = Depends(get_current_user)):
        """Get the agent's current Umwelt (world snapshot)."""
        try:
            # Check if agent exists
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            # Verify the user owns this agent
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to access this agent's Umwelt"}
                )
            
            # Try to get Umwelt data from the Umwelt service
            try:
                # Import Umwelt service
                from alchemist_shared.services.umwelt_service import get_umwelt_manager
                
                umwelt_manager = await get_umwelt_manager()
                umwelt_data = await umwelt_manager.get_umwelt(agent_id)
                
                return {
                    "status": "success",
                    "data": {
                        "agent_id": agent_id,
                        "umwelt": umwelt_data,
                        "last_updated": datetime.now().isoformat(),
                        "total_keys": len(umwelt_data)
                    }
                }
                
            except ImportError:
                logger.warning("Umwelt service not available")
                return {
                    "status": "success",
                    "data": {
                        "agent_id": agent_id,
                        "umwelt": {},
                        "last_updated": datetime.now().isoformat(),
                        "total_keys": 0,
                        "note": "Umwelt service not available"
                    }
                }
            except Exception as e:
                logger.error(f"Error getting Umwelt for agent {agent_id}: {e}")
                return {
                    "status": "success",
                    "data": {
                        "agent_id": agent_id,
                        "umwelt": {},
                        "last_updated": datetime.now().isoformat(),
                        "total_keys": 0,
                        "error": str(e)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in get_agent_umwelt for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.post("/api/agents/generate-profile-picture")
    async def generate_agent_profile_picture(request: ProfilePictureRequest, user_id: str = Depends(get_current_user)):
        """Generate a profile picture for an agent using DALL-E."""
        try:
            agent_id = request.agent_id
            
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to generate a profile picture for this agent"}
                )
            
            # Create descriptive prompt based on agent data
            agent_name = agent_config.get("name", "AI Agent")
            agent_role = agent_config.get("instructions", "").strip() or agent_config.get("description", "").strip() or "AI Assistant"
            agent_personality = agent_config.get("personality", "").strip()
            
            # Clean up role text - take first sentence or first 50 chars
            if len(agent_role) > 50:
                agent_role = agent_role.split('.')[0][:50] + "..."
            
            # Build AI agent-focused prompts based on style
            style_prompts = {
                "professional": "Digital AI avatar with robotic features, professional appearance, metallic elements, glowing blue eyes",
                "friendly": "Friendly AI robot character with rounded features, soft lighting, approachable synthetic appearance",
                "creative": "Artistic AI being with digital patterns, creative synthetic design, abstract technological elements",
                "futuristic": "Advanced AI entity with futuristic design, holographic elements, sleek robotic appearance",
                "minimalist": "Clean AI avatar with simple geometric design, minimal synthetic features, abstract digital form"
            }
            
            base_prompt = style_prompts.get(request.style, style_prompts["professional"])
            
            logger.info(f"Generating profile picture for agent {agent_id} with prompt: {base_prompt}")
            
            # Generate image using OpenAI DALL-E
            try:
                # Get the OpenAI service and API key
                openai_service = get_openai_service()
                api_key = openai_service.api_key
                
                if not api_key:
                    logger.error("No OpenAI API key available")
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error", 
                            "message": "OpenAI API key not configured"
                        }
                    )
                
                # Create OpenAI client with the API key
                client = OpenAI(api_key=api_key)
                
                # Use the AI agent-focused prompt
                simple_prompt = base_prompt
                logger.info(f"Making DALL-E API call with simplified prompt: {simple_prompt}")
                logger.info(f"Parameters: model=gpt-image-1")
                
                # Use gpt-image-1 model as in your example
                response = client.images.generate(
                    model="gpt-image-1",
                    prompt=simple_prompt
                )
                
                # Extract base64 image data
                image_base64 = response.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)
                
                # Upload to Firebase Storage
                bucket = get_storage_bucket()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = f"temp_generated_images/{agent_id}/temp_{timestamp}.png"
                blob = bucket.blob(temp_path)
                blob.upload_from_string(image_bytes, content_type='image/png')
                blob.make_public()
                
                image_url = blob.public_url
                revised_prompt = simple_prompt
                
                logger.info(f"Successfully generated profile picture for agent {agent_id}")
                
                return {
                    "status": "success",
                    "agent_id": agent_id,
                    "image_url": image_url,
                    "prompt_used": base_prompt,
                    "revised_prompt": revised_prompt,
                    "style": request.style,
                    "size": request.size,
                    "quality": request.quality
                }
                
            except Exception as e:
                error_msg = str(e).lower()
                if "400" in error_msg or "bad request" in error_msg:
                    logger.error(f"OpenAI BadRequest error for agent {agent_id}: {str(e)}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "error", 
                            "message": f"Invalid request to image generation service. Please try a different style."
                        }
                    )
                elif "429" in error_msg or "rate limit" in error_msg:
                    logger.error(f"OpenAI RateLimit error for agent {agent_id}: {str(e)}")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "status": "error", 
                            "message": "Rate limit exceeded. Please try again in a few minutes."
                        }
                    )
                else:
                    logger.error(f"OpenAI DALL-E error for agent {agent_id}: {str(e)}")
                    logger.error(f"Error type: {type(e)}")
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error", 
                            "message": f"Failed to generate image: {str(e)}"
                        }
                    )
                
        except Exception as e:
            logger.error(f"Error generating profile picture for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

    @app.post("/api/agents/save-profile-picture")
    async def save_agent_profile_picture(
        request: Request, 
        user_id: str = Depends(get_current_user)
    ):
        """Save a generated profile picture to Firebase Storage and update agent config."""
        try:
            body = await request.json()
            agent_id = body.get("agent_id")
            image_url = body.get("image_url")
            
            if not agent_id or not image_url:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "agent_id and image_url are required"}
                )
            
            # Check if agent exists and user owns it
            agent_config = await default_storage.get_agent_config(agent_id)
            if not agent_config:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"Agent {agent_id} not found"}
                )
            
            if agent_config.get("userId") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "You do not have permission to save a profile picture for this agent"}
                )
            
            # Download the image from the URL
            try:
                image_response = requests.get(image_url, timeout=30)
                image_response.raise_for_status()
                image_data = image_response.content
                
                # Generate storage path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                storage_path = f"agent_profile_pictures/{agent_id}/profile_{timestamp}.png"
                
                # Upload to Firebase Storage
                bucket = get_storage_bucket()
                blob = bucket.blob(storage_path)
                blob.upload_from_string(image_data, content_type='image/png')
                blob.make_public()
                
                profile_picture_url = blob.public_url
                
                # Update agent config with profile picture URL
                profile_picture_data = {
                    "profile_picture_url": profile_picture_url,
                    "profile_picture_storage_path": storage_path,
                    "profile_picture_updated_at": firestore.SERVER_TIMESTAMP,
                    "profile_picture_style": body.get("style", "professional")
                }
                
                update_success = await default_storage.update_agent_config(agent_id, profile_picture_data)
                
                if not update_success:
                    # If Firestore update fails, try to delete the uploaded file
                    try:
                        blob.delete()
                    except:
                        pass
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": "Failed to update agent configuration"}
                    )
                
                logger.info(f"Successfully saved profile picture for agent {agent_id}")
                
                return {
                    "status": "success",
                    "agent_id": agent_id,
                    "profile_picture_url": profile_picture_url,
                    "storage_path": storage_path
                }
                
            except requests.RequestException as e:
                logger.error(f"Error downloading image for agent {agent_id}: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": f"Failed to download image: {str(e)}"}
                )
                
        except Exception as e:
            logger.error(f"Error saving profile picture for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )