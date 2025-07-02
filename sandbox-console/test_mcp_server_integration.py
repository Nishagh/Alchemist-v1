#!/usr/bin/env python3
"""
Test MCP Server Integration for Agent 9cb4e76c-28bf-45d6-a7c0-e67607675457

This script tests the MCP server connectivity, tool discovery, and integration
to ensure the agent can properly access and use MCP server tools.
"""
import asyncio
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from mcp_tool import RESTMCPClient, get_mcp_tools_sync
from agent import get_mcp_server

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test agent ID
TEST_AGENT_ID = "9cb4e76c-28bf-45d6-a7c0-e67607675457"

def test_mcp_url_generation():
    """Test MCP server URL generation for the agent."""
    print(f"🔗 Testing MCP Server URL Generation for {TEST_AGENT_ID}")
    print("=" * 70)
    
    try:
        mcp_url = get_mcp_server(TEST_AGENT_ID)
        expected_url = f"https://mcp-{TEST_AGENT_ID}-851487020021.us-central1.run.app"
        
        print(f"Generated URL: {mcp_url}")
        print(f"Expected URL:  {expected_url}")
        print(f"URL Match: {'✅' if mcp_url == expected_url else '❌'}")
        
        return mcp_url
    except Exception as e:
        print(f"❌ Error generating MCP URL: {e}")
        return None

def test_mcp_server_connectivity(mcp_url: str):
    """Test basic connectivity to MCP server."""
    print(f"\\n🔗 Testing MCP Server Connectivity")
    print("=" * 70)
    print(f"Testing URL: {mcp_url}")
    
    # Test different endpoints
    endpoints_to_test = [
        ("/health", "Health Check"),
        ("/", "Root Endpoint"),
        ("/tools", "Tools Discovery"),
        ("/api/health", "API Health"),
    ]
    
    connectivity_results = {}
    
    for endpoint, description in endpoints_to_test:
        try:
            print(f"\\nTesting {description} ({endpoint}):")
            response = requests.get(f"{mcp_url}{endpoint}", timeout=10)
            
            print(f"   Status: {response.status_code}")
            connectivity_results[endpoint] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_size': len(response.content)
            }
            
            if response.status_code == 200:
                print(f"   ✅ Success")
                try:
                    data = response.json()
                    if 'agent_id' in data:
                        print(f"   Agent ID: {data['agent_id']}")
                    if 'service' in data:
                        print(f"   Service: {data['service']}")
                    if 'tools' in data:
                        print(f"   Tools Count: {len(data['tools'])}")
                except:
                    print(f"   Response size: {len(response.content)} bytes")
            else:
                print(f"   ❌ Failed")
                if response.text:
                    print(f"   Error: {response.text[:100]}")
                    
        except requests.exceptions.ConnectTimeout:
            print(f"   ❌ Connection timeout")
            connectivity_results[endpoint] = {'status_code': None, 'success': False, 'error': 'timeout'}
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error (server may not be running)")
            connectivity_results[endpoint] = {'status_code': None, 'success': False, 'error': 'connection_error'}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            connectivity_results[endpoint] = {'status_code': None, 'success': False, 'error': str(e)}
    
    return connectivity_results

async def test_mcp_client_async(mcp_url: str):
    """Test MCP client functionality asynchronously."""
    print(f"\\n🤖 Testing MCP Client Functionality")
    print("=" * 70)
    
    try:
        # Create MCP client
        mcp_client = RESTMCPClient(mcp_url)
        
        # Test health check
        print("Testing health check...")
        health_ok = await mcp_client.check_health()
        print(f"Health Check: {'✅ Passed' if health_ok else '❌ Failed'}")
        
        # Test tool discovery
        print("\\nTesting tool discovery...")
        tools = await mcp_client.discover_tools()
        print(f"Tools Discovered: {len(tools)}")
        
        tool_details = []
        for i, tool in enumerate(tools):
            tool_name = tool.get('name', 'Unknown')
            tool_desc = tool.get('description', 'No description')
            tool_args = tool.get('args', [])
            
            print(f"   {i+1}. {tool_name}")
            print(f"      Description: {tool_desc}")
            print(f"      Arguments: {len(tool_args)}")
            
            # Show argument details
            for arg in tool_args[:3]:  # Show first 3 args
                arg_name = arg.get('name', 'unnamed')
                arg_type = arg.get('type', 'unknown')
                arg_required = arg.get('required', False)
                print(f"         - {arg_name} ({arg_type}) {'[required]' if arg_required else '[optional]'}")
            
            if len(tool_args) > 3:
                print(f"         ... and {len(tool_args) - 3} more arguments")
            
            tool_details.append({
                'name': tool_name,
                'description': tool_desc,
                'args_count': len(tool_args),
                'args': tool_args
            })
        
        return {
            'health_ok': health_ok,
            'tools_count': len(tools),
            'tools': tool_details
        }
        
    except Exception as e:
        print(f"❌ MCP Client Error: {e}")
        return {
            'health_ok': False,
            'tools_count': 0,
            'tools': [],
            'error': str(e)
        }

def test_mcp_langchain_integration(mcp_url: str):
    """Test MCP integration with LangChain tools."""
    print(f"\\n🛠️  Testing MCP LangChain Integration")
    print("=" * 70)
    
    try:
        # Get MCP tools for LangChain
        print("Creating LangChain tools from MCP server...")
        mcp_tools = get_mcp_tools_sync(mcp_url)
        
        print(f"LangChain Tools Created: {len(mcp_tools)}")
        
        tool_results = []
        for tool in mcp_tools:
            print(f"\\n✅ Tool: {tool.name}")
            print(f"   Description: {tool.description}")
            
            tool_info = {
                'name': tool.name,
                'description': tool.description,
                'test_result': None
            }
            
            # Try to test the tool with appropriate test data
            try:
                # Determine appropriate test input based on tool name
                test_input = None
                if 'balance' in tool.name.lower():
                    test_input = "12345"  # Account number
                elif 'transfer' in tool.name.lower():
                    test_input = {"from_account": "12345", "to_account": "67890", "amount": "100"}
                elif 'transaction' in tool.name.lower():
                    test_input = "12345"  # Account number
                elif 'customer' in tool.name.lower():
                    test_input = "customer123"  # Customer ID
                else:
                    # Generic test input
                    test_input = "test_input"
                
                print(f"   Testing with input: {test_input}")
                
                # Execute tool
                if isinstance(test_input, dict):
                    result = tool.func(**test_input)
                else:
                    result = tool.func(test_input)
                
                if result and "Error" not in result:
                    print(f"   ✅ Tool execution successful")
                    print(f"   Result preview: {str(result)[:100]}...")
                    tool_info['test_result'] = 'success'
                else:
                    print(f"   ⚠️  Tool returned error or empty result")
                    print(f"   Result: {str(result)[:150] if result else 'No result'}")
                    tool_info['test_result'] = 'error'
                    
            except Exception as e:
                print(f"   ❌ Tool execution failed: {e}")
                tool_info['test_result'] = 'failed'
            
            tool_results.append(tool_info)
        
        return {
            'tools_count': len(mcp_tools),
            'tools': tool_results
        }
        
    except Exception as e:
        print(f"❌ LangChain integration error: {e}")
        return {
            'tools_count': 0,
            'tools': [],
            'error': str(e)
        }

def generate_mcp_report(url, connectivity_results, async_results, langchain_results):
    """Generate comprehensive MCP server integration report."""
    print(f"\\n📊 MCP Server Integration Report for Agent {TEST_AGENT_ID}")
    print("=" * 80)
    
    print(f"\\n🌐 SERVER INFORMATION:")
    print(f"   URL: {url}")
    
    # Connectivity Analysis
    print(f"\\n🔗 CONNECTIVITY RESULTS:")
    working_endpoints = sum(1 for result in connectivity_results.values() if result.get('success', False))
    total_endpoints = len(connectivity_results)
    print(f"   Working Endpoints: {working_endpoints}/{total_endpoints}")
    
    for endpoint, result in connectivity_results.items():
        status = result.get('status_code', 'N/A')
        success = result.get('success', False)
        print(f"   {endpoint}: {'✅' if success else '❌'} (Status: {status})")
    
    # Async Client Results
    print(f"\\n🤖 MCP CLIENT FUNCTIONALITY:")
    if 'error' in async_results:
        print(f"   Status: ❌ Failed ({async_results['error']})")
    else:
        health_ok = async_results.get('health_ok', False)
        tools_count = async_results.get('tools_count', 0)
        print(f"   Health Check: {'✅ Passed' if health_ok else '❌ Failed'}")
        print(f"   Tools Discovered: {tools_count}")
        
        if tools_count > 0:
            tools = async_results.get('tools', [])
            for tool in tools[:3]:  # Show first 3 tools
                print(f"     - {tool['name']} ({tool['args_count']} args)")
            if len(tools) > 3:
                print(f"     ... and {len(tools) - 3} more tools")
    
    # LangChain Integration
    print(f"\\n🛠️  LANGCHAIN INTEGRATION:")
    if 'error' in langchain_results:
        print(f"   Status: ❌ Failed ({langchain_results['error']})")
    else:
        lc_tools_count = langchain_results.get('tools_count', 0)
        print(f"   LangChain Tools Created: {lc_tools_count}")
        
        if lc_tools_count > 0:
            tools = langchain_results.get('tools', [])
            successful_tests = sum(1 for tool in tools if tool.get('test_result') == 'success')
            print(f"   Successful Tool Tests: {successful_tests}/{len(tools)}")
    
    # Overall Assessment
    print(f"\\n🎯 OVERALL ASSESSMENT:")
    score = 0
    max_score = 4
    
    if working_endpoints > 0:
        score += 1
        print("   ✅ Server is accessible")
    else:
        print("   ❌ Server is not accessible")
    
    if async_results.get('health_ok', False):
        score += 1
        print("   ✅ Health check working")
    else:
        print("   ❌ Health check failed")
    
    if async_results.get('tools_count', 0) > 0:
        score += 1
        print("   ✅ Tools discovery working")
    else:
        print("   ❌ No tools discovered")
    
    if langchain_results.get('tools_count', 0) > 0:
        score += 1
        print("   ✅ LangChain integration working")
    else:
        print("   ❌ LangChain integration failed")
    
    print(f"\\n   SCORE: {score}/{max_score} ({score/max_score*100:.0f}%)")
    
    if score == max_score:
        print("   🎉 EXCELLENT: MCP server fully operational!")
    elif score >= 3:
        print("   ✅ GOOD: MCP server mostly working with minor issues")
    elif score >= 2:
        print("   ⚠️  PARTIAL: MCP server partially working, needs attention")
    else:
        print("   ❌ CRITICAL: MCP server not functioning properly")

async def run_async_tests(mcp_url: str):
    """Run async tests for MCP server."""
    return await test_mcp_client_async(mcp_url)

def main():
    """Run all MCP server tests."""
    print(f"🧪 Testing MCP Server Integration for Agent: {TEST_AGENT_ID}")
    print("=" * 80)
    
    # Test URL generation
    mcp_url = test_mcp_url_generation()
    
    if not mcp_url:
        print("❌ Cannot proceed without MCP URL")
        return
    
    # Test connectivity
    connectivity_results = test_mcp_server_connectivity(mcp_url)
    
    # Test async functionality
    async_results = asyncio.run(run_async_tests(mcp_url))
    
    # Test LangChain integration
    langchain_results = test_mcp_langchain_integration(mcp_url)
    
    # Generate report
    generate_mcp_report(mcp_url, connectivity_results, async_results, langchain_results)

if __name__ == "__main__":
    main()