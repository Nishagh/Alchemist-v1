"""
Direct Tool System Module

This module provides a direct tool system to replace LangChain's tool functionality,
offering better control over tool registration, execution, and schema management.
"""
import json
import logging
import asyncio
import inspect
from typing import Dict, Any, List, Optional, Callable, Union, get_type_hints
from dataclasses import dataclass, asdict
from enum import Enum
import functools

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Represents a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum_values: Optional[List[str]] = None


@dataclass
class ToolSchema:
    """Represents a tool schema for OpenAI function calling."""
    name: str
    description: str
    parameters: List[ToolParameter]
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            
            if param.enum_values:
                prop["enum"] = param.enum_values
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolError(Exception):
    """Exception raised during tool execution."""
    pass


class DirectTool:
    """
    Direct tool implementation replacing LangChain's Tool class.
    
    Features:
    - Automatic schema generation from function signatures
    - Type validation
    - Async and sync function support
    - Error handling and logging
    - Metadata support
    """
    
    def __init__(
        self,
        name: str,
        func: Callable,
        description: Optional[str] = None,
        schema: Optional[ToolSchema] = None,
        validate_input: bool = True
    ):
        """
        Initialize a direct tool.
        
        Args:
            name: Tool name
            func: Function to execute
            description: Tool description
            schema: Tool schema (auto-generated if not provided)
            validate_input: Whether to validate input parameters
        """
        self.name = name
        self.func = func
        self.description = description or getattr(func, '__doc__', f"Tool: {name}")
        self.validate_input = validate_input
        self.is_async = asyncio.iscoroutinefunction(func)
        
        # Generate schema if not provided
        self.schema = schema or self._generate_schema()
        
        logger.info(f"DirectTool '{name}' registered ({'async' if self.is_async else 'sync'})")
    
    def _generate_schema(self) -> ToolSchema:
        """Generate tool schema from function signature."""
        sig = inspect.signature(self.func)
        type_hints = get_type_hints(self.func)
        
        parameters = []
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == 'self':
                continue
            
            # Get type information
            param_type = type_hints.get(param_name, str)
            
            # Convert Python types to JSON schema types
            json_type = self._python_type_to_json_type(param_type)
            
            # Extract description from parameter annotation or docstring
            description = f"Parameter: {param_name}"
            
            # Check if parameter is required
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default
            
            # Handle enum values
            enum_values = None
            if hasattr(param_type, '__members__'):  # Enum type
                enum_values = list(param_type.__members__.keys())
            
            parameters.append(ToolParameter(
                name=param_name,
                type=json_type,
                description=description,
                required=required,
                default=default,
                enum_values=enum_values
            ))
        
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters
        )
    
    def _python_type_to_json_type(self, python_type: type) -> str:
        """Convert Python type to JSON schema type."""
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        
        # Handle Union types (like Optional)
        if hasattr(python_type, '__origin__'):
            if python_type.__origin__ is Union:
                # For Optional types, get the non-None type
                args = [arg for arg in python_type.__args__ if arg is not type(None)]
                if args:
                    python_type = args[0]
        
        return type_mapping.get(python_type, "string")
    
    def _validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert arguments according to schema."""
        if not self.validate_input:
            return arguments
        
        validated = {}
        
        for param in self.schema.parameters:
            value = arguments.get(param.name)
            
            # Check required parameters
            if param.required and value is None:
                raise ToolError(f"Required parameter '{param.name}' is missing")
            
            # Use default if not provided
            if value is None and param.default is not None:
                value = param.default
            
            # Type conversion
            if value is not None:
                try:
                    if param.type == "integer":
                        value = int(value)
                    elif param.type == "number":
                        value = float(value)
                    elif param.type == "boolean":
                        if isinstance(value, str):
                            value = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            value = bool(value)
                    elif param.type == "string":
                        value = str(value)
                    # Arrays and objects are kept as-is
                    
                    # Check enum values
                    if param.enum_values and value not in param.enum_values:
                        raise ToolError(f"Parameter '{param.name}' must be one of: {param.enum_values}")
                    
                except (ValueError, TypeError) as e:
                    raise ToolError(f"Invalid type for parameter '{param.name}': {str(e)}")
            
            if value is not None:
                validated[param.name] = value
        
        return validated
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given arguments.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            ToolResult object
        """
        try:
            # Validate arguments
            validated_args = self._validate_arguments(arguments)
            
            # Execute function
            if self.is_async:
                result = await self.func(**validated_args)
            else:
                result = self.func(**validated_args)
            
            return ToolResult(
                success=True,
                result=result,
                metadata={"tool_name": self.name, "arguments": validated_args}
            )
            
        except ToolError as e:
            logger.error(f"Tool validation error in '{self.name}': {str(e)}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                metadata={"tool_name": self.name, "arguments": arguments}
            )
        except Exception as e:
            logger.error(f"Tool execution error in '{self.name}': {str(e)}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool execution failed: {str(e)}",
                metadata={"tool_name": self.name, "arguments": arguments}
            )
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format."""
        return self.schema.to_openai_format()


class ToolRegistry:
    """
    Registry for managing tools.
    
    Features:
    - Tool registration and discovery
    - Namespace support
    - Bulk operations
    - Schema management
    """
    
    def __init__(self, namespace: str = "default"):
        """
        Initialize tool registry.
        
        Args:
            namespace: Namespace for this registry
        """
        self.namespace = namespace
        self.tools: Dict[str, DirectTool] = {}
        
        logger.info(f"ToolRegistry initialized for namespace: {namespace}")
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: Optional[str] = None,
        schema: Optional[ToolSchema] = None,
        **kwargs
    ) -> DirectTool:
        """
        Register a tool.
        
        Args:
            name: Tool name
            func: Function to execute
            description: Tool description
            schema: Tool schema
            **kwargs: Additional tool options
            
        Returns:
            DirectTool instance
        """
        if name in self.tools:
            logger.warning(f"Tool '{name}' already exists, overwriting")
        
        tool = DirectTool(
            name=name,
            func=func,
            description=description,
            schema=schema,
            **kwargs
        )
        
        self.tools[name] = tool
        logger.info(f"Tool '{name}' registered in namespace '{self.namespace}'")
        
        return tool
    
    def register_from_functions(self, functions: Dict[str, Callable]) -> None:
        """
        Register multiple tools from a dictionary of functions.
        
        Args:
            functions: Dictionary mapping names to functions
        """
        for name, func in functions.items():
            self.register_tool(name, func)
    
    def get_tool(self, name: str) -> Optional[DirectTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self.tools
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def get_all_tools(self) -> Dict[str, DirectTool]:
        """Get all registered tools."""
        return self.tools.copy()
    
    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool.
        
        Args:
            name: Tool name to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Tool '{name}' removed from namespace '{self.namespace}'")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all tools."""
        self.tools.clear()
        logger.info(f"All tools cleared from namespace '{self.namespace}'")
    
    def to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert all tools to OpenAI function calling format."""
        return [tool.to_openai_format() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            ToolResult object
        """
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{name}' not found",
                metadata={"available_tools": self.list_tools()}
            )
        
        return await tool.execute(arguments)


# Decorators for easy tool registration
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    registry: Optional[ToolRegistry] = None
):
    """
    Decorator to register a function as a tool.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        registry: Tool registry to register with (uses default if not provided)
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__
        
        # Register with provided registry or create a default one
        if registry:
            registry.register_tool(tool_name, func, tool_description)
        else:
            # Store in function for later registration
            func._tool_name = tool_name
            func._tool_description = tool_description
        
        return func
    
    return decorator


# Default global registry
default_registry = ToolRegistry("global")


# Convenience functions
def register_tool(name: str, func: Callable, **kwargs) -> DirectTool:
    """Register a tool with the default registry."""
    return default_registry.register_tool(name, func, **kwargs)


def get_tool(name: str) -> Optional[DirectTool]:
    """Get a tool from the default registry."""
    return default_registry.get_tool(name)


def execute_tool(name: str, arguments: Dict[str, Any]) -> ToolResult:
    """Execute a tool from the default registry."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(default_registry.execute_tool(name, arguments))


def get_all_tools() -> Dict[str, DirectTool]:
    """Get all tools from the default registry."""
    return default_registry.get_all_tools()


def tools_to_openai_format() -> List[Dict[str, Any]]:
    """Convert all tools from default registry to OpenAI format."""
    return default_registry.to_openai_format()


# Backward compatibility classes
class BaseTool:
    """Backward compatibility with LangChain's BaseTool."""
    
    def __init__(self, name: str, description: str, func: Callable):
        """Initialize with LangChain-compatible interface."""
        self.name = name
        self.description = description
        self.func = func
        self._tool = DirectTool(name, func, description)
    
    def run(self, tool_input: str) -> str:
        """Run the tool (LangChain compatibility)."""
        # Parse input if it's JSON
        try:
            if isinstance(tool_input, str):
                arguments = json.loads(tool_input)
            else:
                arguments = tool_input
        except json.JSONDecodeError:
            arguments = {"input": tool_input}
        
        # Execute tool
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._tool.execute(arguments))
        
        if result.success:
            return str(result.result)
        else:
            raise ToolError(result.error)
    
    async def arun(self, tool_input: str) -> str:
        """Async run the tool (LangChain compatibility)."""
        # Parse input if it's JSON
        try:
            if isinstance(tool_input, str):
                arguments = json.loads(tool_input)
            else:
                arguments = tool_input
        except json.JSONDecodeError:
            arguments = {"input": tool_input}
        
        # Execute tool
        result = await self._tool.execute(arguments)
        
        if result.success:
            return str(result.result)
        else:
            raise ToolError(result.error)


class Tool(BaseTool):
    """LangChain Tool compatibility class."""
    
    def __init__(self, name: str, description: str, func: Callable, **kwargs):
        """Initialize with LangChain Tool interface."""
        super().__init__(name, description, func)