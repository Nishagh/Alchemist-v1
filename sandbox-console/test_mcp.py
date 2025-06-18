#!/usr/bin/env python3
"""
Test script for MCP integration

This script tests the connection to the MCP server and lists available tools.
"""
import asyncio
import logging
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_rest_mcp_connection():
    """Test REST-based MCP server connection and tool listing."""
    base_url = "https://mcp-server-8e749a5b-91a3-4354-afdf-dc1d157e89fd-851487020021.us-central1.run.app"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health check
            logger.info(f"🏥 Testing health check: {base_url}/health")
            health_response = await client.get(f"{base_url}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                logger.info(f"✅ Server is healthy! Agent ID: {health_data.get('agent_id')}")
            else:
                logger.error(f"❌ Health check failed with status: {health_response.status_code}")
                return
            
            # Test tools endpoint
            logger.info(f"🛠️ Testing tools endpoint: {base_url}/tools")
            tools_response = await client.get(f"{base_url}/tools")
            
            if tools_response.status_code == 200:
                tools_data = tools_response.json()
                tools = tools_data.get('tools', [])
                logger.info(f"✅ Successfully connected! Found {len(tools)} tools:")
                
                for tool in tools:
                    logger.info(f"  📋 Tool: {tool['name']} - {tool['description']}")
                    args_count = len(tool.get('args', []))
                    if args_count > 0:
                        logger.info(f"       Args: {args_count} parameters")
                
                # Test API info endpoint
                logger.info(f"📝 Testing API info endpoint: {base_url}/api-info")
                try:
                    api_response = await client.get(f"{base_url}/api-info")
                    if api_response.status_code == 200:
                        logger.info("✅ API info endpoint available")
                    else:
                        logger.info("ℹ️ API info endpoint not available (this is okay)")
                except Exception as e:
                    logger.info("ℹ️ API info endpoint not available (this is okay)")
                
                return True
                
            else:
                logger.error(f"❌ Tools endpoint failed with status: {tools_response.status_code}")
                logger.error(f"Response: {tools_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False


async def test_tool_execution():
    """Test executing a simple tool to verify the server works end-to-end."""
    base_url = "https://mcp-server-8e749a5b-91a3-4354-afdf-dc1d157e89fd-851487020021.us-central1.run.app"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test a simple tool call - get all customers
            logger.info("🧪 Testing tool execution: getAllCustomers")
            
            # For REST APIs, we might need to call the actual endpoint
            # Let's try a few patterns to see how to execute tools
            possible_patterns = [
                f"{base_url}/getAllCustomers",
                f"{base_url}/api/getAllCustomers", 
                f"{base_url}/customers",
                f"{base_url}/execute/getAllCustomers"
            ]
            
            for pattern in possible_patterns:
                try:
                    logger.info(f"   Trying: {pattern}")
                    response = await client.get(pattern)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ Tool execution successful! Response: {json.dumps(data, indent=2)[:200]}...")
                        return True
                    elif response.status_code != 404:
                        logger.info(f"   Status {response.status_code}: {response.text[:100]}")
                except Exception as e:
                    logger.info(f"   Failed: {str(e)[:50]}")
                    
            logger.info("ℹ️ Tool execution patterns not found - this might require specific implementation")
            return False
            
        except Exception as e:
            logger.error(f"❌ Tool execution test failed: {str(e)}")
            return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting MCP server tests...")
    
    # Test basic connection
    connection_success = await test_rest_mcp_connection()
    
    if connection_success:
        # Test tool execution
        await test_tool_execution()
        logger.info("🎉 MCP server test completed!")
    else:
        logger.error("❌ Connection test failed - skipping tool execution test")


if __name__ == "__main__":
    asyncio.run(main()) 