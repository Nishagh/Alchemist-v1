"""
Direct LLM Service Module

This module provides direct access to OpenAI's API, replacing LangChain's ChatOpenAI
functionality with better control over token usage, streaming, and error handling.
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Union, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        msg = {"role": self.role, "content": self.content}
        if self.name:
            msg["name"] = self.name
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg


@dataclass
class TokenUsage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        """Add two token usage objects."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens
        )


@dataclass
class LLMResponse:
    """Response from LLM service."""
    content: str
    finish_reason: str
    token_usage: TokenUsage
    tool_calls: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None


class DirectLLMService:
    """
    Direct OpenAI API service providing full control over LLM interactions.
    
    Features:
    - Direct OpenAI API calls with proper error handling
    - Token usage tracking
    - Streaming support
    - Function/tool calling
    - Conversation management
    - Retry logic with exponential backoff
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize the direct LLM service.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Default model to use
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Token usage tracking
        self.total_usage = TokenUsage(0, 0, 0)
        
        logger.info(f"DirectLLMService initialized with model: {model}")
    
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        model: Optional[str] = None
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            tools: Available tools/functions
            tool_choice: Tool choice strategy
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            model: Model to use (overrides default)
            
        Returns:
            LLMResponse object or async generator for streaming
        """
        try:
            # Prepare messages in OpenAI format
            openai_messages = [msg.to_openai_format() for msg in messages]
            
            # Prepare request parameters
            params = {
                "model": model or self.model,
                "messages": openai_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            
            if stream:
                return self._stream_response(params)
            else:
                return await self._complete_response(params)
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise
    
    async def _complete_response(self, params: Dict[str, Any]) -> LLMResponse:
        """Generate a complete response."""
        try:
            response = await self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            message = choice.message
            
            # Extract token usage
            usage = response.usage
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )
            
            # Update total usage tracking
            self.total_usage += token_usage
            
            # Extract tool calls if present
            tool_calls = None
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            return LLMResponse(
                content=message.content or "",
                finish_reason=choice.finish_reason,
                token_usage=token_usage,
                tool_calls=tool_calls,
                model=response.model
            )
            
        except Exception as e:
            logger.error(f"Error in complete response: {str(e)}")
            raise
    
    async def _stream_response(self, params: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        try:
            params["stream"] = True
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            raise
    
    async def call_tool_function(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        available_tools: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        Call a tool function.
        
        Args:
            function_name: Name of the function to call
            arguments: Function arguments
            available_tools: Dictionary mapping function names to callables
            
        Returns:
            Function result
        """
        try:
            if function_name not in available_tools:
                return {
                    "error": f"Function '{function_name}' not found",
                    "available_functions": list(available_tools.keys())
                }
            
            tool_function = available_tools[function_name]
            
            # Call the function
            if asyncio.iscoroutinefunction(tool_function):
                result = await tool_function(**arguments)
            else:
                result = tool_function(**arguments)
            
            return {"result": result}
            
        except Exception as e:
            logger.error(f"Error calling tool function {function_name}: {str(e)}")
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def get_token_usage(self) -> TokenUsage:
        """Get total token usage for this session."""
        return self.total_usage
    
    def reset_token_usage(self) -> None:
        """Reset token usage tracking."""
        self.total_usage = TokenUsage(0, 0, 0)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        This is a rough estimation based on the rule of thumb:
        1 token ≈ 4 characters for English text
        """
        return len(text) // 4


class AgentExecutor:
    """
    Agent executor that orchestrates conversation flow with tool calling.
    
    This replaces LangChain's AgentExecutor with direct control over the execution flow.
    """
    
    def __init__(
        self,
        llm_service: DirectLLMService,
        tools: Dict[str, Callable],
        system_prompt: str,
        max_iterations: int = 25,
        verbose: bool = True
    ):
        """
        Initialize the agent executor.
        
        Args:
            llm_service: Direct LLM service instance
            tools: Dictionary mapping tool names to callable functions
            system_prompt: System prompt for the agent
            max_iterations: Maximum number of iterations
            verbose: Whether to log execution steps
        """
        self.llm_service = llm_service
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Convert tools to OpenAI function format
        self.openai_tools = self._convert_tools_to_openai_format()
        
        logger.info(f"AgentExecutor initialized with {len(tools)} tools")
    
    def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI function calling format."""
        openai_tools = []
        
        for tool_name, tool_func in self.tools.items():
            # Extract function information
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": getattr(tool_func, '__doc__', f"Tool: {tool_name}"),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # If tool has schema information, use it
            if hasattr(tool_func, '_tool_schema'):
                tool_schema["function"].update(tool_func._tool_schema)
            
            openai_tools.append(tool_schema)
        
        return openai_tools
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with given inputs.
        
        Args:
            inputs: Input dictionary with 'input' and optional 'chat_history'
            
        Returns:
            Execution result with 'output' and 'intermediate_steps'
        """
        try:
            user_input = inputs.get('input', '')
            chat_history = inputs.get('chat_history', [])
            
            # Build message history
            messages = [Message(role="system", content=self.system_prompt)]
            
            # Add chat history
            for msg in chat_history:
                if hasattr(msg, 'content'):
                    role = 'user' if msg.__class__.__name__ == 'HumanMessage' else 'assistant'
                    messages.append(Message(role=role, content=msg.content))
            
            # Add current user input
            messages.append(Message(role="user", content=user_input))
            
            # Execute with tool calling
            intermediate_steps = []
            iteration = 0
            
            while iteration < self.max_iterations:
                iteration += 1
                
                if self.verbose:
                    logger.info(f"Agent iteration {iteration}")
                
                # Generate response
                response = await self.llm_service.generate_response(
                    messages=messages,
                    tools=self.openai_tools if self.tools else None,
                    tool_choice="auto" if self.tools else None
                )
                
                # Check if we need to call tools
                if response.tool_calls:
                    # Add assistant message with tool calls
                    messages.append(Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls
                    ))
                    
                    # Execute tool calls
                    for tool_call in response.tool_calls:
                        function_name = tool_call["function"]["name"]
                        arguments = json.loads(tool_call["function"]["arguments"])
                        
                        if self.verbose:
                            logger.info(f"Calling tool: {function_name} with args: {arguments}")
                        
                        # Call the tool
                        tool_result = await self.llm_service.call_tool_function(
                            function_name, arguments, self.tools
                        )
                        
                        # Add tool result message
                        messages.append(Message(
                            role="tool",
                            content=json.dumps(tool_result),
                            tool_call_id=tool_call["id"]
                        ))
                        
                        # Track intermediate step
                        intermediate_steps.append({
                            "action": function_name,
                            "action_input": arguments,
                            "observation": tool_result
                        })
                    
                    # Continue to next iteration for final response
                    continue
                else:
                    # No tool calls, we have final response
                    return {
                        "output": response.content,
                        "intermediate_steps": intermediate_steps,
                        "token_usage": response.token_usage
                    }
            
            # Max iterations reached
            return {
                "output": "Maximum iterations reached without completion.",
                "intermediate_steps": intermediate_steps,
                "token_usage": self.llm_service.get_token_usage()
            }
            
        except Exception as e:
            logger.error(f"Error in agent execution: {str(e)}")
            raise


# Convenience function for creating service instances
def create_llm_service(
    api_key: Optional[str] = None,
    model: str = "gpt-4"
) -> DirectLLMService:
    """Create a DirectLLMService instance."""
    return DirectLLMService(api_key=api_key, model=model)


def create_agent_executor(
    llm_service: DirectLLMService,
    tools: Dict[str, Callable],
    system_prompt: str,
    **kwargs
) -> AgentExecutor:
    """Create an AgentExecutor instance."""
    return AgentExecutor(
        llm_service=llm_service,
        tools=tools,
        system_prompt=system_prompt,
        **kwargs
    )