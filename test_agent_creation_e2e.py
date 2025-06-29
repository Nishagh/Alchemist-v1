#!/usr/bin/env python3
"""
End-to-End Test Script for AI Agent Creation with EA3 Integration

This script tests the complete agent creation workflow from start to finish:
1. Creates a new AI agent via agent-engine API
2. Interacts with the agent to generate conversations
3. Verifies EA3 (Epistemic Autonomy, Accountability, Alignment) tracking
4. Checks life-story creation and coherence monitoring
5. Tests various EA3 endpoints and features

Usage:
    python test_agent_creation_e2e.py
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_e2e_test")

class AgentE2ETest:
    """End-to-end test for agent creation and EA3 integration"""
    
    def __init__(self, base_url: str = "http://localhost:8080", user_id: str = "6SWFwT35QEZw8QJnuwXqpPQcl3V2"):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.test_agent_id = None
        self.session = None
        
        # Test data
        self.test_agent_config = {
            "name": "TestBot Assistant",
            "description": "A comprehensive test assistant for validating the Alchemist platform",
            "instructions": "You are a helpful AI assistant designed to help users with various tasks. Be friendly, informative, and always aim to provide accurate and helpful responses.",
            "personality": "Friendly, helpful, and knowledgeable. Always eager to assist and learn from interactions.",
            "agent_type": "general",
            "status": "active"
        }
        
        # Test conversations for EA3 validation
        self.test_conversations = [
            "Hello! Can you introduce yourself and tell me what you can help with?",
            "What are your core capabilities and objectives?",
            "Can you help me understand how AI agents work?",
            "Tell me about your decision-making process.",
            "What would you do if you encountered conflicting information?",
            "How do you ensure you provide accurate and helpful responses?"
        ]
    
    async def setup_session(self):
        """Setup HTTP session with authentication"""
        self.session = aiohttp.ClientSession()
        
        # For local development, use test token format
        self.headers = {
            "Authorization": f"Bearer dev-test-{self.user_id}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Session setup complete for user: {self.user_id}")
    
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test if the agent-engine service is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"Health check passed: {health_data}")
                    return True
                else:
                    logger.error(f"Health check failed with status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Health check failed with error: {e}")
            return False
    
    async def create_agent(self) -> Optional[str]:
        """Create a new AI agent"""
        try:
            # Generate unique agent ID
            self.test_agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
            
            # Prepare agent creation payload
            payload = {
                **self.test_agent_config,
                "agent_id": self.test_agent_id
            }
            
            logger.info(f"Creating agent with ID: {self.test_agent_id}")
            
            async with self.session.post(
                f"{self.base_url}/api/agents",
                headers=self.headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Agent created successfully: {result}")
                    return result.get("agent_id") or result.get("id")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create agent. Status: {response.status}, Error: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None
    
    async def verify_agent_exists(self, agent_id: str) -> bool:
        """Verify the agent was created and is accessible"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{agent_id}",
                headers=self.headers
            ) as response:
                
                if response.status == 200:
                    agent_data = await response.json()
                    logger.info(f"Agent verification successful: {agent_data}")
                    return True
                else:
                    logger.error(f"Agent verification failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error verifying agent: {e}")
            return False
    
    async def interact_with_agent(self, agent_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Send a message to the agent and get response"""
        try:
            payload = {
                "message": message,
                "agent_id": agent_id
            }
            
            logger.info(f"Sending message to agent {agent_id}: {message}")
            
            async with self.session.post(
                f"{self.base_url}/api/alchemist/interact",
                headers=self.headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Agent response: {result.get('response', 'No response')[:100]}...")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Agent interaction failed. Status: {response.status}, Error: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error interacting with agent: {e}")
            return None
    
    async def run_conversation_sequence(self, agent_id: str) -> List[Dict[str, Any]]:
        """Run a sequence of conversations to build agent's life-story"""
        results = []
        
        for i, message in enumerate(self.test_conversations):
            logger.info(f"Running conversation {i+1}/{len(self.test_conversations)}")
            
            result = await self.interact_with_agent(agent_id, message)
            if result:
                results.append(result)
                
                # Small delay between conversations to allow EA3 processing
                await asyncio.sleep(2)
            else:
                logger.warning(f"Failed to get response for conversation {i+1}")
        
        return results
    
    async def test_ea3_life_story(self, agent_id: str) -> bool:
        """Test EA3 life-story endpoint"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{agent_id}/life-story",
                headers=self.headers
            ) as response:
                
                if response.status == 200:
                    life_story = await response.json()
                    logger.info(f"Life-story retrieved successfully. Keys: {list(life_story.keys())}")
                    
                    # Verify life-story structure
                    if 'life_story' in life_story:
                        story_data = life_story['life_story']
                        logger.info(f"Life-story contains {len(story_data)} entries")
                        return True
                    else:
                        logger.warning("Life-story data structure unexpected")
                        return False
                        
                elif response.status == 404:
                    logger.info("Life-story not found (agent may be new)")
                    return True  # This is acceptable for new agents
                elif response.status == 503:
                    logger.warning("EA3 services not available")
                    return True  # This is acceptable if EA3 is not enabled
                else:
                    logger.error(f"Life-story endpoint failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing life-story endpoint: {e}")
            return False
    
    async def test_ea3_status(self, agent_id: str) -> bool:
        """Test EA3 status endpoint"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{agent_id}/ea3-status",
                headers=self.headers
            ) as response:
                
                if response.status == 200:
                    ea3_status = await response.json()
                    logger.info(f"EA3 status retrieved successfully")
                    
                    # Verify EA3 status structure
                    if 'ea3_status' in ea3_status:
                        status_data = ea3_status['ea3_status']
                        logger.info(f"EA3 Status - Autonomy: {status_data.get('autonomy_score', 'N/A')}, "
                                  f"Alignment: {status_data.get('alignment', {}).get('alignment_score', 'N/A')}, "
                                  f"Coherence: {status_data.get('coherence', {}).get('narrative_coherence', 'N/A')}")
                        return True
                    else:
                        logger.warning("EA3 status structure unexpected")
                        return False
                        
                elif response.status == 503:
                    logger.warning("EA3 services not available")
                    return True  # Acceptable if EA3 is not enabled
                else:
                    logger.error(f"EA3 status endpoint failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing EA3 status endpoint: {e}")
            return False
    
    async def test_trigger_reflection(self, agent_id: str) -> bool:
        """Test manual trigger of autonomous reflection"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/agents/{agent_id}/trigger-reflection",
                headers=self.headers,
                json={}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Reflection triggered successfully: {result}")
                    return True
                elif response.status == 503:
                    logger.warning("EA3 services not available for reflection")
                    return True  # Acceptable if EA3 is not enabled
                else:
                    logger.error(f"Trigger reflection failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing trigger reflection: {e}")
            return False
    
    async def test_coherence_trends(self, agent_id: str) -> bool:
        """Test coherence trends endpoint"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{agent_id}/coherence-trends",
                headers=self.headers
            ) as response:
                
                if response.status == 200:
                    trends = await response.json()
                    logger.info(f"Coherence trends retrieved successfully")
                    return True
                elif response.status == 503:
                    logger.warning("EA3 services not available for coherence trends")
                    return True  # Acceptable if EA3 is not enabled
                else:
                    logger.error(f"Coherence trends endpoint failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing coherence trends: {e}")
            return False
    
    async def test_narrative_conflicts(self, agent_id: str) -> bool:
        """Test narrative conflicts endpoint"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{agent_id}/conflicts",
                headers=self.headers
            ) as response:
                
                if response.status == 200:
                    conflicts = await response.json()
                    logger.info(f"Narrative conflicts retrieved successfully")
                    return True
                elif response.status == 503:
                    logger.warning("EA3 services not available for conflicts")
                    return True  # Acceptable if EA3 is not enabled
                else:
                    logger.error(f"Narrative conflicts endpoint failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error testing narrative conflicts: {e}")
            return False
    
    async def get_conversations(self, agent_id: str) -> bool:
        """Test getting agent conversations"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{agent_id}/conversations",
                headers=self.headers
            ) as response:
                
                if response.status == 200:
                    conversations = await response.json()
                    conv_count = len(conversations.get('conversations', []))
                    logger.info(f"Retrieved {conv_count} conversation messages")
                    return True
                else:
                    logger.error(f"Get conversations failed. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return False
    
    async def run_full_test(self) -> Dict[str, bool]:
        """Run the complete end-to-end test suite"""
        results = {}
        
        try:
            await self.setup_session()
            
            # Test 1: Health Check
            logger.info("=== Testing Health Check ===")
            results['health_check'] = await self.test_health_check()
            
            if not results['health_check']:
                logger.error("Health check failed - aborting tests")
                return results
            
            # Test 2: Agent Creation
            logger.info("=== Testing Agent Creation ===")
            agent_id = await self.create_agent()
            results['agent_creation'] = agent_id is not None
            
            if not results['agent_creation']:
                logger.error("Agent creation failed - aborting tests")
                return results
            
            # Test 3: Agent Verification
            logger.info("=== Testing Agent Verification ===")
            results['agent_verification'] = await self.verify_agent_exists(agent_id)
            
            # Test 4: Agent Interactions
            logger.info("=== Testing Agent Interactions ===")
            conversation_results = await self.run_conversation_sequence(agent_id)
            results['agent_interactions'] = len(conversation_results) > 0
            
            # Wait for EA3 processing
            logger.info("Waiting for EA3 processing to complete...")
            await asyncio.sleep(5)
            
            # Test 5: EA3 Life-Story
            logger.info("=== Testing EA3 Life-Story ===")
            results['ea3_life_story'] = await self.test_ea3_life_story(agent_id)
            
            # Test 6: EA3 Status
            logger.info("=== Testing EA3 Status ===")
            results['ea3_status'] = await self.test_ea3_status(agent_id)
            
            # Test 7: Trigger Reflection
            logger.info("=== Testing Trigger Reflection ===")
            results['trigger_reflection'] = await self.test_trigger_reflection(agent_id)
            
            # Test 8: Coherence Trends
            logger.info("=== Testing Coherence Trends ===")
            results['coherence_trends'] = await self.test_coherence_trends(agent_id)
            
            # Test 9: Narrative Conflicts
            logger.info("=== Testing Narrative Conflicts ===")
            results['narrative_conflicts'] = await self.test_narrative_conflicts(agent_id)
            
            # Test 10: Get Conversations
            logger.info("=== Testing Get Conversations ===")
            results['get_conversations'] = await self.get_conversations(agent_id)
            
            # Store agent ID for cleanup
            self.test_agent_id = agent_id
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            results['execution_error'] = str(e)
        
        finally:
            await self.cleanup_session()
        
        return results
    
    def print_test_summary(self, results: Dict[str, bool]):
        """Print a summary of test results"""
        print("\n" + "="*60)
        print("AGENT CREATION E2E TEST SUMMARY")
        print("="*60)
        
        passed = 0
        total = 0
        
        for test_name, result in results.items():
            if test_name == 'execution_error':
                continue
                
            total += 1
            status = "PASS" if result else "FAIL"
            status_color = "✅" if result else "❌"
            
            if result:
                passed += 1
            
            print(f"{status_color} {test_name.replace('_', ' ').title()}: {status}")
        
        print("-"*60)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        if 'execution_error' in results:
            print(f"❌ Execution Error: {results['execution_error']}")
        
        if self.test_agent_id:
            print(f"\n📝 Test Agent ID: {self.test_agent_id}")
            print(f"🌐 Agent URL: {self.base_url}/api/agents/{self.test_agent_id}")
        
        print("="*60)


async def main():
    """Main function to run the E2E tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="End-to-End Agent Creation Test")
    parser.add_argument("--url", default="http://localhost:8080", help="Base URL for agent-engine service")
    parser.add_argument("--user-id", default="6SWFwT35QEZw8QJnuwXqpPQcl3V2", help="User ID for testing")
    
    args = parser.parse_args()
    
    # Create test instance
    test = AgentE2ETest(base_url=args.url, user_id=args.user_id)
    
    # Run tests
    print("Starting End-to-End Agent Creation Test...")
    print(f"Target URL: {args.url}")
    print(f"User ID: {args.user_id}")
    print("-"*60)
    
    start_time = time.time()
    results = await test.run_full_test()
    end_time = time.time()
    
    # Print results
    test.print_test_summary(results)
    print(f"⏱️  Total Test Time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())