"""
Alchemist API Routes

This module organizes all API routes for the Alchemist system,
following the conversation-centric architecture with modular Firebase V9 approach.
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
from services.firebase_service import (
    get_conversation_repository, 
    get_firestore_service,
    ConversationRepository,
    FirestoreService
)
from agent import UserAgent


# Initialize logging
logger = logging.getLogger(__name__)

# Pydantic models for request bodies
class CreateConversationRequest(BaseModel):
    agent_id: str

class ProcessMessageRequest(BaseModel):
    agent_id: str
    conversation_id: str
    message: str

# User authentication dependency
async def get_current_user(
    userId_header: Optional[str] = Header(None, alias="userId"), 
    userId: Optional[str] = None
) -> str:
    """
    Validate the user ID from request headers or query parameters.
    This function will be used as a dependency for routes that require user authentication.
    """
    # Use header userId if available, otherwise use query parameter
    user_id = userId_header or userId
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID is required for this operation"
        )
    return user_id

def create_new_conversation(agent_id: str, repo: ConversationRepository = Depends(get_conversation_repository)) -> str:
    """
    Create a new conversation with the specified agent using the repository pattern.
    
    Args:
        agent_id: ID of the agent to use for this conversation
        repo: ConversationRepository dependency
    
    Returns:
        The ID of the new conversation
    """
    try:
        # Prepare conversation data
        conversation_data = {
            'agent_id': agent_id,
            'status': 'active',
            'message_count': 0
        }
        
        # Create conversation using repository
        conversation_id = repo.create_conversation(agent_id, conversation_data)
        
        logger.info(f"Created new conversation: {conversation_id} with agent: {agent_id}")
        return conversation_id
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise

def add_message_to_conversation(
    conversation_id: str,
    role: str,
    content: str,
    agent_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
) -> str:
    """
    Add a message to an existing conversation using the repository pattern.
    
    Args:
        conversation_id: ID of the conversation
        role: 'user' or 'agent'
        content: The message content
        agent_id: ID of the agent
        repo: ConversationRepository dependency
    
    Returns:
        The ID of the new message
    """
    try:
        # Prepare message data
        message_data = {
            'role': role,
            'content': content,
        }
        
        # Add message using repository
        message_id = repo.add_message(agent_id, conversation_id, message_data)
        
        logger.info(f"Added message from {role} to conversation: {conversation_id}")
        return message_id
    except Exception as e:
        logger.error(f"Failed to add message: {str(e)}")
        raise


async def process_message(
    conversation_id: str, 
    message: str, 
    agent_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
) -> Dict[str, Any]:
    """
    Process a user message in a conversation using the modular approach.
    
    Args:
        conversation_id: ID of the conversation
        message: The user's message
        agent_id: ID of the agent
        repo: ConversationRepository dependency
        
    Returns:
        Dictionary with the agent's response
    """
    try:
        # Add user message to conversation
        message_id = add_message_to_conversation(
            conversation_id=conversation_id,
            role='user',
            content=message,
            agent_id=agent_id,
            repo=repo
        )
        
        # Process with agent
        logger.info(f"Processing message with agent {agent_id}")
        
        try:                
            agent = UserAgent(agent_id=agent_id, conversation_id=conversation_id)
            agent.init_langchain()
            
            # UserAgent.process is async and expects a dict with 'message' key
            result = await agent.process({"message": message})
            
            if result.get('status') == 'success':
                response_text = result.get('response', '')
                logger.info("Successfully processed message with OpenAPI agent")
            else:
                response_text = result.get('message', 'Unknown error occurred')
                logger.error(f"Agent returned error: {response_text}")
                
        except Exception as e:
            logger.error(f"Error with OpenAPI agent: {str(e)}")
            response_text = f"Error processing your request: {str(e)}"
        
        # Add agent response to conversation
        logger.info(f"Response Text: {response_text[:100]}..." if len(response_text) > 100 else f"Response Text: {response_text}")
        response_id = add_message_to_conversation(
            conversation_id=conversation_id,
            role='agent',
            content=response_text,
            agent_id=agent_id,
            repo=repo
        )
        
        return {
            'conversation_id': conversation_id,
            'message_id': message_id,
            'response_id': response_id,
            'content': response_text
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise


def register_routes(app: FastAPI):
    """
    Register all API routes with the FastAPI app using modular dependencies
    """
    
    # Status endpoint
    @app.get("/api/status")
    async def get_api_status():
        """Check API connection status"""
        return {"status": "success", "message": "API is running"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint for the sandbox console service"""
        try:
            # Check OpenAI API key configuration
            openai_configured = bool(os.getenv('OPENAI_API_KEY'))
            
            # Check Firebase project configuration
            firebase_configured = bool(os.getenv('FIREBASE_PROJECT_ID'))
            
            # Check if tools are properly configured (basic check)
            tools_configured = True  # Simplified for now
            
            response_data = {
                "service": "sandbox-console",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "components": {
                    "openai": {
                        "status": "healthy" if openai_configured else "degraded",
                        "configured": openai_configured
                    },
                    "firebase": {
                        "status": "healthy" if firebase_configured else "degraded",
                        "configured": firebase_configured
                    },
                    "tools": {
                        "status": "healthy" if tools_configured else "degraded",
                        "configured": tools_configured
                    }
                }
            }
            
            # Determine overall status
            if not openai_configured or not firebase_configured or not tools_configured:
                response_data["status"] = "degraded"
            
            return response_data
            
        except Exception as e:
            error_response = {
                "service": "sandbox-console",
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            raise HTTPException(status_code=503, detail=error_response)
    
    @app.post("/api/agent/create_conversation")
    async def create_conversation_endpoint(
        request: CreateConversationRequest,
        repo: ConversationRepository = Depends(get_conversation_repository)
    ):
        """Create a new conversation for an agent using dependency injection."""
        try:
            logger.info(f"Creating new conversation for agent: {request.agent_id}")
            conversation_id = create_new_conversation(request.agent_id, repo)
            return {"status": "success", "conversation_id": conversation_id}
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
            
    @app.post("/api/agent/process_message")
    async def process_message_endpoint(
        request: ProcessMessageRequest,
        repo: ConversationRepository = Depends(get_conversation_repository)
    ):
        """Process a message for an agent using dependency injection."""
        try:
            response = await process_message(
                request.conversation_id, 
                request.message, 
                request.agent_id,
                repo
            )
            return {"status": "success", "response": response}
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    @app.get("/api/agent/{agent_id}/conversations/{conversation_id}/messages")
    async def get_conversation_messages(
        agent_id: str,
        conversation_id: str,
        limit: Optional[int] = Query(50, ge=1, le=100),
        repo: ConversationRepository = Depends(get_conversation_repository)
    ):
        """Get messages from a conversation with pagination."""
        try:
            messages = []
            for message_doc in repo.get_messages(agent_id, conversation_id, limit):
                message_data = message_doc.to_dict()
                message_data['id'] = message_doc.id
                messages.append(message_data)
            
            return {
                "status": "success", 
                "messages": messages,
                "count": len(messages)
            }
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    @app.get("/api/agent/{agent_id}/conversations/{conversation_id}")
    async def get_conversation(
        agent_id: str,
        conversation_id: str,
        repo: ConversationRepository = Depends(get_conversation_repository)
    ):
        """Get conversation details."""
        try:
            conversation = repo.get_conversation(agent_id, conversation_id)
            if not conversation.exists:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            conversation_data = conversation.to_dict()
            conversation_data['id'] = conversation.id
            
            return {"status": "success", "conversation": conversation_data}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}