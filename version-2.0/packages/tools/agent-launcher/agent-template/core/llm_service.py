"""
Direct LLM Service for high-performance AI interactions
"""

import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
import openai
import asyncio
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """LLM response with metadata"""
    content: str
    model: str
    token_usage: TokenUsage
    response_time: float
    timestamp: datetime
    finish_reason: str
    metadata: Dict[str, Any]


class DirectLLMService:
    """
    High-performance direct LLM service with token tracking
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        # Try to use alchemist-shared OpenAI config first
        openai_config = settings.get_openai_service()
        if openai_config:
            self.api_key = openai_config.get("api_key")
            self.alchemist_openai_config = openai_config
        else:
            self.api_key = api_key or settings.get_openai_api_key()
            self.alchemist_openai_config = None
        
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        
        # Token usage tracking
        self.total_usage = TokenUsage()
        self.session_usage = {}
        
        logger.info(f"DirectLLMService initialized with model: {model}")
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None,
                            tools: Optional[List[Dict[str, Any]]] = None,
                            stream: bool = False) -> LLMResponse:
        """
        Generate chat completion with comprehensive tracking
        
        Args:
            messages: List of message dictionaries
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            stream: Whether to stream the response
            
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            # Make API call
            if stream:
                return await self._stream_completion(params, start_time)
            else:
                response = await self.client.chat.completions.create(**params)
                return self._process_response(response, start_time)
                
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            # Return error response
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=self.model,
                token_usage=TokenUsage(),
                response_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                finish_reason="error",
                metadata={"error": str(e)}
            )
    
    async def _stream_completion(self, params: Dict[str, Any], start_time: float) -> LLMResponse:
        """Handle streaming completion"""
        content_chunks = []
        finish_reason = "stop"
        
        try:
            async for chunk in await self.client.chat.completions.create(**params):
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunks.append(chunk.choices[0].delta.content)
                
                if chunk.choices and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason
            
            content = "".join(content_chunks)
            
            # Estimate token usage for streaming (approximate)
            estimated_prompt_tokens = sum(len(msg.get("content", "").split()) for msg in params["messages"]) * 1.3
            estimated_completion_tokens = len(content.split()) * 1.3
            
            token_usage = TokenUsage(
                prompt_tokens=int(estimated_prompt_tokens),
                completion_tokens=int(estimated_completion_tokens),
                total_tokens=int(estimated_prompt_tokens + estimated_completion_tokens)
            )
            
            self._update_usage_tracking(token_usage)
            
            return LLMResponse(
                content=content,
                model=self.model,
                token_usage=token_usage,
                response_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                finish_reason=finish_reason,
                metadata={"streaming": True, "estimated_tokens": True}
            )
            
        except Exception as e:
            logger.error(f"Streaming completion failed: {e}")
            raise
    
    def _process_response(self, response, start_time: float) -> LLMResponse:
        """Process standard completion response"""
        
        # Extract content
        content = ""
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content or ""
        
        # Extract token usage
        token_usage = TokenUsage()
        if response.usage:
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
        
        # Extract finish reason
        finish_reason = "stop"
        if response.choices and response.choices[0].finish_reason:
            finish_reason = response.choices[0].finish_reason
        
        # Update usage tracking
        self._update_usage_tracking(token_usage)
        
        return LLMResponse(
            content=content,
            model=self.model,
            token_usage=token_usage,
            response_time=time.time() - start_time,
            timestamp=datetime.utcnow(),
            finish_reason=finish_reason,
            metadata={"streaming": False}
        )
    
    def _update_usage_tracking(self, token_usage: TokenUsage):
        """Update internal token usage tracking"""
        self.total_usage.prompt_tokens += token_usage.prompt_tokens
        self.total_usage.completion_tokens += token_usage.completion_tokens
        self.total_usage.total_tokens += token_usage.total_tokens
    
    async def stream_chat_completion(self, messages: List[Dict[str, str]], 
                                   temperature: float = 0.7,
                                   max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """
        Stream chat completion for real-time responses
        
        Args:
            messages: List of message dictionaries
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Content chunks as they arrive
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            async for chunk in await self.client.chat.completions.create(**params):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming completion failed: {e}")
            yield f"Error: {str(e)}"
    
    def get_token_usage(self) -> TokenUsage:
        """Get total token usage"""
        return self.total_usage
    
    def get_session_usage(self, session_id: str) -> TokenUsage:
        """Get token usage for specific session"""
        return self.session_usage.get(session_id, TokenUsage())
    
    def track_session_usage(self, session_id: str, token_usage: TokenUsage):
        """Track token usage for a session"""
        if session_id not in self.session_usage:
            self.session_usage[session_id] = TokenUsage()
        
        session_usage = self.session_usage[session_id]
        session_usage.prompt_tokens += token_usage.prompt_tokens
        session_usage.completion_tokens += token_usage.completion_tokens
        session_usage.total_tokens += token_usage.total_tokens
    
    def calculate_cost(self, token_usage: TokenUsage) -> float:
        """Calculate approximate cost based on token usage"""
        # Approximate pricing (update based on current OpenAI pricing)
        pricing = {
            "gpt-4": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
            "gpt-3.5-turbo": {"prompt": 0.001 / 1000, "completion": 0.002 / 1000}
        }
        
        model_pricing = pricing.get(self.model, pricing["gpt-4"])
        
        prompt_cost = token_usage.prompt_tokens * model_pricing["prompt"]
        completion_cost = token_usage.completion_tokens * model_pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def reset_usage_tracking(self):
        """Reset token usage tracking"""
        self.total_usage = TokenUsage()
        self.session_usage.clear()
        logger.info("Token usage tracking reset")
    
    async def health_check(self) -> bool:
        """Check if LLM service is healthy"""
        try:
            response = await self.chat_completion([
                {"role": "user", "content": "Hello"}
            ])
            return response.content is not None and "error" not in response.metadata
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model": self.model,
            "api_provider": "openai",
            "total_usage": {
                "prompt_tokens": self.total_usage.prompt_tokens,
                "completion_tokens": self.total_usage.completion_tokens,
                "total_tokens": self.total_usage.total_tokens,
                "estimated_cost": self.calculate_cost(self.total_usage)
            },
            "active_sessions": len(self.session_usage)
        }