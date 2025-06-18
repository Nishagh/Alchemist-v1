"""
Prompt Engineer API Module

This module provides an API interface to the Prompt Engineer Agent functionality.
"""
import logging
from typing import Dict, Any, Optional

from agent import prompt_engineer_agent

logger = logging.getLogger(__name__)

class PromptEngineerAPI:
    """
    API for the Prompt Engineer Agent functionality.
    
    This class provides methods to create or update agent prompts through the Prompt Engineer Agent.
    """
    
    @staticmethod
    async def update_agent_prompt(agent_id: str, instructions: str) -> Dict[str, Any]:
        """
        Create or update an agent's prompt based on the provided instructions.
        If the agent already has a system prompt, it will be updated.
        If not, a new system prompt will be created.
        
        Args:
            agent_id: ID of the agent whose prompt should be created/updated
            instructions: Instructions for creating or updating the prompt
            
        Returns:
            Dictionary containing the prompt and status
        """
        try:
            logger.info(f"Creating or updating prompt for agent {agent_id}")
            
            # Use the prompt engineer agent to create/update the prompt
            result = await prompt_engineer_agent.update_agent_prompt(agent_id, instructions)
            
            return result
        
        except Exception as e:
            error_message = f"Error in prompt engineer API: {str(e)}"
            logger.error(error_message)
            
            return {
                "error": error_message,
                "agent_id": agent_id
            }

# Create a singleton instance
prompt_engineer_api = PromptEngineerAPI()