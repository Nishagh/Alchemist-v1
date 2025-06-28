"""
Alchemist API Routes

This module organizes all API routes for the Alchemist system,
following the conversation-centric architecture.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends, File, UploadFile, Form, Header, Query
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel
from firebase_admin import firestore, storage
from firebase_admin.firestore import SERVER_TIMESTAMP
import yaml
import requests
import json

# Import Alchemist components
from alchemist.services.storage_service import default_storage
from alchemist.services.openai_init import initialize_openai
from alchemist.agents.orchestrator_agent import OrchestratorAgent
from alchemist.config.firebase_config import get_storage_bucket
from firebase_admin import auth

# Initialize logging first
logger = logging.getLogger(__name__)

# Import eA³ (Epistemic Autonomy) services (required)
from alchemist_shared.services import (
    get_ea3_orchestrator, ConversationContext
)
from alchemist_shared.events import get_story_event_publisher

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

# File validation functions
def validate_openapi_file(yaml_content: dict) -> bool:
    """Validate if the YAML content is an OpenAPI specification."""
    return ('openapi' in yaml_content or 'swagger' in yaml_content) and isinstance(yaml_content, dict)

def validate_mcp_config_file(yaml_content: dict) -> bool:
    """Validate if the YAML content is an MCP configuration."""
    # MCP config should have 'server' and 'tools' keys at root level
    return (
        isinstance(yaml_content, dict) and 
        'server' in yaml_content and 
        'tools' in yaml_content and
        isinstance(yaml_content.get('tools'), list)
    )

def detect_file_type(yaml_content: dict) -> str:
    """Detect if the YAML content is OpenAPI or MCP config."""
    if validate_openapi_file(yaml_content):
        return "openapi"
    elif validate_mcp_config_file(yaml_content):
        return "mcp_config"
    else:
        return "unknown"

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
            return {
                "status": "success", 
                "id": agent_id,
                "agent_id": agent_id,
                "data": agent_config
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
                
                # Initialize agent's life-story for eA³ (Epistemic Autonomy, Accountability, Alignment) - required
                ea3_orchestrator = get_ea3_orchestrator()
                core_objective = f"Assist users as a helpful AI agent specializing in: {message}"
                
                life_story_created = await ea3_orchestrator.create_agent_life_story(
                    agent_id=agent_id,
                    core_objective=core_objective,
                    agent_config=agent_config
                )
                
                if life_story_created:
                    logger.info(f"Initialized life-story for new agent {agent_id}")
                else:
                    logger.error(f"Failed to initialize life-story for agent {agent_id}")
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": "Failed to initialize agent life-story"}
                    )
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
            }
            
            result = await orchestrator.process(input_data)
            
            # eA³ (Epistemic Autonomy, Accountability, Alignment) processing with async story events - required
            ea3_orchestrator = get_ea3_orchestrator()
            
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
            
            # Publish story event asynchronously for microservices coordination - required
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
            ea3_orchestrator = get_ea3_orchestrator()
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
            ea3_orchestrator = get_ea3_orchestrator()
            
            # Check alignment drift
            alignment_check = await ea3_orchestrator.check_alignment_drift(agent_id)
            
            # Check narrative coherence
            coherence_check = await ea3_orchestrator.force_narrative_coherence_check(agent_id)
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "ea3_status": {
                    "alignment": alignment_check,
                    "coherence": coherence_check,
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
            ea3_orchestrator = get_ea3_orchestrator()
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

    # Unified YAML Upload Endpoint (Auto-detects OpenAPI vs MCP Config)
    @app.post("/api/agents/{agent_id}/config")
    async def upload_config_file(
        agent_id: str,
        file: UploadFile = File(...),
        user_id: str = Depends(get_current_user)
    ):
        """Upload a YAML configuration file (OpenAPI or MCP config) for an agent."""
        try:
            # Validate file type
            if not file.filename or not file.filename.lower().endswith(('.yaml', '.yml')):
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "File must be a YAML file (.yaml or .yml)"}
                )
            
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
                    content={"status": "error", "message": "You do not have permission to upload files for this agent"}
                )
            
            # Read and validate YAML content
            content = await file.read()
            try:
                yaml_content = yaml.safe_load(content)
                if not isinstance(yaml_content, dict):
                    raise ValueError("YAML content must be a dictionary")
                
                # Auto-detect file type
                file_type = detect_file_type(yaml_content)
                
                if file_type == "unknown":
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "error", 
                            "message": "File does not appear to be a valid OpenAPI specification or MCP configuration"
                        }
                    )
                    
            except yaml.YAMLError as e:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Invalid YAML format: {str(e)}"}
                )
            
            # Generate unique filename and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            bucket = get_storage_bucket()
            
            logger.info(f"Detected file type: {file_type} for agent {agent_id}")
            
            if file_type == "openapi":
                # Handle OpenAPI file - upload and convert to MCP config
                openapi_storage_filename = f"openapi_specs/{agent_id}/{timestamp}_{file.filename}"
                
                # Upload OpenAPI file to Firebase Storage
                openapi_blob = bucket.blob(openapi_storage_filename)
                openapi_blob.upload_from_string(content, content_type='application/x-yaml')
                openapi_blob.make_public()
                
                # Prepare conversion service request
                conversion_url = os.environ.get("MCP_CONFIG_GENERATOR_URL", "http://localhost:8080")
                server_name = f"agent_{agent_id}_api"
                
                request_data = {
                    "openapi_spec": content.decode('utf-8'),
                    "server_name": server_name,
                    "format": "yaml",
                    "validate": True
                }
                
                logger.info(f"Converting OpenAPI to MCP config for agent {agent_id}")
                
                # Call conversion service
                try:
                    response = requests.post(
                        f"{conversion_url}/convert",
                        json=request_data,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        conversion_data = response.json()
                        
                        if conversion_data.get('success'):
                            mcp_config = conversion_data.get('mcp_config', '')
                            
                            # Save MCP config to Firebase Storage
                            mcp_filename = f"mcp_configs/{agent_id}/{timestamp}_mcp_config.yaml"
                            mcp_blob = bucket.blob(mcp_filename)
                            mcp_blob.upload_from_string(mcp_config, content_type='application/x-yaml')
                            mcp_blob.make_public()
                            
                            # Prepare complete file info
                            file_info = {
                                "openapi_spec": {
                                    "filename": file.filename,
                                    "storage_path": openapi_storage_filename,
                                    "upload_timestamp": firestore.SERVER_TIMESTAMP,
                                    "file_size": len(content),
                                    "public_url": openapi_blob.public_url,
                                    "status": "uploaded"
                                },
                                "mcp_config": {
                                    "filename": f"{timestamp}_mcp_config.yaml",
                                    "storage_path": mcp_filename,
                                    "conversion_timestamp": firestore.SERVER_TIMESTAMP,
                                    "file_size": len(mcp_config.encode('utf-8')),
                                    "public_url": mcp_blob.public_url,
                                    "server_name": server_name,
                                    "status": "converted"
                                }
                            }
                            
                            # Update the agent's configuration
                            update_success = await default_storage.update_agent_config(agent_id, file_info)
                            
                            if not update_success:
                                # If Firestore update fails, try to delete the uploaded files
                                try:
                                    openapi_blob.delete()
                                    mcp_blob.delete()
                                except:
                                    pass
                                return JSONResponse(
                                    status_code=500,
                                    content={"status": "error", "message": "Failed to update agent configuration"}
                                )
                            
                            return {
                                "status": "success",
                                "message": "OpenAPI specification uploaded and converted to MCP config successfully",
                                "file_type": "openapi",
                                "agent_id": agent_id,
                                "files": {
                                    "openapi": {
                                        "filename": file.filename,
                                        "storage_path": openapi_storage_filename,
                                        "file_size": len(content),
                                        "public_url": openapi_blob.public_url
                                    },
                                    "mcp_config": {
                                        "filename": f"{timestamp}_mcp_config.yaml",
                                        "storage_path": mcp_filename,
                                        "file_size": len(mcp_config.encode('utf-8')),
                                        "public_url": mcp_blob.public_url,
                                        "server_name": server_name
                                    }
                                }
                            }
                        else:
                            error_msg = conversion_data.get('error', 'Unknown conversion error')
                            logger.error(f"Conversion failed for agent {agent_id}: {error_msg}")
                            
                            # Still save the OpenAPI file but mark conversion as failed
                            openapi_info = {
                                "openapi_spec": {
                                    "filename": file.filename,
                                    "storage_path": openapi_storage_filename,
                                    "upload_timestamp": firestore.SERVER_TIMESTAMP,
                                    "file_size": len(content),
                                    "public_url": openapi_blob.public_url,
                                    "status": "uploaded"
                                },
                                "conversion_error": {
                                    "error": error_msg,
                                    "timestamp": firestore.SERVER_TIMESTAMP
                                }
                            }
                            
                            await default_storage.update_agent_config(agent_id, openapi_info)
                            
                            return JSONResponse(
                                status_code=422,
                                content={
                                    "status": "partial_success",
                                    "message": "OpenAPI file uploaded but conversion to MCP config failed",
                                    "file_type": "openapi",
                                    "error": error_msg,
                                    "openapi_file": {
                                        "filename": file.filename,
                                        "public_url": openapi_blob.public_url
                                    }
                                }
                            )
                    else:
                        logger.error(f"Conversion service HTTP error {response.status_code}: {response.text}")
                        
                        # Still save the OpenAPI file but mark conversion as failed
                        openapi_info = {
                            "openapi_spec": {
                                "filename": file.filename,
                                "storage_path": openapi_storage_filename,
                                "upload_timestamp": firestore.SERVER_TIMESTAMP,
                                "file_size": len(content),
                                "public_url": openapi_blob.public_url,
                                "status": "uploaded"
                            },
                            "conversion_error": {
                                "error": f"HTTP {response.status_code}: {response.text}",
                                "timestamp": firestore.SERVER_TIMESTAMP
                            }
                        }
                        
                        await default_storage.update_agent_config(agent_id, openapi_info)
                        
                        return JSONResponse(
                            status_code=422,
                            content={
                                "status": "partial_success",
                                "message": "OpenAPI file uploaded but conversion service failed",
                                "file_type": "openapi",
                                "error": f"HTTP {response.status_code}",
                                "openapi_file": {
                                    "filename": file.filename,
                                    "public_url": openapi_blob.public_url
                                }
                            }
                        )
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Conversion service request failed for agent {agent_id}: {e}")
                    
                    # Still save the OpenAPI file but mark conversion as failed
                    openapi_info = {
                        "openapi_spec": {
                            "filename": file.filename,
                            "storage_path": openapi_storage_filename,
                            "upload_timestamp": firestore.SERVER_TIMESTAMP,
                            "file_size": len(content),
                            "public_url": openapi_blob.public_url,
                            "status": "uploaded"
                        },
                        "conversion_error": {
                            "error": f"Request failed: {str(e)}",
                            "timestamp": firestore.SERVER_TIMESTAMP
                        }
                    }
                    
                    await default_storage.update_agent_config(agent_id, openapi_info)
                    
                    return JSONResponse(
                        status_code=422,
                        content={
                            "status": "partial_success",
                            "message": "OpenAPI file uploaded but conversion service unreachable",
                            "file_type": "openapi",
                            "error": str(e),
                            "openapi_file": {
                                "filename": file.filename,
                                "public_url": openapi_blob.public_url
                            }
                        }
                    )
            
            elif file_type == "mcp_config":
                # Handle MCP config file - upload directly without conversion
                mcp_storage_filename = f"mcp_configs/{agent_id}/{timestamp}_{file.filename}"
                
                # Upload MCP config to Firebase Storage
                mcp_blob = bucket.blob(mcp_storage_filename)
                mcp_blob.upload_from_string(content, content_type='application/x-yaml')
                mcp_blob.make_public()
                
                # Prepare MCP config info for Firestore
                mcp_config_info = {
                    "mcp_config": {
                        "filename": file.filename,
                        "storage_path": mcp_storage_filename,
                        "upload_timestamp": firestore.SERVER_TIMESTAMP,
                        "file_size": len(content),
                        "public_url": mcp_blob.public_url,
                        "status": "uploaded_directly"
                    }
                }
                
                # Update the agent's configuration
                update_success = await default_storage.update_agent_config(agent_id, mcp_config_info)
                
                if not update_success:
                    # If Firestore update fails, try to delete the uploaded file
                    try:
                        mcp_blob.delete()
                    except:
                        pass
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": "Failed to update agent configuration"}
                    )
                
                return {
                    "status": "success",
                    "message": "MCP configuration uploaded successfully",
                    "file_type": "mcp_config",
                    "agent_id": agent_id,
                    "mcp_config": {
                        "filename": file.filename,
                        "storage_path": mcp_storage_filename,
                        "file_size": len(content),
                        "public_url": mcp_blob.public_url
                    }
                }
            
        except Exception as e:
            logger.error(f"Error uploading config file for agent {agent_id}: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Error: {str(e)}"}
            )

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