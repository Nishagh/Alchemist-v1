#!/usr/bin/env python3
"""
Test script for interacting with a deployed agent

This script allows you to chat with an already deployed agent.
"""

import requests
import json
from typing import Optional

class DeployedAgentTester:
    def __init__(self, agent_url: str):
        """Initialize the tester with the deployed agent URL"""
        self.agent_url = agent_url.rstrip('/')
        self.conversation_id: Optional[str] = None
    
    def create_conversation(self) -> bool:
        """Create a new conversation with the deployed agent"""
        try:
            create_url = f"{self.agent_url}/api/conversation/create"
            response = requests.post(create_url, json={})
            
            if response.status_code == 200:
                result = response.json()
                self.conversation_id = result.get('conversation_id')
                print(f"💬 Conversation created: {self.conversation_id}")
                return True
            else:
                print(f"❌ Failed to create conversation: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating conversation: {str(e)}")
            return False
    
    def send_message(self, message: str) -> Optional[str]:
        """Send a message to the agent and get response"""
        if not self.conversation_id:
            print("❌ No active conversation")
            return None
        
        try:
            message_url = f"{self.agent_url}/api/conversation/message"
            payload = {
                "conversation_id": self.conversation_id,
                "message": message
            }
            
            print("🤔 Agent is thinking...")
            response = requests.post(message_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response')
            else:
                print(f"❌ Error sending message: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error sending message: {str(e)}")
            return None
    
    def get_agent_info(self) -> dict:
        """Get information about the deployed agent"""
        try:
            info_url = f"{self.agent_url}/"
            response = requests.get(info_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error getting agent info: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting agent info: {str(e)}")
            return {}
    
    def test_health(self) -> bool:
        """Test if the agent is healthy and responding"""
        try:
            health_url = f"{self.agent_url}/healthz"
            response = requests.get(health_url, timeout=100)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Agent is healthy")
                print(f"   Status: {health_data.get('status')}")
                print(f"   Agent ID: {health_data.get('agent_id')}")
                print(f"   Config loaded: {health_data.get('config_loaded')}")
                print(f"   Tools initialized: {health_data.get('tools_initialized')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def interactive_chat(self):
        """Start an interactive chat session with the deployed agent"""
        # Test health first
        #print("🔍 Testing agent health...")
        #if not self.test_health():
        #    print("❌ Agent health check failed. Cannot proceed with chat.")
        #    return
        
        # Get agent info
        print("\n📋 Getting agent information...")
        agent_info = self.get_agent_info()
        if agent_info:
            print(f"\n🤖 Agent Info:")
            print(f"   Name: {agent_info.get('message', 'Unknown')}")
            print(f"   Agent ID: {agent_info.get('agent_id', 'Unknown')}")
            print(f"   Domain: {agent_info.get('domain', 'Unknown')}")
            print(f"   Model: {agent_info.get('model', 'Unknown')}")
            print(f"   Tools: {agent_info.get('tools_count', 0)}")
            print(f"   Type: {agent_info.get('type', 'Unknown')}")
        
        # Create conversation
        print("\n🔗 Creating conversation...")
        if not self.create_conversation():
            return
        
        print("\n💬 Starting interactive chat session")
        print("Type 'quit', 'exit', or 'bye' to end the session")
        print("Type 'info' to see agent information again")
        print("Type 'new' to start a new conversation")
        print("=" * 60)
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye!")
                    break
                
                # Check for special commands
                if user_input.lower() == 'info':
                    agent_info = self.get_agent_info()
                    if agent_info:
                        print(f"\n🤖 Current Agent Info:")
                        for key, value in agent_info.items():
                            print(f"   {key}: {value}")
                    continue
                
                if user_input.lower() == 'new':
                    print("🔄 Starting new conversation...")
                    if self.create_conversation():
                        print("✅ New conversation created!")
                    continue
                
                if not user_input:
                    continue
                
                # Send message to agent
                response = self.send_message(user_input)
                
                if response:
                    print(f"🤖 Agent: {response}")
                else:
                    print("❌ Failed to get response from agent")
                
            except KeyboardInterrupt:
                print("\n👋 Chat session ended by user")
                break
            except Exception as e:
                print(f"❌ Error in chat session: {str(e)}")
                break


def main():
    """Main function to test the deployed agent"""
    print("🧪 Deployed Agent Tester")
    print("=" * 50)
    
    # Default agent URL
    default_agent_url = "https://agent-8e749a5b-91a3-4354-afdf-dc1d157e89fd-851487020021.us-central1.run.app"
    
    # Get agent URL from user or use default
    agent_url = input(f"Enter agent URL (default: {default_agent_url}): ").strip()
    if not agent_url:
        agent_url = default_agent_url
    
    print(f"🎯 Testing agent at: {agent_url}")
    
    # Initialize tester
    tester = DeployedAgentTester(agent_url)
    
    while True:
        print("\n🎯 Choose an option:")
        print("1. Test agent health")
        print("2. Get agent information")
        print("3. Start interactive chat")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            print("\n🔍 Testing agent health...")
            tester.test_health()
        
        elif choice == '2':
            print("\n📋 Getting agent information...")
            agent_info = tester.get_agent_info()
            if agent_info:
                print(f"\n🤖 Agent Information:")
                for key, value in agent_info.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ Failed to get agent info")
        
        elif choice == '3':
            tester.interactive_chat()
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()