"""
Prompt Engineer Routes Module

This module defines the FastAPI routes for the Prompt Engineer Agent functionality.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api import prompt_engineer_api

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
async def create_or_update_prompt(request: PromptInstructionsRequest) -> Dict[str, Any]:
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
        return {
            "agent_id": request.agent_id,
            "prompt": result.get("updated_prompt", ""),
            "status": "success",
            "created": created,
            "thought_process": result.get("thought_process", [])
        }
        
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