"""
Tool Registry Service for managing available tools and function calling
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a registered tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    category: str = "general"
    enabled: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """
    Registry for managing available tools and function calling
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.tools: Dict[str, ToolInfo] = {}
        self.categories: Dict[str, List[str]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"Tool registry initialized for agent {agent_id}")
    
    def register_function_tool(self, name: str, description: str, 
                             parameters: Dict[str, Any], function: Callable,
                             category: str = "general", enabled: bool = True,
                             metadata: Dict[str, Any] = None):
        """
        Register a function tool
        
        Args:
            name: Tool name
            description: Tool description  
            parameters: JSON schema for tool parameters
            function: Function to execute
            category: Tool category
            enabled: Whether tool is enabled
            metadata: Additional metadata
        """
        try:
            if name in self.tools:
                logger.warning(f"Tool '{name}' already registered, updating...")
            
            tool_info = ToolInfo(
                name=name,
                description=description,
                parameters=parameters,
                function=function,
                category=category,
                enabled=enabled,
                metadata=metadata or {}
            )
            
            self.tools[name] = tool_info
            
            # Update category mapping
            if category not in self.categories:
                self.categories[category] = []
            if name not in self.categories[category]:
                self.categories[category].append(name)
            
            logger.info(f"Registered tool '{name}' in category '{category}'")
            
        except Exception as e:
            logger.error(f"Failed to register tool '{name}': {e}")
            raise
    
    def register_builtin_tools(self):
        """Register built-in tools for agent functionality"""
        try:
            # Memory tools
            self.register_function_tool(
                name="store_memory",
                description="Store important information in agent memory for later retrieval",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to store in memory"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.5
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorizing the memory"
                        }
                    },
                    "required": ["content"]
                },
                function=self._store_memory_tool,
                category="memory"
            )
            
            # Reflection tools
            self.register_function_tool(
                name="self_reflect",
                description="Trigger self-reflection on recent actions and decisions",
                parameters={
                    "type": "object",
                    "properties": {
                        "focus_area": {
                            "type": "string",
                            "description": "Area to focus reflection on (actions, decisions, learning, etc.)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context or specific situation to reflect on"
                        }
                    },
                    "required": ["focus_area"]
                },
                function=self._self_reflect_tool,
                category="reflection"
            )
            
            # Utility tools
            self.register_function_tool(
                name="get_current_time",
                description="Get current date and time",
                parameters={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Time format (iso, timestamp, readable)",
                            "enum": ["iso", "timestamp", "readable"],
                            "default": "iso"
                        }
                    }
                },
                function=self._get_current_time_tool,
                category="utility"
            )
            
            logger.info("Built-in tools registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register built-in tools: {e}")
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            tool_info = self.tools[tool_name]
            
            if not tool_info.enabled:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' is disabled"
                }
            
            # Record execution start
            execution_start = datetime.utcnow()
            
            # Execute the tool
            try:
                if asyncio.iscoroutinefunction(tool_info.function):
                    result = await tool_info.function(**parameters)
                else:
                    result = tool_info.function(**parameters)
                
                # Update usage statistics
                tool_info.usage_count += 1
                tool_info.last_used = datetime.utcnow()
                
                # Record execution in history
                execution_record = {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "result": result,
                    "timestamp": execution_start.isoformat(),
                    "duration": (datetime.utcnow() - execution_start).total_seconds(),
                    "success": True
                }
                self.execution_history.append(execution_record)
                
                # Keep only last 100 executions
                if len(self.execution_history) > 100:
                    self.execution_history = self.execution_history[-100:]
                
                logger.info(f"Tool '{tool_name}' executed successfully")
                
                return {
                    "success": True,
                    "result": result,
                    "execution_time": execution_record["duration"]
                }
                
            except Exception as e:
                # Record failed execution
                execution_record = {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "error": str(e),
                    "timestamp": execution_start.isoformat(),
                    "duration": (datetime.utcnow() - execution_start).total_seconds(),
                    "success": False
                }
                self.execution_history.append(execution_record)
                
                logger.error(f"Tool '{tool_name}' execution failed: {e}")
                
                return {
                    "success": False,
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        if tool_name not in self.tools:
            return None
        
        tool_info = self.tools[tool_name]
        return {
            "name": tool_info.name,
            "description": tool_info.description,
            "parameters": tool_info.parameters,
            "category": tool_info.category,
            "enabled": tool_info.enabled,
            "usage_count": tool_info.usage_count,
            "last_used": tool_info.last_used.isoformat() if tool_info.last_used else None,
            "metadata": tool_info.metadata
        }
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tools in a specific category"""
        if category not in self.categories:
            return []
        
        return [self.get_tool_info(tool_name) for tool_name in self.categories[category]]
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools"""
        return [self.get_tool_info(tool_name) for tool_name in self.tools.keys()]
    
    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """Get all enabled tools"""
        return [
            self.get_tool_info(tool_name) 
            for tool_name, tool_info in self.tools.items() 
            if tool_info.enabled
        ]
    
    def enable_tool(self, tool_name: str):
        """Enable a tool"""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = True
            logger.info(f"Tool '{tool_name}' enabled")
        else:
            logger.warning(f"Tool '{tool_name}' not found")
    
    def disable_tool(self, tool_name: str):
        """Disable a tool"""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = False
            logger.info(f"Tool '{tool_name}' disabled")
        else:
            logger.warning(f"Tool '{tool_name}' not found")
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            tool_info = self.tools[tool_name]
            del self.tools[tool_name]
            
            # Remove from category
            if tool_info.category in self.categories:
                if tool_name in self.categories[tool_info.category]:
                    self.categories[tool_info.category].remove(tool_name)
            
            logger.info(f"Tool '{tool_name}' unregistered")
        else:
            logger.warning(f"Tool '{tool_name}' not found")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        total_executions = sum(tool.usage_count for tool in self.tools.values())
        
        return {
            "total_tools": len(self.tools),
            "enabled_tools": len([t for t in self.tools.values() if t.enabled]),
            "total_executions": total_executions,
            "categories": {
                category: len(tools) for category, tools in self.categories.items()
            },
            "most_used_tools": sorted(
                [(name, tool.usage_count) for name, tool in self.tools.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "recent_executions": len(self.execution_history)
        }
    
    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    # Built-in tool implementations
    async def _store_memory_tool(self, content: str, importance: float = 0.5, tags: List[str] = None) -> str:
        """Store information in agent memory"""
        try:
            # This would integrate with the agent's memory system
            # For now, just log the memory storage
            logger.info(f"Storing memory: {content[:100]}... (importance: {importance})")
            
            return f"Memory stored successfully with importance {importance}"
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return f"Error storing memory: {str(e)}"
    
    async def _self_reflect_tool(self, focus_area: str, context: str = None) -> str:
        """Trigger self-reflection"""
        try:
            reflection_prompt = f"Reflecting on {focus_area}"
            if context:
                reflection_prompt += f" in context: {context}"
            
            # This would trigger the agent's self-reflection mechanism
            logger.info(f"Self-reflection triggered: {reflection_prompt}")
            
            return f"Self-reflection initiated on {focus_area}"
            
        except Exception as e:
            logger.error(f"Failed to trigger self-reflection: {e}")
            return f"Error in self-reflection: {str(e)}"
    
    def _get_current_time_tool(self, format: str = "iso") -> str:
        """Get current time in specified format"""
        try:
            now = datetime.utcnow()
            
            if format == "timestamp":
                return str(int(now.timestamp()))
            elif format == "readable":
                return now.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:  # iso format
                return now.isoformat()
                
        except Exception as e:
            logger.error(f"Failed to get current time: {e}")
            return f"Error getting time: {str(e)}"
    
    def get_tools(self) -> Dict[str, ToolInfo]:
        """Get raw tools dictionary (for internal use)"""
        return self.tools