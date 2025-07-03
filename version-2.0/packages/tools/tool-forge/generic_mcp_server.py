#!/usr/bin/env python3
"""
Higress MCP Server
A flexible MCP server that can ingest any YAML configuration and dynamically
create MCP tools for AI agents to interact with various APIs.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import yaml
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR
)
from pydantic import BaseModel, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp-server")

class SecurityScheme(BaseModel):
    """Security scheme configuration"""
    id: str
    type: str  # http, apiKey
    scheme: Optional[str] = None  # basic, bearer
    name: Optional[str] = None  # header name for apiKey
    in_: Optional[str] = None  # header, query for apiKey
    defaultCredential: Optional[str] = None

class ToolArg(BaseModel):
    """Tool argument configuration"""
    name: str
    description: str
    type: str = "string"
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    position: Optional[str] = None  # query, path, header, cookie, body

class RequestTemplate(BaseModel):
    """HTTP request template configuration"""
    url: str
    method: str = "GET"
    headers: Optional[List[Dict[str, str]]] = None
    security: Optional[Dict[str, Any]] = None

class ResponseTemplate(BaseModel):
    """Response template configuration"""
    body: Optional[str] = None
    prependBody: Optional[str] = None
    appendBody: Optional[str] = None

class MCPTool(BaseModel):
    """MCP Tool configuration"""
    name: str
    description: str
    args: List[ToolArg] = []
    requestTemplate: RequestTemplate
    responseTemplate: Optional[ResponseTemplate] = None

class MCPServerConfig(BaseModel):
    """Complete MCP server configuration"""
    server: Dict[str, Any]
    tools: List[MCPTool] = []

class MCPServer:
    """MCP Server that dynamically creates tools from YAML configuration"""
    
    def __init__(self, config_path: Optional[str] = None, config_content: Optional[str] = None):
        self.server = Server("mcp-server")
        self.config: Optional[MCPServerConfig] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Load configuration
        if config_path:
            self.load_config_from_file(config_path)
        elif config_content:
            self.load_config_from_content(config_content)
        else:
            raise ValueError("Either config_path or config_content must be provided")
        
        self.setup_handlers()
    
    def load_config_from_file(self, config_path: str):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            self.config = MCPServerConfig(**config_data)
            logger.info(f"✅ Loaded configuration from {config_path}")
            logger.info(f"📊 Found {len(self.config.tools)} tools to register")
        except Exception as e:
            logger.error(f"❌ Failed to load config from {config_path}: {e}")
            raise
    
    def load_config_from_content(self, config_content: str):
        """Load configuration from YAML content string"""
        try:
            config_data = yaml.safe_load(config_content)
            self.config = MCPServerConfig(**config_data)
            logger.info("✅ Loaded configuration from content")
            logger.info(f"📊 Found {len(self.config.tools)} tools to register")
        except Exception as e:
            logger.error(f"❌ Failed to load config from content: {e}")
            raise
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Return list of available tools"""
            tools = []
            
            for tool_config in self.config.tools:
                # Convert tool arguments to MCP tool properties
                properties = {}
                required = []
                
                for arg in tool_config.args:
                    prop_def = {
                        "type": arg.type,
                        "description": arg.description
                    }
                    
                    if arg.enum:
                        prop_def["enum"] = arg.enum
                    
                    if arg.default is not None:
                        prop_def["default"] = arg.default
                    
                    properties[arg.name] = prop_def
                    
                    if arg.required:
                        required.append(arg.name)
                
                # Create MCP tool
                tool = Tool(
                    name=tool_config.name,
                    description=tool_config.description,
                    inputSchema={
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                )
                tools.append(tool)
            
            logger.info(f"📋 Returning {len(tools)} available tools")
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool execution"""
            tool_name = request.name
            arguments = request.arguments or {}
            
            logger.info(f"🔧 Executing tool: {tool_name} with args: {arguments}")
            
            # Find the tool configuration
            tool_config = None
            for tool in self.config.tools:
                if tool.name == tool_name:
                    tool_config = tool
                    break
            
            if not tool_config:
                logger.error(f"❌ Tool not found: {tool_name}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: Tool '{tool_name}' not found")],
                    isError=True
                )
            
            try:
                # Execute the tool
                result = await self.execute_tool(tool_config, arguments)
                return CallToolResult(
                    content=[TextContent(type="text", text=result)]
                )
            except Exception as e:
                error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                logger.error(f"❌ {error_msg}")
                logger.error(traceback.format_exc())
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )
    
    async def execute_tool(self, tool_config: MCPTool, arguments: Dict[str, Any]) -> str:
        """Execute a tool with the given arguments"""
        # Prepare the HTTP request
        url = self.build_url(tool_config.requestTemplate.url, arguments)
        method = tool_config.requestTemplate.method.upper()
        headers = self.build_headers(tool_config.requestTemplate.headers, arguments)
        
        # Handle request body based on argument positions
        body = None
        params = {}
        
        # Process arguments based on their positions
        for arg in tool_config.args:
            arg_value = arguments.get(arg.name)
            if arg_value is None and arg.default is not None:
                arg_value = arg.default
            
            if arg_value is None:
                continue
            
            position = arg.position or "query"
            
            if position == "path":
                # Path parameters are already handled in build_url
                continue
            elif position == "query":
                params[arg.name] = arg_value
            elif position == "header":
                headers[arg.name] = str(arg_value)
            elif position == "body":
                if body is None:
                    body = {}
                body[arg.name] = arg_value
        
        # Convert body to JSON if needed
        if body and method in ["POST", "PUT", "PATCH"]:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body)
        
        # Apply security if configured
        headers = self.apply_security(headers, tool_config.requestTemplate.security)
        
        # Make the HTTP request
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            logger.info(f"🌐 Making {method} request to {url}")
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=body,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                
                # Check if request was successful
                if response.status >= 400:
                    error_msg = f"HTTP {response.status}: {response_text}"
                    logger.error(f"❌ API request failed: {error_msg}")
                    return f"API Error: {error_msg}"
                
                # Apply response template if configured
                if tool_config.responseTemplate:
                    return self.format_response(response_text, tool_config.responseTemplate)
                else:
                    return response_text
        
        except Exception as e:
            logger.error(f"❌ Request failed: {str(e)}")
            raise
    
    def build_url(self, url_template: str, arguments: Dict[str, Any]) -> str:
        """Build URL with path parameters replaced"""
        url = url_template
        
        # Replace path parameters
        for key, value in arguments.items():
            placeholder = f"{{{key}}}"
            if placeholder in url:
                url = url.replace(placeholder, str(value))
        
        return url
    
    def build_headers(self, header_templates: Optional[List[Dict[str, str]]], arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "User-Agent": "MCP-Server/1.0",
            "Accept": "application/json"
        }
        
        if header_templates:
            for header_template in header_templates:
                key = header_template.get("key", "")
                value_template = header_template.get("value", "")
                
                # Simple template replacement
                value = value_template
                for arg_name, arg_value in arguments.items():
                    placeholder = f"{{{{.args.{arg_name}}}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(arg_value))
                
                # Handle config placeholders
                if "{{.config." in value:
                    # Extract config values from environment or server config
                    server_config = self.config.server.get("config", {})
                    for config_key, config_value in server_config.items():
                        placeholder = f"{{{{.config.{config_key}}}}}"
                        if placeholder in value:
                            # Try environment variable first
                            env_value = os.getenv(config_key.upper())
                            actual_value = env_value if env_value else str(config_value)
                            value = value.replace(placeholder, actual_value)
                
                headers[key] = value
        
        return headers
    
    def apply_security(self, headers: Dict[str, str], security_config: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Apply security configuration to headers"""
        if not security_config:
            return headers
        
        security_id = security_config.get("id")
        if not security_id:
            return headers
        
        # Find security scheme
        security_schemes = self.config.server.get("securitySchemes", [])
        scheme = None
        for s in security_schemes:
            if s.get("id") == security_id:
                scheme = s
                break
        
        if not scheme:
            logger.warning(f"⚠️ Security scheme '{security_id}' not found")
            return headers
        
        # Apply security based on type
        credential = security_config.get("credential") or scheme.get("defaultCredential")
        if not credential:
            # Try to get from environment
            credential = os.getenv(f"{security_id.upper()}_CREDENTIAL")
        
        if not credential:
            logger.warning(f"⚠️ No credential found for security scheme '{security_id}'")
            return headers
        
        scheme_type = scheme.get("type")
        if scheme_type == "http":
            scheme_name = scheme.get("scheme")
            if scheme_name == "bearer":
                headers["Authorization"] = f"Bearer {credential}"
            elif scheme_name == "basic":
                headers["Authorization"] = f"Basic {credential}"
        elif scheme_type == "apiKey":
            location = scheme.get("in")
            name = scheme.get("name")
            if location == "header" and name:
                headers[name] = credential
        
        return headers
    
    def format_response(self, response_text: str, response_template: ResponseTemplate) -> str:
        """Format response using template"""
        if response_template.body:
            # Custom body template (would need template engine for full support)
            return response_template.body
        
        result = ""
        
        if response_template.prependBody:
            result += response_template.prependBody + "\n\n"
        
        result += response_text
        
        if response_template.appendBody:
            result += "\n\n" + response_template.appendBody
        
        return result
    
    async def run(self):
        """Run the MCP server"""
        logger.info(f"🚀 Starting MCP Server")
        logger.info(f"📊 Server: {self.config.server.get('name', 'Unknown')}")
        logger.info(f"🔧 Tools available: {len(self.config.tools)}")
        
        # List available tools for debugging
        for tool in self.config.tools:
            logger.info(f"  • {tool.name}: {tool.description}")
        
        async with stdio_server() as streams:
            await self.server.run(
                streams[0], streams[1], InitializationOptions(
                    server_name="mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities()
                )
            )
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()