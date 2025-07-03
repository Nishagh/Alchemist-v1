"""
MCP (Model Control Protocol) Service for external tool integration
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx
import json

from services.tool_registry import ToolRegistry
from config.settings import settings

logger = logging.getLogger(__name__)


class MCPService:
    """
    MCP service for connecting to external MCP servers and integrating tools
    """
    
    def __init__(self, agent_id: str, mcp_server_url: str):
        self.agent_id = agent_id
        self.mcp_server_url = mcp_server_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.available_tools = {}
        
        logger.info(f"MCP service initialized for agent {agent_id} with server: {mcp_server_url}")
    
    async def initialize(self):
        """Initialize MCP connection and discover available tools"""
        try:
            # Connect to MCP server
            await self._connect_to_server()
            
            # Discover available tools
            await self._discover_tools()
            
            logger.info(f"MCP service initialized with {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP service: {e}")
            raise
    
    async def _connect_to_server(self):
        """Connect to MCP server"""
        try:
            response = await self.client.post(
                f"{self.mcp_server_url}/api/connect",
                json={
                    "agent_id": self.agent_id,
                    "protocol_version": "1.0"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to connect to MCP server: HTTP {response.status_code}")
            
            connection_data = response.json()
            logger.info(f"Connected to MCP server: {connection_data.get('server_info', {})}")
            
        except Exception as e:
            logger.error(f"MCP server connection error: {e}")
            raise
    
    async def _discover_tools(self):
        """Discover available tools from MCP server"""
        try:
            response = await self.client.get(
                f"{self.mcp_server_url}/tools"
            )
            
            if response.status_code == 200:
                tools_data = response.json()
                tools = tools_data.get('tools', [])
                
                # Handle both list and dict formats
                if isinstance(tools, list):
                    # Convert list to dict using tool name as key
                    self.available_tools = {tool.get('name', f'tool_{i}'): tool for i, tool in enumerate(tools)}
                else:
                    # Already a dict
                    self.available_tools = tools
                    
                logger.info(f"Discovered {len(self.available_tools)} MCP tools")
            else:
                logger.warning(f"Failed to discover tools: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Tool discovery error: {e}")
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool via MCP server
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name not in self.available_tools:
                raise ValueError(f"Tool '{tool_name}' not available")
            
            response = await self.client.post(
                f"{self.mcp_server_url}/api/execute",
                json={
                    "agent_id": self.agent_id,
                    "tool_name": tool_name,
                    "parameters": parameters
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Tool {tool_name} executed successfully")
                return result
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                raise Exception(f"Tool execution failed: {error_data.get('error', f'HTTP {response.status_code}')}")
                
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return {"error": str(e), "success": False}
    
    async def register_tools(self, tool_registry: ToolRegistry):
        """Register MCP tools with the tool registry"""
        try:
            if not self.available_tools:
                await self._discover_tools()
            
            for tool_name, tool_info in self.available_tools.items():
                # Convert MCP tool format to tool registry format
                tool_registry.register_function_tool(
                    name=tool_name,
                    description=tool_info.get('description', f'MCP tool: {tool_name}'),
                    parameters=tool_info.get('parameters', {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }),
                    function=self._create_tool_wrapper(tool_name)
                )
            
            logger.info(f"Registered {len(self.available_tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to register MCP tools: {e}")
    
    def _create_tool_wrapper(self, tool_name: str):
        """Create a wrapper function for MCP tool execution"""
        async def tool_wrapper(**kwargs) -> str:
            try:
                result = await self.execute_tool(tool_name, kwargs)
                
                if result.get('success', True):
                    return result.get('output', str(result))
                else:
                    return f"Tool execution failed: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                logger.error(f"Tool wrapper error for {tool_name}: {e}")
                return f"Error executing tool {tool_name}: {str(e)}"
        
        return tool_wrapper
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        try:
            response = await self.client.get(
                f"{self.mcp_server_url}/api/tools/{tool_name}",
                params={"agent_id": self.agent_id}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get tool info for {tool_name}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting tool info for {tool_name}: {e}")
            return None
    
    async def refresh_tools(self):
        """Refresh the list of available tools"""
        try:
            await self._discover_tools()
            logger.info("MCP tools refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh MCP tools: {e}")
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information"""
        try:
            response = await self.client.get(f"{self.mcp_server_url}/api/info")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to get MCP server info: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if MCP service is healthy"""
        try:
            response = await self.client.get(f"{self.mcp_server_url}/health")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"MCP service health check failed: {e}")
            return False
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get MCP service usage statistics"""
        try:
            response = await self.client.get(
                f"{self.mcp_server_url}/api/stats",
                params={"agent_id": self.agent_id}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to get MCP usage stats: {e}")
            return {"error": str(e)}
    
    async def register_agent_capabilities(self, capabilities: Dict[str, Any]):
        """Register agent capabilities with MCP server"""
        try:
            response = await self.client.post(
                f"{self.mcp_server_url}/api/capabilities",
                json={
                    "agent_id": self.agent_id,
                    "capabilities": capabilities
                }
            )
            
            if response.status_code == 200:
                logger.info("Agent capabilities registered with MCP server")
                return response.json()
            else:
                logger.warning(f"Failed to register capabilities: HTTP {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to register agent capabilities: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close MCP service connection"""
        try:
            # Disconnect from server
            await self.client.post(
                f"{self.mcp_server_url}/api/disconnect",
                json={"agent_id": self.agent_id}
            )
            
            # Close HTTP client
            await self.client.aclose()
            
            logger.info("MCP service connection closed")
            
        except Exception as e:
            logger.error(f"Error closing MCP service: {e}")