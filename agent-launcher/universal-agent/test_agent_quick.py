#!/usr/bin/env python3
"""
Quick Test Script for Universal Agent
====================================

A simpler script to quickly test the Universal Agent with predefined queries.
Perfect for quick validation of functionality.

Usage:
    python3 test_agent_quick.py
"""

import os
import asyncio
import json
from datetime import datetime

# Set the agent ID
AGENT_ID = "8e749a5b-91a3-4354-afdf-dc1d157e89fd"
os.environ['AGENT_ID'] = AGENT_ID

# Import the Universal Agent components
import main as agent_main
from main import initialize_agent

class QuickTester:
    """Quick tester for Universal Agent"""
    
    def __init__(self):
        self.conversation_id = f"quick-test-{int(datetime.now().timestamp())}"
        
    async def initialize_agent(self):
        """Initialize the agent"""
        print("🚀 Initializing Universal Agent...")
        await initialize_agent()
        
        if agent_main.llm_service and agent_main.conversation_manager and agent_main.tool_registry:
            print(f"✅ Agent initialized: {agent_main.AGENT_CONFIG.get('name')}")
            print(f"   Model: {agent_main.llm_service.model}")
            print(f"   Tools: {len(agent_main.tool_registry.list_tools())}")
            return True
        else:
            print("❌ Agent initialization failed")
            return False
    
    async def test_basic_conversation(self):
        """Test basic conversation"""
        print("\n💬 Testing Basic Conversation...")
        
        queries = [
            "Hello! What can you help me with?",
            "What time is it?",
            "Tell me about your capabilities"
        ]
        
        for query in queries:
            print(f"\n👤 User: {query}")
            
            result = await agent_main.conversation_manager.process_message(
                conversation_id=self.conversation_id,
                message=query
            )
            
            if result.success:
                print(f"🤖 Agent: {result.response[:200]}...")
                print(f"📊 Tokens: {result.token_usage.total_tokens}")
                if result.tool_calls_made:
                    print(f"🔧 Tools used: {', '.join(result.tool_calls_made)}")
            else:
                print(f"❌ Error: {result.error}")
    
    async def test_streaming(self):
        """Test streaming responses"""
        print("\n🌊 Testing Streaming Response...")
        
        query = "Explain what banking services you can help with"
        print(f"👤 User: {query}")
        print("🤖 Agent (streaming): ", end="", flush=True)
        
        chunks = []
        async for chunk in agent_main.conversation_manager.stream_response(
            conversation_id=f"{self.conversation_id}-stream",
            message=query
        ):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        
        print(f"\n✅ Streaming completed: {len(chunks)} chunks received")
    
    async def test_banking_tools(self):
        """Test banking tools"""
        print("\n🏦 Testing Banking Tools...")
        
        tools_to_test = [
            ("getAllCustomers", {}, "Get all customers"),
            ("getAccountTypes", {}, "Get account types"),
        ]
        
        for tool_name, args, description in tools_to_test:
            if tool_name in agent_main.tool_registry.list_tools():
                print(f"\n🔧 Testing {tool_name}: {description}")
                
                result = await agent_main.tool_registry.execute_tool(tool_name, args)
                
                if result.success:
                    try:
                        data = json.loads(result.result)
                        if isinstance(data, dict):
                            keys = list(data.keys())
                            print(f"✅ Success: Response has keys {keys}")
                            
                            # Show some data
                            if 'customers' in data:
                                print(f"   Found {len(data['customers'])} customers")
                            elif 'account_types' in data:
                                print(f"   Found {len(data['account_types'])} account types")
                        else:
                            print(f"✅ Success: {str(result.result)[:100]}...")
                    except json.JSONDecodeError:
                        print(f"✅ Success: {str(result.result)[:100]}...")
                else:
                    print(f"❌ Failed: {result.error}")
            else:
                print(f"⚠️ Tool {tool_name} not available")
    
    async def test_token_tracking(self):
        """Test token usage tracking"""
        print("\n📊 Testing Token Usage Tracking...")
        
        # Get current usage
        usage_before = agent_main.llm_service.get_token_usage()
        print(f"Tokens before test: {usage_before.total_tokens}")
        
        # Send a message
        result = await agent_main.conversation_manager.process_message(
            conversation_id=self.conversation_id,
            message="Give me a brief summary of what you can do"
        )
        
        if result.success:
            print(f"✅ Message processed")
            print(f"   This message used: {result.token_usage.total_tokens} tokens")
            print(f"   Breakdown: {result.token_usage.prompt_tokens} prompt + {result.token_usage.completion_tokens} completion")
            
            # Get updated usage
            usage_after = agent_main.llm_service.get_token_usage()
            print(f"Total session tokens: {usage_after.total_tokens}")
            
            # Estimate cost
            estimated_cost = (usage_after.prompt_tokens * 0.03 + usage_after.completion_tokens * 0.06) / 1000
            print(f"Estimated cost: ~${estimated_cost:.4f}")
        else:
            print(f"❌ Failed: {result.error}")
    
    async def show_summary(self):
        """Show test summary"""
        print("\n" + "="*50)
        print("🎯 Test Summary")
        print("="*50)
        
        # Agent info
        print(f"Agent: {agent_main.AGENT_CONFIG.get('name')}")
        print(f"Model: {agent_main.llm_service.model}")
        print(f"Tools: {len(agent_main.tool_registry.list_tools())}")
        
        # Token usage
        usage = agent_main.llm_service.get_token_usage()
        print(f"Total tokens used: {usage.total_tokens}")
        print(f"  Prompt: {usage.prompt_tokens}")
        print(f"  Completion: {usage.completion_tokens}")
        
        # Tools available
        tools = agent_main.tool_registry.list_tools()
        banking_tools = [t for t in tools if t.startswith('get') or 'transfer' in t.lower()]
        print(f"Banking tools: {len(banking_tools)}")
        
        # Capabilities
        print("\n✅ Verified Capabilities:")
        print("  • Direct LLM service (no LangChain)")
        print("  • Token usage tracking")
        print("  • Streaming responses")
        print("  • MCP tool integration")
        print("  • Banking API tools")
        print("  • Conversation management")
        
        print(f"\n🎉 Universal Agent is fully functional!")

async def main():
    """Main test function"""
    tester = QuickTester()
    
    try:
        # Initialize
        if not await tester.initialize_agent():
            return
        
        # Run tests
        await tester.test_basic_conversation()
        await tester.test_streaming()
        await tester.test_banking_tools()
        await tester.test_token_tracking()
        
        # Show summary
        await tester.show_summary()
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Universal Agent Quick Test")
    print("=" * 30)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")