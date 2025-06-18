#!/usr/bin/env python3
"""
Quick test to deploy and interact with an agent
"""

import requests
import time

def deploy_and_test_agent():
    deployment_service_url = "https://alchemist-deployment-service-b3hpe34qdq-uc.a.run.app"
    agent_id = "8e749a5b-91a3-4354-afdf-dc1d157e89fd"
    
    print("🚀 Starting agent deployment...")
    
    # Deploy agent
    deploy_response = requests.post(
        f"{deployment_service_url}/api/deploy",
        json={"agent_id": agent_id}
    )
    
    if deploy_response.status_code == 200:
        deployment_data = deploy_response.json()
        deployment_id = deployment_data.get('deployment_id')
        print(f"✅ Deployment started with ID: {deployment_id}")
        
        # Wait for completion
        print("⏳ Waiting for deployment...")
        while True:
            status_response = requests.get(
                f"{deployment_service_url}/api/deployment/{deployment_id}/status"
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                progress = status_data.get('progress_percentage', 0)
                step = status_data.get('current_step', '')
                
                print(f"📊 {progress}% - {step}")
                
                if status == 'completed':
                    agent_url = status_data.get('service_url')
                    print(f"🎉 Agent deployed at: {agent_url}")
                    return agent_url
                elif status == 'failed':
                    error = status_data.get('error_message', 'Unknown error')
                    print(f"❌ Deployment failed: {error}")
                    return None
                    
                time.sleep(10)
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return None
    else:
        print(f"❌ Deployment request failed: {deploy_response.status_code} - {deploy_response.text}")
        return None

if __name__ == "__main__":
    agent_url = deploy_and_test_agent()
    if agent_url:
        print(f"\n🎯 Agent URL: {agent_url}")
        print("You can now test this agent!")
    else:
        print("\n❌ Deployment failed")