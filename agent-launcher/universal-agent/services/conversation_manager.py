"""
Conversation Manager Module

This module provides conversation state management and coordination between
the LLM service, tool system, and message history.
"""
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from datetime import datetime
from dataclasses import dataclass

from .direct_llm_service import DirectLLMService, LLMResponse, TokenUsage
from .direct_tool_system import ToolRegistry, ToolResult
from .message_types import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    ConversationHistory, MessageConverter
)

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Represents the current state of a conversation."""
    conversation_id: str
    history: ConversationHistory
    total_tokens: TokenUsage
    turn_count: int
    last_activity: datetime
    metadata: Dict[str, Any]


@dataclass
class ConversationResult:
    """Result from conversation processing."""
    response: str
    conversation_id: str
    turn_count: int
    token_usage: TokenUsage
    tool_calls_made: List[str]
    success: bool
    error: Optional[str] = None


class ConversationManager:
    """
    Manages conversation state and orchestrates interactions between
    LLM service, tools, and message history.
    
    Features:
    - Conversation state management
    - Tool execution coordination
    - Token usage tracking
    - Multi-turn conversation support
    - Streaming response support
    - Error handling and recovery
    """
    
    def __init__(
        self,
        llm_service: DirectLLMService,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
        max_turns_per_conversation: int = 50,
        max_tool_iterations: int = 10
    ):
        """
        Initialize conversation manager.
        
        Args:
            llm_service: Direct LLM service instance
            tool_registry: Tool registry for available tools
            system_prompt: Default system prompt
            max_turns_per_conversation: Maximum turns per conversation
            max_tool_iterations: Maximum tool call iterations per turn
        """
        self.llm_service = llm_service
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.max_turns_per_conversation = max_turns_per_conversation
        self.max_tool_iterations = max_tool_iterations
        
        # Active conversations
        self.conversations: Dict[str, ConversationState] = {}
        
        logger.info("ConversationManager initialized")
    
    def create_conversation(
        self,
        conversation_id: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Unique conversation identifier
            system_prompt: Custom system prompt for this conversation
            metadata: Additional conversation metadata
            
        Returns:
            ConversationState instance
        """
        history = ConversationHistory()
        
        # Set system prompt
        prompt = system_prompt or self.system_prompt
        if prompt:
            history.set_system_message(prompt)
        
        # Create conversation state
        state = ConversationState(
            conversation_id=conversation_id,
            history=history,
            total_tokens=TokenUsage(0, 0, 0),
            turn_count=0,
            last_activity=datetime.now(),
            metadata=metadata or {}
        )
        
        self.conversations[conversation_id] = state
        
        logger.info(f"Created conversation: {conversation_id}")
        return state
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation state by ID."""
        return self.conversations.get(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID to delete
            
        Returns:
            True if conversation was deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        user_id: Optional[str] = None,
        stream: bool = False
    ) -> ConversationResult:
        """
        Process a user message in a conversation.
        
        Args:
            conversation_id: Conversation ID
            message: User message
            user_id: Optional user identifier
            stream: Whether to stream the response
            
        Returns:
            ConversationResult
        """
        try:
            # Get or create conversation
            state = self.get_conversation(conversation_id)
            if not state:
                state = self.create_conversation(conversation_id)
            
            # Check conversation limits
            if state.turn_count >= self.max_turns_per_conversation:
                return ConversationResult(
                    response="Conversation limit reached. Please start a new conversation.",
                    conversation_id=conversation_id,
                    turn_count=state.turn_count,
                    token_usage=TokenUsage(0, 0, 0),
                    tool_calls_made=[],
                    success=False,
                    error="Conversation limit reached"
                )
            
            # Add user message to history
            state.history.add_human_message(message)
            
            # Process with tool calling
            if stream:
                # For streaming, we need to handle tool calls differently
                return await self._process_with_streaming(state, user_id)
            else:
                return await self._process_with_tools(state, user_id)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ConversationResult(
                response="I'm sorry, I encountered an error processing your message.",
                conversation_id=conversation_id,
                turn_count=state.turn_count if 'state' in locals() else 0,
                token_usage=TokenUsage(0, 0, 0),
                tool_calls_made=[],
                success=False,
                error=str(e)
            )
    
    async def _process_with_tools(
        self,
        state: ConversationState,
        user_id: Optional[str] = None
    ) -> ConversationResult:
        """Process message with tool calling support."""
        tool_calls_made = []
        iteration = 0
        
        while iteration < self.max_tool_iterations:
            iteration += 1
            
            # Get available tools
            tools = self.tool_registry.to_openai_format() if self.tool_registry.list_tools() else None
            
            # Generate response
            response = await self.llm_service.generate_response(
                messages=[msg for msg in state.history.get_messages()],
                tools=tools,
                tool_choice="auto" if tools else None
            )
            
            # Update token usage
            state.total_tokens += response.token_usage
            
            # Check if we need to call tools
            if response.tool_calls:
                # Add assistant message with tool calls
                state.history.add_ai_message(
                    content=response.content,
                    tool_calls=response.tool_calls
                )
                
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call["function"]["name"]
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    logger.info(f"Executing tool: {tool_name}")
                    tool_calls_made.append(tool_name)
                    
                    # Execute the tool
                    tool_result = await self.tool_registry.execute_tool(tool_name, arguments)
                    
                    # Format tool result
                    if tool_result.success:
                        result_content = json.dumps(tool_result.result) if tool_result.result else "Tool executed successfully"
                    else:
                        result_content = f"Tool error: {tool_result.error}"
                    
                    # Add tool result message
                    state.history.add_tool_message(
                        content=result_content,
                        tool_call_id=tool_call["id"],
                        tool_name=tool_name
                    )
                
                # Continue for final response
                continue
            else:
                # No tool calls, we have final response
                state.history.add_ai_message(content=response.content)
                state.turn_count += 1
                state.last_activity = datetime.now()
                
                return ConversationResult(
                    response=response.content,
                    conversation_id=state.conversation_id,
                    turn_count=state.turn_count,
                    token_usage=response.token_usage,
                    tool_calls_made=tool_calls_made,
                    success=True
                )
        
        # Max iterations reached
        error_msg = "Maximum tool iterations reached. Please try again."
        state.history.add_ai_message(content=error_msg)
        state.turn_count += 1
        state.last_activity = datetime.now()
        
        return ConversationResult(
            response=error_msg,
            conversation_id=state.conversation_id,
            turn_count=state.turn_count,
            token_usage=state.total_tokens,
            tool_calls_made=tool_calls_made,
            success=False,
            error="Max tool iterations reached"
        )
    
    async def _process_with_streaming(
        self,
        state: ConversationState,
        user_id: Optional[str] = None
    ) -> ConversationResult:
        """Process message with streaming support (simplified - no tool calls during streaming)."""
        # For streaming, we'll disable tool calls to keep it simple
        # In a more advanced implementation, you could handle tool calls in streaming mode
        
        response_content = ""
        
        try:
            # Generate streaming response
            stream = await self.llm_service.generate_response(
                messages=[msg for msg in state.history.get_messages()],
                stream=True
            )
            
            async for chunk in stream:
                response_content += chunk
            
            # Add messages to history
            state.history.add_ai_message(content=response_content)
            state.turn_count += 1
            state.last_activity = datetime.now()
            
            return ConversationResult(
                response=response_content,
                conversation_id=state.conversation_id,
                turn_count=state.turn_count,
                token_usage=TokenUsage(0, 0, 0),  # Token usage not available in streaming
                tool_calls_made=[],
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}")
            error_msg = "I'm sorry, I encountered an error while streaming the response."
            
            return ConversationResult(
                response=error_msg,
                conversation_id=state.conversation_id,
                turn_count=state.turn_count,
                token_usage=TokenUsage(0, 0, 0),
                tool_calls_made=[],
                success=False,
                error=str(e)
            )
    
    async def stream_response(
        self,
        conversation_id: str,
        message: str,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response for a message.
        
        Args:
            conversation_id: Conversation ID
            message: User message
            user_id: Optional user identifier
            
        Yields:
            Response chunks
        """
        try:
            # Get or create conversation
            state = self.get_conversation(conversation_id)
            if not state:
                state = self.create_conversation(conversation_id)
            
            # Add user message
            state.history.add_human_message(message)
            
            # Generate streaming response
            response_content = ""
            stream = await self.llm_service.generate_response(
                messages=[msg for msg in state.history.get_messages()],
                stream=True
            )
            
            async for chunk in stream:
                response_content += chunk
                yield chunk
            
            # Add complete response to history
            state.history.add_ai_message(content=response_content)
            state.turn_count += 1
            state.last_activity = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in stream_response: {str(e)}")
            yield f"Error: {str(e)}"
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        state = self.get_conversation(conversation_id)
        if not state:
            return []
        
        messages = state.history.get_messages(include_system=False)
        
        if limit:
            messages = messages[-limit:]
        
        return [msg.to_dict() for msg in messages]
    
    def get_conversation_stats(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation statistics.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Statistics dictionary or None if conversation not found
        """
        state = self.get_conversation(conversation_id)
        if not state:
            return None
        
        return {
            "conversation_id": conversation_id,
            "turn_count": state.turn_count,
            "message_count": len(state.history),
            "total_tokens": asdict(state.total_tokens),
            "last_activity": state.last_activity.isoformat(),
            "created_at": state.metadata.get("created_at"),
            "metadata": state.metadata
        }
    
    def list_conversations(self) -> List[str]:
        """List all active conversation IDs."""
        return list(self.conversations.keys())
    
    def cleanup_old_conversations(self, max_age_hours: int = 24) -> int:
        """
        Clean up old conversations.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of conversations cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        old_conversations = [
            conv_id for conv_id, state in self.conversations.items()
            if state.last_activity < cutoff_time
        ]
        
        for conv_id in old_conversations:
            del self.conversations[conv_id]
        
        if old_conversations:
            logger.info(f"Cleaned up {len(old_conversations)} old conversations")
        
        return len(old_conversations)


# Convenience function for creating a conversation manager
def create_conversation_manager(
    llm_service: DirectLLMService,
    tool_registry: ToolRegistry,
    system_prompt: str = "",
    **kwargs
) -> ConversationManager:
    """Create a ConversationManager instance."""
    return ConversationManager(
        llm_service=llm_service,
        tool_registry=tool_registry,
        system_prompt=system_prompt,
        **kwargs
    )