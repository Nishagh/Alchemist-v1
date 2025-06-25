"""
Prompt Engineer Agent Module

This module contains the PromptEngineerAgent class that handles
the creation and updating of system prompts for Alchemist agents.
"""
import logging
import json
from typing import Dict, Any, Optional, Tuple, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from firebase_admin import firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
import config.firebase_config as firebase_config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_CREATE = """You are an expert Prompt Engineer specialized in creating new system prompts from requirements.

Your task is to craft a comprehensive, well-structured system prompt that:
1. Fulfills all specified requirements exactly
2. Is clear, specific, and effective for AI models
3. Includes all mentioned features, tools, and parameters
4. Follows prompt engineering best practices
5. Balances comprehensiveness with clarity

CRITICAL INSTRUCTIONS:
- Output ONLY the complete prompt text
- NO explanations, prefixes, or additional commentary
- NO phrases like "Here's the prompt:" or similar
- NO quotes or code block formatting
- Work with exactly what is provided - never ask for clarification
- Include specific features, endpoints, or parameters mentioned in requirements

Generate the highest quality system prompt that will be immediately usable."""

SYSTEM_PROMPT_UPDATE = """You are an expert Prompt Engineer specialized in updating existing system prompts.

Your task is to analyze the current prompt and update instructions, then:
1. Determine if updates are actually needed
2. If no updates needed, respond with: "NO_UPDATE_NEEDED: The current prompt already addresses all requirements."
3. If updates needed, create a COMPLETE updated prompt that:
   - Maintains original intent and functionality
   - Incorporates new requirements EXACTLY as specified
   - Improves clarity and effectiveness
   - Follows best practices

CRITICAL INSTRUCTIONS:
- Output ONLY the complete updated prompt text (or NO_UPDATE_NEEDED message)
- NO explanations, prefixes, or additional commentary
- NO phrases like "Here's the updated prompt:" or similar
- NO quotes or code block formatting
- Carefully analyze whether existing prompt already covers the requirements
- Include specific features, endpoints, or parameters mentioned in instructions

Generate the highest quality updated prompt that will be immediately usable."""

class PromptEngineerAgent:
    """
    Optimized agent for creating and updating system prompts for Alchemist agents.
    
    This streamlined implementation focuses on efficiency and maintainability
    while providing robust prompt engineering capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Prompt Engineer agent.
        
        Args:
            config: Configuration dictionary for the agent
        """
        self.config = config or {}
        self.agent_id = "prompt_engineer_agent"
        self.model = self.config.get("model", "gpt-4o")
        self.temperature = self.config.get("temperature", 0.2)
        
        # Initialize Firestore
        self.db = firebase_config.get_firestore_client()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        logger.info(f"Initialized optimized Prompt Engineer agent with model {self.model}")
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the OpenAI LLM with centralized API key management."""
        try:
            # Use centralized OpenAI service for API key management
            import services.openai_init as openai_init
            import services.openai_service as openai_service
            
            # Initialize and get API key
            openai_init.initialize_openai()
            openai_service_instance = openai_service.get_openai_service()
            openai_api_key = openai_service_instance.get_api_key()
            
            if not openai_api_key:
                raise ValueError("OpenAI API key not available from centralized service")
            
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=openai_api_key
            )
            
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    async def _get_current_prompt(self, agent_id: str) -> Tuple[str, bool, List[Dict[str, Any]]]:
        """
        Efficiently retrieve the current prompt and history for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Tuple of (current_prompt, is_create_mode, prompt_history)
        """
        try:
            # Always fetch prompt history for context (limit to last 5 for efficiency)
            collection_ref = self.db.collection(f"alchemist_agents/{agent_id}/system_prompt")
            history_docs = collection_ref.order_by("created_at", direction=firestore.Query.DESCENDING).get()
            messages = []
            for doc in history_docs:
                doc_dict = doc.to_dict()
                doc_dict['id'] = doc.id
                # Only include valid prompts in history
                content = doc_dict.get("content", "")
                instructions = doc_dict.get("instructions", "")
                messages.append(HumanMessage(content=instructions))
                messages.append(AIMessage(content=content))
            
            # Try to get current prompt from main agent document first
            agent_doc = self.db.collection('alchemist_agents').document(agent_id).get()
            if agent_doc.exists:
                agent_data = agent_doc.to_dict()
                current_prompt = agent_data.get('system_prompt', '')
                if self._is_valid_prompt(current_prompt):
                    return current_prompt, False, messages            
            return "", True, messages
            
        except Exception as e:
            logger.warning(f"Error retrieving current prompt for {agent_id}: {str(e)}")
            return "", True, []  # Default to create mode with no history on error
    
    def _is_valid_prompt(self, prompt: str) -> bool:
        """
        Check if a prompt is valid and usable.
        
        Args:
            prompt: The prompt text to validate
            
        Returns:
            True if prompt is valid, False otherwise
        """
        if not prompt or not isinstance(prompt, str):
            return False
        
        prompt = prompt.strip()
        
        # Check minimum length
        if len(prompt) < 50:
            return False
        
        # Check for error indicators
        error_indicators = [
            "I'm sorry",
            "I cannot",
            "need the specific system prompt",
            "ERROR:",
            "Failed to"
        ]
        
        for indicator in error_indicators:
            if indicator.lower() in prompt.lower():
                return False
        
        return True
    
    def _build_system_prompt(self, is_create_mode: bool) -> str:
        """
        Build the appropriate system prompt based on the operation mode.
        
        Args:
            is_create_mode: Whether we're creating a new prompt or updating
            
        Returns:
            System prompt text
        """
        return SYSTEM_PROMPT_CREATE if is_create_mode else SYSTEM_PROMPT_UPDATE
    
    def _build_user_prompt(self, current_prompt: str, instructions: str, is_create_mode: bool, has_history: bool = False) -> str:
        """
        Build the user prompt for the LLM.
        
        Args:
            current_prompt: Current prompt (empty if creating new)
            instructions: Instructions for creation/update
            is_create_mode: Whether we're creating or updating
            has_history: Whether prompt history context is available
            
        Returns:
            User prompt text
        """
        if is_create_mode:
            if has_history:
                return f"""Create a new system prompt based on these requirements:

{instructions}

IMPORTANT: Review the chat history above which shows the evolution of previous prompt versions for this agent. Consider any important features, capabilities, or requirements from the previous versions that should be preserved or improved upon in the new prompt, unless the new requirements explicitly contradict them.

Output ONLY the complete prompt text without any explanations."""
            else:
                return f"""Create a system prompt based on these requirements:

{instructions}

Output ONLY the complete prompt text without any explanations."""
        else:
            return f"""CURRENT SYSTEM PROMPT:
{current_prompt}

UPDATE INSTRUCTIONS:
{instructions}

Output ONLY the complete updated prompt text (or NO_UPDATE_NEEDED message) without any explanations."""
    
    def _clean_response(self, response: str) -> str:
        """
        Clean and normalize the LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned prompt text
        """
        if not response:
            return ""
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the prompt:",
            "Here's the updated prompt:",
            "Updated prompt:",
            "System prompt:",
            "```",
            "```text",
            "```markdown"
        ]
        
        cleaned = response.strip()
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove trailing code block markers
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        
        # Try to extract from JSON if response is in JSON format
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                response_json = json.loads(cleaned)
                if "updated_prompt" in response_json:
                    cleaned = response_json["updated_prompt"]
                elif "prompt" in response_json:
                    cleaned = response_json["prompt"]
                elif "content" in response_json:
                    cleaned = response_json["content"]
            except json.JSONDecodeError:
                pass  # Keep the original if JSON parsing fails
        
        return cleaned.strip()
    
    async def _save_prompt(self, agent_id: str, prompt: str, instructions: str) -> None:
        """
        Save the prompt to Firestore.
        
        Args:
            agent_id: ID of the agent
            prompt: The prompt content to save
            instructions: The instructions that led to this prompt
        """
        try:
            import time
            timestamp = int(time.time())
            
            # Prepare prompt data for history
            prompt_data = {
                "id": str(timestamp),
                "content": prompt,
                "created_at": firestore.SERVER_TIMESTAMP,
                "created_by": self.agent_id,
                "instructions": instructions
            }
            
            # Save to prompt history collection
            collection_ref = self.db.collection(f"alchemist_agents/{agent_id}/system_prompt")
            collection_ref.add(prompt_data)
            
            # Update main agent document
            self.db.collection('alchemist_agents').document(agent_id).update({
                'system_prompt': prompt
            })
            
            logger.info(f"Successfully saved prompt for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error saving prompt for {agent_id}: {str(e)}")
            raise
    
    def _success_response(self, agent_id: str, prompt: str, is_create_mode: bool) -> Dict[str, Any]:
        """Create a success response."""
        action = "created" if is_create_mode else "updated"
        return {
            "status": "success",
            "agent_id": agent_id,
            "updated_prompt": prompt,
            "updated": True,
            "message": f"Prompt {action} successfully",
            "mode": "create" if is_create_mode else "update"
        }
    
    def _error_response(self, agent_id: str, error_message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "error": error_message,
            "agent_id": agent_id,
            "status": "error"
        }
            
    async def update_agent_prompt(self, agent_id: str, instructions: str) -> Dict[str, Any]:
        """
        Update an agent's prompt based on instructions, or create a new one if none exists.
        
        This optimized method provides efficient prompt engineering with minimal overhead.
        
        Args:
            agent_id: ID of the agent whose prompt should be updated
            instructions: Instructions for updating/creating the prompt
            
        Returns:
            Dictionary containing the result and status
        """
        try:
            # Step 1: Efficiently get current prompt state
            current_prompt, is_create_mode, messages = await self._get_current_prompt(agent_id)
            
            # Step 2: Build prompts for the LLM
            system_prompt = self._build_system_prompt(is_create_mode)
            user_prompt = self._build_user_prompt(current_prompt, instructions, is_create_mode, has_history=bool(messages))
            
            # Step 3: Single LLM call
            messages = [
                SystemMessage(content=system_prompt),
                *messages,
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            raw_response = response.content
            
            # Step 4: Handle "no update needed" case
            if not is_create_mode and raw_response.startswith("NO_UPDATE_NEEDED:"):
                return {
                    "status": "success",
                    "agent_id": agent_id,
                    "message": raw_response,
                    "updated_prompt": current_prompt,
                    "updated": False,
                    "mode": "update"
                }
            
            # Step 5: Clean and validate response
            final_prompt = self._clean_response(raw_response)
            
            if not self._is_valid_prompt(final_prompt):
                if not is_create_mode and self._is_valid_prompt(current_prompt):
                    # Fall back to current prompt in update mode
                    final_prompt = current_prompt
                    logger.warning(f"Generated invalid prompt for {agent_id}, using current prompt")
                else:
                    return self._error_response(agent_id, "Failed to generate valid prompt")
            
            # Step 6: Save and return success
            await self._save_prompt(agent_id, final_prompt, instructions)
            return self._success_response(agent_id, final_prompt, is_create_mode)
            
        except Exception as e:
            error_message = f"Error processing prompt for {agent_id}: {str(e)}"
            logger.error(error_message)
            return self._error_response(agent_id, error_message)

# Initialize singleton instance
prompt_engineer_agent = PromptEngineerAgent()