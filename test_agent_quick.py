#!/usr/bin/env python3
"""
Quick Agent Creation Test - Validates core functionality without full conversation sequence
"""
import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("quick_test")

async def quick_test():
    base_url = "http://localhost:8080"
    user_id = "6SWFwT35QEZw8QJnuwXqpPQcl3V2"
    
    headers = {
        "Authorization": f"Bearer dev-test-{user_id}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        print("🚀 Starting Quick Agent Creation Test...")
        
        # Test 1: Health Check
        async with session.get(f"{base_url}/health") as response:
            health_ok = response.status == 200
            print(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
        
        if not health_ok:
            return
        
        # Test 2: Create Agent
        agent_data = {
            "name": "QuickTest Agent",
            "description": "Quick test agent",
            "instructions": "Be helpful",
            "personality": "Friendly",
            "agent_type": "general",
            "status": "active"
        }
        
        async with session.post(f"{base_url}/api/agents", headers=headers, json=agent_data) as response:
            create_ok = response.status == 200
            if create_ok:
                result = await response.json()
                agent_id = result.get("agent_id")
                print(f"✅ Agent Creation: PASS (ID: {agent_id})")
            else:
                print(f"❌ Agent Creation: FAIL (Status: {response.status})")
                return
        
        # Test 3: Verify Agent
        async with session.get(f"{base_url}/api/agents/{agent_id}", headers=headers) as response:
            verify_ok = response.status == 200
            print(f"✅ Agent Verification: {'PASS' if verify_ok else 'FAIL'}")
        
        # Test 4: Single Interaction
        interaction_data = {"message": "Hello, how are you?", "agent_id": agent_id}
        async with session.post(f"{base_url}/api/alchemist/interact", headers=headers, json=interaction_data) as response:
            interact_ok = response.status == 200
            if interact_ok:
                result = await response.json()
                response_text = result.get("response", "")[:50]
                print(f"✅ Agent Interaction: PASS (Response: {response_text}...)")
            else:
                print(f"❌ Agent Interaction: FAIL (Status: {response.status})")
        
        # Test 5: EA3 Life Story (optional)
        async with session.get(f"{base_url}/api/agents/{agent_id}/life-story", headers=headers) as response:
            if response.status == 200:
                print("✅ EA3 Life Story: PASS")
            elif response.status == 503:
                print("⚠️  EA3 Life Story: SKIP (Service not available)")
            else:
                print("❌ EA3 Life Story: FAIL")
        
        # Test 6: EA3 Status (optional) 
        async with session.get(f"{base_url}/api/agents/{agent_id}/ea3-status", headers=headers) as response:
            if response.status == 200:
                print("✅ EA3 Status: PASS")
            elif response.status == 503:
                print("⚠️  EA3 Status: SKIP (Service not available)")
            else:
                print("❌ EA3 Status: FAIL")
        
        print(f"\n🎯 Test completed! Agent ID: {agent_id}")
        print(f"🌐 Agent URL: {base_url}/api/agents/{agent_id}")

if __name__ == "__main__":
    asyncio.run(quick_test())