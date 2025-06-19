#!/usr/bin/env python3
"""
Interactive Test Script for Universal Agent
==========================================

This script allows you to test the Universal Agent functionality by:
- Sending user queries and getting responses
- Testing streaming responses
- Monitoring token usage
- Testing banking tools via MCP
- Testing knowledge base search
- Viewing conversation history

Usage:
    python3 test_agent_interactive.py

Commands:
    /help - Show available commands
    /stream - Toggle streaming mode
    /tokens - Show token usage
    /tools - List available tools
    /bank - Test banking tools
    /search <query> - Search knowledge base
    /history - Show conversation history
    /stats - Show conversation stats
    /quit - Exit the script
"""

import os
import asyncio
import json
import sys
from typing import Optional
from datetime import datetime

# Set the agent ID
AGENT_ID = "8e749a5b-91a3-4354-afdf-dc1d157e89fd"
os.environ['AGENT_ID'] = AGENT_ID

# Import the Universal Agent components
import main as agent_main
from main import initialize_agent

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class UniversalAgentTester:
    """Interactive tester for Universal Agent"""
    
    def __init__(self):
        self.conversation_id = f"test-session-{int(datetime.now().timestamp())}"
        self.streaming_mode = False
        self.agent_initialized = False
        
    async def initialize(self):
        """Initialize the Universal Agent"""
        try:
            print(f"{Colors.CYAN}🚀 Initializing Universal Agent...{Colors.ENDC}")
            await initialize_agent()
            
            if agent_main.llm_service and agent_main.conversation_manager and agent_main.tool_registry:
                self.agent_initialized = True
                print(f"{Colors.GREEN}✅ Agent initialized successfully!{Colors.ENDC}")
                print(f"{Colors.BLUE}   Agent: {agent_main.AGENT_CONFIG.get('name', 'Unknown')}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Model: {agent_main.llm_service.model}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Tools: {len(agent_main.tool_registry.list_tools())}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Conversation ID: {self.conversation_id}{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.RED}❌ Agent initialization failed{Colors.ENDC}")
                return False
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error initializing agent: {e}{Colors.ENDC}")
            return False
    
    def print_help(self):
        """Print available commands"""
        print(f"\n{Colors.HEADER}📋 Available Commands:{Colors.ENDC}")
        print(f"{Colors.CYAN}/help{Colors.ENDC}           - Show this help message")
        print(f"{Colors.CYAN}/stream{Colors.ENDC}         - Toggle streaming mode (currently: {'ON' if self.streaming_mode else 'OFF'})")
        print(f"{Colors.CYAN}/tokens{Colors.ENDC}         - Show current token usage")
        print(f"{Colors.CYAN}/tools{Colors.ENDC}          - List all available tools")
        print(f"{Colors.CYAN}/bank{Colors.ENDC}           - Test banking tools (get customers, accounts, etc.)")
        print(f"{Colors.CYAN}/search <query>{Colors.ENDC} - Search the knowledge base")
        print(f"{Colors.CYAN}/history{Colors.ENDC}        - Show conversation history")
        print(f"{Colors.CYAN}/stats{Colors.ENDC}          - Show conversation statistics")
        print(f"{Colors.CYAN}/quit{Colors.ENDC}           - Exit the test script")
        print(f"\n{Colors.YELLOW}💡 Tip: Just type your question to chat with the agent!{Colors.ENDC}")
        
        # Show example queries
        print(f"\n{Colors.HEADER}💬 Example Queries:{Colors.ENDC}")
        print(f"{Colors.GREEN}• What banking services do you offer?{Colors.ENDC}")
        print(f"{Colors.GREEN}• Show me all customers{Colors.ENDC}")
        print(f"{Colors.GREEN}• What time is it?{Colors.ENDC}")
        print(f"{Colors.GREEN}• Can you help me check account balances?{Colors.ENDC}")
        print(f"{Colors.GREEN}• Search for information about loans{Colors.ENDC}")
    
    async def process_user_message(self, message: str):
        """Process a user message and return the response"""
        try:
            if self.streaming_mode:
                print(f"{Colors.YELLOW}🌊 Streaming response:{Colors.ENDC}")
                response_chunks = []
                
                async for chunk in agent_main.conversation_manager.stream_response(
                    conversation_id=self.conversation_id,
                    message=message
                ):
                    print(chunk, end='', flush=True)
                    response_chunks.append(chunk)
                
                print()  # New line after streaming
                return ''.join(response_chunks)
            else:
                result = await agent_main.conversation_manager.process_message(
                    conversation_id=self.conversation_id,
                    message=message
                )
                
                if result.success:
                    # Show token usage
                    if result.token_usage.total_tokens > 0:
                        print(f"{Colors.BLUE}📊 Tokens: {result.token_usage.total_tokens} " +
                              f"(prompt: {result.token_usage.prompt_tokens}, " +
                              f"completion: {result.token_usage.completion_tokens}){Colors.ENDC}")
                    
                    # Show tools called
                    if result.tool_calls_made:
                        print(f"{Colors.CYAN}🔧 Tools used: {', '.join(result.tool_calls_made)}{Colors.ENDC}")
                    
                    return result.response
                else:
                    return f"{Colors.RED}❌ Error: {result.error}{Colors.ENDC}"
                    
        except Exception as e:
            return f"{Colors.RED}❌ Error processing message: {e}{Colors.ENDC}"
    
    async def show_token_usage(self):
        """Show current token usage"""
        try:
            total_usage = agent_main.llm_service.get_token_usage()
            print(f"\n{Colors.HEADER}📊 Token Usage Summary:{Colors.ENDC}")
            print(f"{Colors.BLUE}   Prompt tokens: {total_usage.prompt_tokens}{Colors.ENDC}")
            print(f"{Colors.BLUE}   Completion tokens: {total_usage.completion_tokens}{Colors.ENDC}")
            print(f"{Colors.GREEN}   Total tokens: {total_usage.total_tokens}{Colors.ENDC}")
            
            # Estimate cost (rough estimate for GPT-4)
            estimated_cost = (total_usage.prompt_tokens * 0.03 + total_usage.completion_tokens * 0.06) / 1000
            print(f"{Colors.YELLOW}   Estimated cost: ~${estimated_cost:.4f}{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting token usage: {e}{Colors.ENDC}")
    
    async def list_tools(self):
        """List all available tools"""
        try:
            tools = agent_main.tool_registry.list_tools()
            print(f"\n{Colors.HEADER}🔧 Available Tools ({len(tools)}):{Colors.ENDC}")
            
            # Categorize tools
            banking_tools = [t for t in tools if t.startswith('get') or t in ['transferFunds', 'healthCheck']]
            search_tools = [t for t in tools if 'search' in t.lower() or 'knowledge' in t.lower()]
            utility_tools = [t for t in tools if t not in banking_tools and t not in search_tools]
            
            if banking_tools:
                print(f"{Colors.CYAN}   Banking Tools:{Colors.ENDC}")
                for tool in banking_tools:
                    print(f"     • {tool}")
            
            if search_tools:
                print(f"{Colors.CYAN}   Knowledge Base Tools:{Colors.ENDC}")
                for tool in search_tools:
                    print(f"     • {tool}")
            
            if utility_tools:
                print(f"{Colors.CYAN}   Utility Tools:{Colors.ENDC}")
                for tool in utility_tools:
                    print(f"     • {tool}")
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Error listing tools: {e}{Colors.ENDC}")
    
    async def test_banking_tools(self):
        """Test banking tools"""
        print(f"\n{Colors.HEADER}🏦 Testing Banking Tools:{Colors.ENDC}")
        
        try:
            # Test getAllCustomers
            if 'getAllCustomers' in agent_main.tool_registry.list_tools():
                print(f"{Colors.CYAN}📋 Getting all customers...{Colors.ENDC}")
                result = await agent_main.tool_registry.execute_tool('getAllCustomers', {})
                
                if result.success:
                    try:
                        data = json.loads(result.result)
                        if isinstance(data, dict) and 'customers' in data:
                            customers = data['customers']
                            print(f"{Colors.GREEN}✅ Found {len(customers)} customers{Colors.ENDC}")
                            
                            # Show first few customers
                            for i, customer in enumerate(customers[:3]):
                                print(f"   {i+1}. {customer.get('name', 'Unknown')} (ID: {customer.get('customer_id', 'Unknown')})")
                            
                            if len(customers) > 3:
                                print(f"   ... and {len(customers) - 3} more customers")
                        else:
                            print(f"{Colors.YELLOW}📝 Raw response: {str(result.result)[:200]}...{Colors.ENDC}")
                    except json.JSONDecodeError:
                        print(f"{Colors.YELLOW}📝 Response: {str(result.result)[:200]}...{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}❌ Failed to get customers: {result.error}{Colors.ENDC}")
            
            # Test getAccountTypes
            if 'getAccountTypes' in agent_main.tool_registry.list_tools():
                print(f"\n{Colors.CYAN}🏦 Getting account types...{Colors.ENDC}")
                result = await agent_main.tool_registry.execute_tool('getAccountTypes', {})
                
                if result.success:
                    try:
                        data = json.loads(result.result)
                        if isinstance(data, dict) and 'account_types' in data:
                            types = data['account_types']
                            print(f"{Colors.GREEN}✅ Available account types:{Colors.ENDC}")
                            for account_type in types:
                                print(f"   • {account_type}")
                        else:
                            print(f"{Colors.YELLOW}📝 Response: {str(result.result)[:100]}...{Colors.ENDC}")
                    except json.JSONDecodeError:
                        print(f"{Colors.YELLOW}📝 Response: {str(result.result)[:100]}...{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error testing banking tools: {e}{Colors.ENDC}")
    
    async def search_knowledge_base(self, query: str):
        """Search the knowledge base"""
        try:
            print(f"{Colors.CYAN}🔍 Searching knowledge base for: '{query}'{Colors.ENDC}")
            
            # Check if search tool is available
            search_tools = [t for t in agent_main.tool_registry.list_tools() if 'search' in t.lower()]
            
            if search_tools:
                search_tool = search_tools[0]  # Use first search tool
                result = await agent_main.tool_registry.execute_tool(search_tool, {'query': query, 'top_k': 3})
                
                if result.success:
                    print(f"{Colors.GREEN}✅ Search results:{Colors.ENDC}")
                    print(f"{result.result}")
                else:
                    print(f"{Colors.RED}❌ Search failed: {result.error}{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}⚠️ No search tools available{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error searching knowledge base: {e}{Colors.ENDC}")
    
    async def show_conversation_history(self):
        """Show conversation history"""
        try:
            stats = agent_main.conversation_manager.get_conversation_stats(self.conversation_id)
            if stats:
                print(f"\n{Colors.HEADER}📚 Conversation History:{Colors.ENDC}")
                print(f"{Colors.BLUE}   Conversation ID: {stats['conversation_id']}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Turn count: {stats['turn_count']}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Message count: {stats['message_count']}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Last activity: {stats['last_activity']}{Colors.ENDC}")
                
                # Get actual messages
                history = agent_main.conversation_manager.get_conversation_history(self.conversation_id, limit=10)
                if history:
                    print(f"\n{Colors.CYAN}Recent messages:{Colors.ENDC}")
                    for i, msg in enumerate(history[-6:]):  # Show last 6 messages
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')[:100]
                        timestamp = msg.get('timestamp', 'unknown')
                        
                        if role == 'user':
                            print(f"   👤 User: {content}...")
                        elif role == 'assistant':
                            print(f"   🤖 Assistant: {content}...")
            else:
                print(f"{Colors.YELLOW}⚠️ No conversation history found{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting conversation history: {e}{Colors.ENDC}")
    
    async def show_conversation_stats(self):
        """Show detailed conversation statistics"""
        try:
            stats = agent_main.conversation_manager.get_conversation_stats(self.conversation_id)
            if stats:
                print(f"\n{Colors.HEADER}📈 Conversation Statistics:{Colors.ENDC}")
                print(f"{Colors.BLUE}   Conversation ID: {stats['conversation_id']}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Turn count: {stats['turn_count']}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Message count: {stats['message_count']}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Created: {stats.get('created_at', 'Unknown')}{Colors.ENDC}")
                print(f"{Colors.BLUE}   Last activity: {stats['last_activity']}{Colors.ENDC}")
                
                # Token usage for this conversation
                if 'total_tokens' in stats:
                    tokens = stats['total_tokens']
                    print(f"{Colors.GREEN}   Conversation tokens: {tokens.get('total_tokens', 0)}{Colors.ENDC}")
                
                # Global token usage
                total_usage = agent_main.llm_service.get_token_usage()
                print(f"{Colors.GREEN}   Session total tokens: {total_usage.total_tokens}{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}⚠️ No conversation stats available{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting conversation stats: {e}{Colors.ENDC}")
    
    async def run_interactive_session(self):
        """Run the interactive testing session"""
        if not await self.initialize():
            return
        
        print(f"\n{Colors.HEADER}🎯 Universal Agent Interactive Tester{Colors.ENDC}")
        print(f"{Colors.GREEN}Type your questions or use commands (type /help for help){Colors.ENDC}")
        print(f"{Colors.YELLOW}Press Ctrl+C or type /quit to exit{Colors.ENDC}\n")
        
        try:
            while True:
                # Get user input
                try:
                    user_input = input(f"{Colors.BOLD}You: {Colors.ENDC}").strip()
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.ENDC}")
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command_parts = user_input[1:].split(' ', 1)
                    command = command_parts[0].lower()
                    args = command_parts[1] if len(command_parts) > 1 else ""
                    
                    if command == 'help':
                        self.print_help()
                    elif command == 'quit' or command == 'exit':
                        print(f"{Colors.YELLOW}👋 Goodbye!{Colors.ENDC}")
                        break
                    elif command == 'stream':
                        self.streaming_mode = not self.streaming_mode
                        mode = "ON" if self.streaming_mode else "OFF"
                        print(f"{Colors.CYAN}🌊 Streaming mode: {mode}{Colors.ENDC}")
                    elif command == 'tokens':
                        await self.show_token_usage()
                    elif command == 'tools':
                        await self.list_tools()
                    elif command == 'bank':
                        await self.test_banking_tools()
                    elif command == 'search':
                        if args:
                            await self.search_knowledge_base(args)
                        else:
                            print(f"{Colors.RED}❌ Please provide a search query: /search <query>{Colors.ENDC}")
                    elif command == 'history':
                        await self.show_conversation_history()
                    elif command == 'stats':
                        await self.show_conversation_stats()
                    else:
                        print(f"{Colors.RED}❌ Unknown command: {command}. Type /help for available commands.{Colors.ENDC}")
                
                else:
                    # Process as a regular message
                    print(f"{Colors.BOLD}Agent: {Colors.ENDC}", end="")
                    response = await self.process_user_message(user_input)
                    if not self.streaming_mode:
                        print(f"{Colors.GREEN}{response}{Colors.ENDC}")
                    print()  # Add spacing
        
        except Exception as e:
            print(f"{Colors.RED}❌ Unexpected error: {e}{Colors.ENDC}")

async def main():
    """Main function"""
    tester = UniversalAgentTester()
    await tester.run_interactive_session()

if __name__ == "__main__":
    print(f"{Colors.HEADER}🚀 Universal Agent Interactive Tester{Colors.ENDC}")
    print(f"{Colors.BLUE}Testing Agent ID: {AGENT_ID}{Colors.ENDC}")
    print(f"{Colors.CYAN}Starting interactive session...{Colors.ENDC}\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Interrupted by user. Goodbye!{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Fatal error: {e}{Colors.ENDC}")
        sys.exit(1)