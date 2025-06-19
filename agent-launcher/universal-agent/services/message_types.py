"""
Message Types Module

This module provides message types and utilities to replace LangChain's message handling,
offering better control over conversation history and message formatting.
"""
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class BaseMessage:
    """Base class for all message types."""
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        result = asdict(self)
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseMessage':
        """Create message from dictionary."""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class HumanMessage(BaseMessage):
    """Message from a human user."""
    role: str = "user"
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class AIMessage(BaseMessage):
    """Message from an AI assistant."""
    role: str = "assistant"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        msg = {
            "role": self.role,
            "content": self.content
        }
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        return msg


@dataclass
class SystemMessage(BaseMessage):
    """System message providing instructions to the AI."""
    role: str = "system"
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class ToolMessage(BaseMessage):
    """Message containing tool execution results."""
    role: str = "tool"
    tool_call_id: str = ""
    tool_name: Optional[str] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        msg = {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id
        }
        if self.tool_name:
            msg["name"] = self.tool_name
        return msg


class MessageConverter:
    """Utility class for converting between message formats."""
    
    @staticmethod
    def from_langchain_message(lc_message) -> BaseMessage:
        """
        Convert a LangChain message to our message format.
        
        Args:
            lc_message: LangChain message object
            
        Returns:
            BaseMessage instance
        """
        content = getattr(lc_message, 'content', str(lc_message))
        
        # Determine message type based on class name
        class_name = lc_message.__class__.__name__
        
        if class_name == 'HumanMessage':
            return HumanMessage(content=content)
        elif class_name == 'AIMessage':
            tool_calls = getattr(lc_message, 'tool_calls', None)
            return AIMessage(content=content, tool_calls=tool_calls)
        elif class_name == 'SystemMessage':
            return SystemMessage(content=content)
        elif class_name == 'ToolMessage':
            tool_call_id = getattr(lc_message, 'tool_call_id', '')
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            # Default to human message
            return HumanMessage(content=content)
    
    @staticmethod
    def to_langchain_message(message: BaseMessage):
        """
        Convert our message to LangChain format (for backward compatibility).
        
        Args:
            message: Our message instance
            
        Returns:
            LangChain-compatible message
        """
        # This is for backward compatibility only
        # In practice, we'll use our own message types
        class LangChainMessage:
            def __init__(self, content: str, role: str = "user"):
                self.content = content
                self.role = role
            
            def __str__(self):
                return self.content
        
        return LangChainMessage(message.content, getattr(message, 'role', 'user'))
    
    @staticmethod
    def from_openai_message(openai_msg: Dict[str, Any]) -> BaseMessage:
        """
        Convert an OpenAI API message to our message format.
        
        Args:
            openai_msg: OpenAI API message dictionary
            
        Returns:
            BaseMessage instance
        """
        role = openai_msg.get('role', 'user')
        content = openai_msg.get('content', '')
        
        if role == 'user':
            return HumanMessage(content=content)
        elif role == 'assistant':
            tool_calls = openai_msg.get('tool_calls')
            return AIMessage(content=content, tool_calls=tool_calls)
        elif role == 'system':
            return SystemMessage(content=content)
        elif role == 'tool':
            tool_call_id = openai_msg.get('tool_call_id', '')
            tool_name = openai_msg.get('name')
            return ToolMessage(
                content=content,
                tool_call_id=tool_call_id,
                tool_name=tool_name
            )
        else:
            # Default to human message
            return HumanMessage(content=content)
    
    @staticmethod
    def messages_to_openai_format(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """
        Convert a list of messages to OpenAI API format.
        
        Args:
            messages: List of message instances
            
        Returns:
            List of OpenAI API message dictionaries
        """
        return [msg.to_openai_format() for msg in messages]
    
    @staticmethod
    def messages_from_openai_format(openai_messages: List[Dict[str, Any]]) -> List[BaseMessage]:
        """
        Convert OpenAI API messages to our message format.
        
        Args:
            openai_messages: List of OpenAI API message dictionaries
            
        Returns:
            List of message instances
        """
        return [MessageConverter.from_openai_message(msg) for msg in openai_messages]


class ConversationHistory:
    """
    Manages conversation history with support for message limits and context windows.
    """
    
    def __init__(self, max_messages: int = 100, max_tokens: Optional[int] = None):
        """
        Initialize conversation history.
        
        Args:
            max_messages: Maximum number of messages to keep
            max_tokens: Maximum token count (approximate)
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: List[BaseMessage] = []
        self.system_message: Optional[SystemMessage] = None
    
    def set_system_message(self, content: str) -> None:
        """Set the system message."""
        self.system_message = SystemMessage(content=content)
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history."""
        self.messages.append(message)
        self._trim_history()
    
    def add_human_message(self, content: str, **kwargs) -> None:
        """Add a human message."""
        message = HumanMessage(content=content, **kwargs)
        self.add_message(message)
    
    def add_ai_message(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None, **kwargs) -> None:
        """Add an AI message."""
        message = AIMessage(content=content, tool_calls=tool_calls, **kwargs)
        self.add_message(message)
    
    def add_tool_message(self, content: str, tool_call_id: str, tool_name: Optional[str] = None, **kwargs) -> None:
        """Add a tool message."""
        message = ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            **kwargs
        )
        self.add_message(message)
    
    def get_messages(self, include_system: bool = True) -> List[BaseMessage]:
        """
        Get all messages.
        
        Args:
            include_system: Whether to include system message
            
        Returns:
            List of messages
        """
        result = []
        
        if include_system and self.system_message:
            result.append(self.system_message)
        
        result.extend(self.messages)
        return result
    
    def get_openai_messages(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """
        Get messages in OpenAI API format.
        
        Args:
            include_system: Whether to include system message
            
        Returns:
            List of OpenAI API message dictionaries
        """
        messages = self.get_messages(include_system)
        return MessageConverter.messages_to_openai_format(messages)
    
    def clear(self) -> None:
        """Clear all messages except system message."""
        self.messages.clear()
    
    def clear_all(self) -> None:
        """Clear all messages including system message."""
        self.messages.clear()
        self.system_message = None
    
    def get_last_n_messages(self, n: int, include_system: bool = True) -> List[BaseMessage]:
        """
        Get the last N messages.
        
        Args:
            n: Number of messages to get
            include_system: Whether to include system message
            
        Returns:
            List of messages
        """
        result = []
        
        if include_system and self.system_message:
            result.append(self.system_message)
        
        # Get last n messages from conversation
        last_messages = self.messages[-n:] if n > 0 else []
        result.extend(last_messages)
        
        return result
    
    def _trim_history(self) -> None:
        """Trim history based on limits."""
        # Trim by message count
        if len(self.messages) > self.max_messages:
            excess = len(self.messages) - self.max_messages
            self.messages = self.messages[excess:]
        
        # TODO: Implement token-based trimming
        # This would require a tokenizer to count tokens accurately
        if self.max_tokens:
            # For now, we'll use a rough estimate
            total_chars = sum(len(msg.content) for msg in self.messages)
            estimated_tokens = total_chars // 4  # Rough estimate
            
            if estimated_tokens > self.max_tokens:
                # Remove oldest messages until under limit
                while len(self.messages) > 1:
                    self.messages.pop(0)
                    total_chars = sum(len(msg.content) for msg in self.messages)
                    estimated_tokens = total_chars // 4
                    
                    if estimated_tokens <= self.max_tokens:
                        break
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation history to dictionary."""
        return {
            "system_message": self.system_message.to_dict() if self.system_message else None,
            "messages": [msg.to_dict() for msg in self.messages],
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationHistory':
        """Create conversation history from dictionary."""
        history = cls(
            max_messages=data.get('max_messages', 100),
            max_tokens=data.get('max_tokens')
        )
        
        # Load system message
        if data.get('system_message'):
            history.system_message = SystemMessage.from_dict(data['system_message'])
        
        # Load messages
        for msg_data in data.get('messages', []):
            msg_type = msg_data.get('role', 'user')
            
            if msg_type == 'user':
                message = HumanMessage.from_dict(msg_data)
            elif msg_type == 'assistant':
                message = AIMessage.from_dict(msg_data)
            elif msg_type == 'system':
                message = SystemMessage.from_dict(msg_data)
            elif msg_type == 'tool':
                message = ToolMessage.from_dict(msg_data)
            else:
                message = HumanMessage.from_dict(msg_data)
            
            history.messages.append(message)
        
        return history
    
    def __len__(self) -> int:
        """Get number of messages (excluding system message)."""
        return len(self.messages)
    
    def __getitem__(self, index: int) -> BaseMessage:
        """Get message by index."""
        return self.messages[index]


# Backward compatibility functions
def create_human_message(content: str) -> HumanMessage:
    """Create a human message (backward compatibility)."""
    return HumanMessage(content=content)


def create_ai_message(content: str, **kwargs) -> AIMessage:
    """Create an AI message (backward compatibility)."""
    return AIMessage(content=content, **kwargs)


def create_system_message(content: str) -> SystemMessage:
    """Create a system message (backward compatibility)."""
    return SystemMessage(content=content)