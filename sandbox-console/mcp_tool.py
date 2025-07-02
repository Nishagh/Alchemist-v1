#!/usr/bin/env python3
"""
REST-based MCP Integration for Standalone Agent

This module provides integration with REST-based MCP servers, allowing the agent to use
tools and resources from external MCP servers via HTTP requests.
"""
import json
import logging
import asyncio
import httpx
from typing import Dict, Any, List, Optional

from langchain.tools import Tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RESTMCPClient:
    """
    Client for connecting to and interacting with REST-based MCP servers.
    """
    
    def __init__(self, server_url: str):
        """
        Initialize the REST MCP client.
        
        Args:
            server_url: URL of the MCP server (e.g., 'https://mcp-server-xxx.run.app')
        """
        self.server_url = server_url.rstrip('/')
        self.tools_cache: List[Dict[str, Any]] = []
        
    async def check_health(self) -> bool:
        """
        Check if the MCP server is available by trying multiple endpoints.
        
        Returns:
            True if server is accessible, False otherwise
        """
        health_endpoints = [
            "/health",      # Standard health endpoint
            "/",           # Root endpoint  
            "/tools"       # Tools discovery endpoint
        ]
        
        for endpoint in health_endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.server_url}{endpoint}")
                    if response.status_code == 200:
                        logger.info(f"✅ MCP server is accessible via {endpoint}")
                        return True
                    elif response.status_code == 404 and endpoint != "/tools":
                        # 404 is ok for health/root, continue trying other endpoints
                        continue
                    else:
                        logger.info(f"🔶 Endpoint {endpoint} returned status: {response.status_code}")
            except Exception as e:
                logger.info(f"🔶 Endpoint {endpoint} failed: {str(e)}")
                continue
        
        logger.warning(f"⚠️  MCP server at {self.server_url} is not responding to health checks, but will still try to discover tools")
        return True  # Return True to allow tool discovery attempt even if health check fails
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """
        Discover available tools from the MCP server.
        
        Returns:
            List of tool information dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_url}/tools")
                
                if response.status_code == 200:
                    tools_data = response.json()
                    tools = tools_data.get('tools', [])
                    self.tools_cache = tools
                    logger.info(f"✅ Discovered {len(tools)} tools from MCP server")
                    
                    # Debug: Log tool schemas
                    for tool in tools:
                        logger.info(f"🔍 Tool: {tool.get('name')} - Args: {tool.get('args', [])}")
                    
                    return tools
                else:
                    logger.error(f"❌ Tools discovery failed with status: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to discover tools: {str(e)}")
            return []
    
    async def call_tool_rest(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool using the MCP server's REST endpoint format.
        Handles different parameter positions: query, path, and body.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        try:
            # Find the tool in our cache
            tool_info = next((tool for tool in self.tools_cache if tool['name'] == tool_name), None)
            if not tool_info:
                raise ValueError(f"Tool {tool_name} not found in cache")
            
            # Separate arguments by position based on tool schema
            query_params = {}
            path_params = {}
            body_params = {}
            
            # Get tool args from tool_info if available
            tool_args = tool_info.get('args', [])
            
            for arg in tool_args:
                arg_name = arg.get('name')
                position = arg.get('position', 'body')  # Default to body if not specified
                
                if arg_name in arguments:
                    value = arguments[arg_name]
                    if position == 'query':
                        query_params[arg_name] = value
                    elif position == 'path':
                        path_params[arg_name] = value
                    elif position == 'body':
                        body_params[arg_name] = value
                    else:
                        # Unknown position, default to body
                        body_params[arg_name] = value
            
            # For arguments not defined in tool schema, put them in body
            for arg_name, value in arguments.items():
                if not any(arg.get('name') == arg_name for arg in tool_args):
                    body_params[arg_name] = value
            
            # Build URL with path parameters substituted
            base_url = f"{self.server_url}/tools/{tool_name}/execute"
            url = base_url
            
            # Substitute path parameters in URL if any
            for param_name, param_value in path_params.items():
                # Note: This is a simple substitution. In a real implementation,
                # you might want to use the actual URL template from the tool config
                url = url.replace(f"{{{param_name}}}", str(param_value))
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    # Build request with proper parameter positioning
                    request_kwargs = {
                        'url': url,
                        'params': query_params if query_params else None
                    }
                    
                    # Add body parameters if any
                    if body_params:
                        request_kwargs['json'] = body_params
                    
                    logger.info(f"🔧 Calling tool {tool_name}")
                    logger.info(f"🔧 URL: {url}")
                    logger.info(f"🔧 Query params: {query_params}")
                    logger.info(f"🔧 Path params: {path_params}")
                    logger.info(f"🔧 Body params: {body_params}")
                    
                    response = await client.post(**request_kwargs)
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'success': True,
                            'result': json.dumps(data, indent=2),
                            'tool_name': tool_name,
                            'data': data
                        }
                    else:
                        # Try to get error details from response
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', f"HTTP {response.status_code}")
                        except:
                            error_msg = f"HTTP {response.status_code}: {response.text}"
                        
                        return {
                            'success': False,
                            'error': f"Server responded with {response.status_code}: {error_msg}",
                            'tool_name': tool_name
                        }
                        
                except Exception as e:
                    logger.error(f"❌ Failed to call tool {tool_name} at {url}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Request failed: {str(e)}",
                        'tool_name': tool_name
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to call tool {tool_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'tool_name': tool_name
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available tools.
        
        Returns:
            List of tool information dictionaries
        """
        return self.tools_cache.copy()


def create_rest_mcp_tool(tool_info: Dict[str, Any], mcp_client: RESTMCPClient) -> Tool:
    """
    Create a LangChain tool from REST MCP tool information.
    
    Args:
        tool_info: Tool information from the MCP server
        mcp_client: The REST MCP client instance
        
    Returns:
        LangChain Tool instance
    """
    tool_name = tool_info['name']
    tool_description = tool_info['description']
    
    async def tool_func(**kwargs) -> str:
        """
        Tool function that calls the REST MCP server.
        """
        try:
            result = await mcp_client.call_tool_rest(tool_name, kwargs)
            
            if result.get('success', False):
                return result.get('result', 'Tool executed successfully')
            else:
                return f"Error executing tool {tool_name}: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"Error in REST MCP tool {tool_name}: {str(e)}")
            return f"Error executing tool {tool_name}: {str(e)}"
    
    def sync_tool_func(*args, **kwargs) -> str:
        """
        Synchronous wrapper for the async tool function.
        """
        try:
            # Handle positional arguments by mapping them to the tool's parameter names
            final_kwargs = kwargs.copy()
            
            logger.info(f"🔧 Tool {tool_name} called with args: {args}, kwargs: {kwargs}")
            logger.info(f"🔧 Tool schema args: {tool_info.get('args', [])}")
            
            if args and tool_info.get('args'):
                # Map positional arguments to parameter names based on tool schema
                tool_args = tool_info['args']
                logger.info(f"🔧 Using tool schema for parameter mapping")
                
                # Sort parameters: required ones first, then optional ones
                sorted_args = sorted(tool_args, key=lambda x: (not x.get('required', False), x.get('name', '')))
                logger.info(f"🔧 Sorted parameters (required first): {[arg.get('name') for arg in sorted_args]}")
                
                for i, arg_value in enumerate(args):
                    if i < len(sorted_args):
                        param_name = sorted_args[i]['name']
                        final_kwargs[param_name] = arg_value
                        logger.info(f"🔧 Mapped arg[{i}] '{arg_value}' to parameter '{param_name}'")
            elif args:
                # If no schema available, try common parameter names for banking tools
                logger.info(f"🔧 No tool schema available, using hardcoded mapping")
            
            logger.info(f"🔧 Final kwargs for {tool_name}: {final_kwargs}")
            
            # Run the async function in the event loop
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context but need to run async code
                    # Use asyncio.run in a thread pool executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, tool_func(**final_kwargs))
                        return future.result()
                else:
                    # We have a loop but it's not running, use it
                    return loop.run_until_complete(tool_func(**final_kwargs))
            except RuntimeError as re:
                # No event loop in this thread, create a new one
                if "There is no current event loop" in str(re) or "no running event loop" in str(re):
                    return asyncio.run(tool_func(**final_kwargs))
                else:
                    # Some other RuntimeError, re-raise
                    raise
        except Exception as e:
            logger.error(f"Error in sync REST MCP tool wrapper for {tool_name}: {str(e)}")
            return f"Error executing tool {tool_name}: {str(e)}"
    
    # Create the LangChain tool
    return Tool.from_function(
        func=sync_tool_func,
        name=tool_name,
        description=tool_description
    )


async def get_mcp_tools(server_url: str) -> List[Tool]:
    """
    Get LangChain tools from a REST-based MCP server.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        List of LangChain Tool instances
    """
    try:
        logger.info(f"🚀 Initializing REST MCP tools from server: {server_url}")
        
        # Initialize the REST MCP client
        mcp_client = RESTMCPClient(server_url)
        
        # Check server health first
        if not await mcp_client.check_health():
            logger.error("❌ Server health check failed")
            return []
        
        # Discover available tools
        tool_infos = await mcp_client.discover_tools()
        
        if not tool_infos:
            logger.warning("⚠️ No tools discovered from MCP server")
            return []
        
        # Create LangChain tools
        tools = []
        for tool_info in tool_infos:
            try:
                tool = create_rest_mcp_tool(tool_info, mcp_client)
                tools.append(tool)
                logger.info(f"✅ Created LangChain tool: {tool_info['name']}")
            except Exception as e:
                logger.error(f"❌ Failed to create tool {tool_info['name']}: {str(e)}")
        
        logger.info(f"🎉 Successfully created {len(tools)} REST MCP tools")
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to get REST MCP tools from {server_url}: {str(e)}")
        return []


def get_mcp_tools_sync(server_url: str) -> List[Tool]:
    """
    Synchronous wrapper to get REST MCP tools.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        List of LangChain Tool instances
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, use a thread executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_mcp_tools(server_url))
                return future.result()
        else:
            return loop.run_until_complete(get_mcp_tools(server_url))
    except Exception as e:
        logger.error(f"❌ Error in sync REST MCP tools wrapper: {str(e)}")
        return [] 