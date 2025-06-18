#!/usr/bin/env python3
"""
Simple agent test without user input
"""

import requests

def test_agent(agent_url):
    print(f"🧪 Testing agent at: {agent_url}")
    
    # Test root endpoint
    try:
        response = requests.get(agent_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Root endpoint works: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{agent_url}/healthz", timeout=10)
        if response.status_code == 200:
            print(f"✅ Health endpoint works: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
    
    # Test conversation create
    try:
        response = requests.post(f"{agent_url}/api/conversation/create", json={}, timeout=10)
        if response.status_code == 200:
            print(f"✅ Conversation API works: {response.json()}")
        else:
            print(f"❌ Conversation API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Conversation API error: {str(e)}")

if __name__ == "__main__":
    # Test the local agent first
    test_agent("http://localhost:8080")
    
    # Test the working deployed agent
    print("\n" + "="*50)
    test_agent("https://ai-agent-851487020021.us-central1.run.app")
    
    # Also test the agent URL that was supposed to be deployed
    print("\n" + "="*50)
    test_agent("https://agent-8e749a5b-b3hpe34qdq-uc.a.run.app")