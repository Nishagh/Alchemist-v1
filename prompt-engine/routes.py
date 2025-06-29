"""
Prompt Engineer Routes Module

This module defines the FastAPI routes for the Prompt Engineer Agent functionality.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api import prompt_engineer_api

# Import story event system for EA3 integration
from alchemist_shared.events import (
    get_story_event_publisher, 
    StoryEvent, 
    StoryEventType, 
    StoryEventPriority
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompt-engineer", tags=["prompt-engineer"])

class PromptInstructionsRequest(BaseModel):
    """Model for prompt instructions requests."""
    agent_id: str
    instructions: str

class PromptResponse(BaseModel):
    """Model for prompt responses."""
    agent_id: str
    prompt: str
    status: str
    created: bool
    error: Optional[str] = None
    thought_process: Optional[list] = None

@router.post("/prompt", response_model=PromptResponse)
async def create_or_update_prompt(
    request: PromptInstructionsRequest, 
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Create or update an agent's system prompt based on the provided instructions.
    If the agent already has a system prompt, it will be updated.
    If not, a new system prompt will be created.
    
    Args:
        request: The request containing agent_id and instructions
        
    Returns:
        Dictionary containing the resulting prompt and status
    """
    try:
        logger.info(f"Received request to create/update prompt for agent {request.agent_id}")
        
        # Call the API to create or update the prompt
        result = await prompt_engineer_api.update_agent_prompt(
            agent_id=request.agent_id,
            instructions=request.instructions
        )
        
        # Check for errors
        if "error" in result:
            # Make sure we include all required fields even for error responses
            return {
                "agent_id": request.agent_id,
                "status": "error",
                "error": result["error"],
                "prompt": "Error occurred - no prompt generated",  # Default value for error case
                "created": False,  # Default value for error case
                "thought_process": result.get("thought_process", [])
            }
        
        # Return the successful result
        created = result.get("mode", "") == "create"
        response = {
            "agent_id": request.agent_id,
            "prompt": result.get("updated_prompt", ""),
            "status": "success",
            "created": created,
            "thought_process": result.get("thought_process", [])
        }
        
        # Publish story event for EA3 tracking
        background_tasks.add_task(
            publish_prompt_update_event,
            request.agent_id,
            created,
            result.get("updated_prompt", ""),
            request.instructions
        )
        
        return response
        
    except Exception as e:
        error_message = f"Error in prompt engineer route: {str(e)}"
        logger.error(error_message)
        
        # For exceptions, also return a response that matches the model
        error_response = {
            "agent_id": request.agent_id,
            "status": "error",
            "error": error_message,
            "prompt": "Exception occurred - no prompt generated",
            "created": False,
            "thought_process": []
        }
        
        # We can either raise an HTTPException or return the error_response
        # Return the error response to match the expected response model
        return error_response


# Background task functions
async def publish_prompt_update_event(
    agent_id: str, 
    created: bool, 
    prompt: str, 
    instructions: str
):
    """Background task to publish prompt update as story event for EA3 tracking."""
    try:
        story_publisher = get_story_event_publisher()
        if story_publisher:
            event_type = StoryEventType.SYSTEM_UPDATE
            action = "created" if created else "updated"
            
            event = StoryEvent(
                agent_id=agent_id,
                event_type=event_type,
                content=f"Agent prompt {action} based on instructions: {instructions[:100]}...",
                source_service="prompt-engine",
                priority=StoryEventPriority.HIGH,  # Prompt changes are important for narrative
                metadata={
                    "action": action,
                    "prompt_length": len(prompt),
                    "instructions": instructions,
                    "created": created,
                    "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
                }
            )
            await story_publisher.publish_event(event)
            logger.debug(f"Published prompt {action} story event for agent {agent_id}")
    except Exception as e:
        logger.error(f"Failed to publish prompt update story event: {e}")