#!/usr/bin/env python3
"""
Test script for deployed agents via Universal Deployment Service

This script allows you to:
1. Deploy an agent using the deployment service
2. Interact with the deployed agent in a conversational loop
3. Test the complete deployment and chat flow
"""

import requests
import json
import time
from typing import Optional

class AgentDeploymentTester:
    def __init__(self, deployment_service_url: str):
        """Initialize the tester with deployment service URL"""
        self.deployment_service_url = deployment_service_url.rstrip('/')
        self.deployed_agent_url: Optional[str] = None
        self.conversation_id: Optional[str] = None
    
    def deploy_agent(self, agent_id: str) -> bool:
        """Deploy an agent and get its service URL"""
        try:
            print(f"🚀 Deploying agent: {agent_id}")
            print("This may take a few minutes...")
            
            # Start deployment
            deploy_url = f"{self.deployment_service_url}/api/deploy"
            payload = {"agent_id": agent_id}
            
            response = requests.post(deploy_url, json=payload, timeout=600)
            
            if response.status_code == 200:
                result = response.json()
                deployment_id = result.get('deployment_id')
                print(f"✅ Deployment started with ID: {deployment_id}")
                
                # Poll for completion
                return self._wait_for_deployment(deployment_id)
            else:
                print(f"❌ Deployment failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying agent: {str(e)}")
            return False
    
    def _wait_for_deployment(self, deployment_id: str) -> bool:
        """Wait for deployment to complete and get service URL"""
        status_url = f"{self.deployment_service_url}/api/deploy/{deployment_id}/status"
        
        print("⏳ Waiting for deployment to complete...")
        
        while True:
            try:
                response = requests.get(status_url)
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress_percentage', 0)
                    current_step = status_data.get('current_step', '')
                    
                    print(f"📊 Progress: {progress}% - {current_step}")
                    
                    if status == 'completed':
                        self.deployed_agent_url = status_data.get('service_url')
                        print(f"🎉 Deployment completed!")
                        print(f"🌐 Agent URL: {self.deployed_agent_url}")
                        return True
                    elif status == 'failed':
                        error = status_data.get('error', 'Unknown error')
                        print(f"❌ Deployment failed: {error}")
                        return False
                    
                    time.sleep(5)  # Wait 5 seconds before checking again
                else:
                    print(f"❌ Error checking status: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error checking deployment status: {str(e)}")
                return False
    
    def create_conversation(self) -> bool:
        """Create a new conversation with the deployed agent"""
        if not self.deployed_agent_url:
            print("❌ No deployed agent URL available")
            return False
        
        try:
            create_url = f"{self.deployed_agent_url}/api/conversation/create"
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
        if not self.deployed_agent_url or not self.conversation_id:
            print("❌ No active conversation")
            return None
        
        try:
            message_url = f"{self.deployed_agent_url}/api/conversation/message"
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
        if not self.deployed_agent_url:
            return {}
        
        try:
            info_url = f"{self.deployed_agent_url}/"
            response = requests.get(info_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            print(f"❌ Error getting agent info: {str(e)}")
            return {}
    
    def interactive_chat(self):
        """Start an interactive chat session with the deployed agent"""
        if not self.deployed_agent_url:
            print("❌ No deployed agent available")
            return
        
        # Get agent info
        agent_info = self.get_agent_info()
        if agent_info:
            print(f"\n🤖 Agent Info:")
            print(f"   Name: {agent_info.get('message', 'Unknown')}")
            print(f"   Agent ID: {agent_info.get('agent_id', 'Unknown')}")
            print(f"   Domain: {agent_info.get('domain', 'Unknown')}")
            print(f"   Model: {agent_info.get('model', 'Unknown')}")
            print(f"   Tools: {agent_info.get('tools_count', 0)}")
        
        # Create conversation
        if not self.create_conversation():
            return
        
        print("\n💬 Starting interactive chat session")
        print("Type 'quit', 'exit', or 'bye' to end the session")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye!")
                    break
                
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
    """Main function to run the agent deployment tester"""
    print("🧪 Universal Agent Deployment Tester")
    print("=" * 50)
    
    # Get deployment service URL
    deployment_service_url = input("Enter deployment service URL (default: https://alchemist-deployment-service-b3hpe34qdq-uc.a.run.app): ").strip()
    if not deployment_service_url:
        deployment_service_url = "https://alchemist-deployment-service-b3hpe34qdq-uc.a.run.app"
    
    # Initialize tester
    tester = AgentDeploymentTester(deployment_service_url)
    
    while True:
        print("\n🎯 Choose an option:")
        print("1. Deploy a new agent")
        print("2. Chat with deployed agent (if available)")
        print("3. Get agent info")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            agent_id = input("Enter agent ID to deploy: ").strip()
            if agent_id:
                if tester.deploy_agent(agent_id):
                    print("✅ Agent deployed successfully!")
                    # Automatically start chat after successful deployment
                    start_chat = input("Start chatting with the agent? (y/n): ").strip().lower()
                    if start_chat in ['y', 'yes']:
                        tester.interactive_chat()
                else:
                    print("❌ Agent deployment failed")
            else:
                print("❌ Please enter a valid agent ID")
        
        elif choice == '2':
            if tester.deployed_agent_url:
                tester.interactive_chat()
            else:
                print("❌ No deployed agent available. Please deploy an agent first.")
        
        elif choice == '3':
            if tester.deployed_agent_url:
                agent_info = tester.get_agent_info()
                if agent_info:
                    print(f"\n🤖 Agent Information:")
                    for key, value in agent_info.items():
                        print(f"   {key}: {value}")
                else:
                    print("❌ Failed to get agent info")
            else:
                print("❌ No deployed agent available")
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()