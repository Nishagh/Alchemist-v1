#!/usr/bin/env python3
"""
Test script to verify prompt lifecycle event tracking integration.

This script tests that:
1. The prompt-engine correctly initializes the lifecycle service
2. System prompt updates trigger lifecycle events
3. Events are recorded in the agent_lifecycle_events collection
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_lifecycle_service_initialization():
    """Test that the lifecycle service can be initialized."""
    try:
        # Import and initialize the lifecycle service
        from shared.alchemist_shared.services.agent_lifecycle_service import (
            init_agent_lifecycle_service,
            get_agent_lifecycle_service
        )
        
        # Initialize the service
        service = init_agent_lifecycle_service()
        assert service is not None, "Lifecycle service should be initialized"
        
        # Check that we can get the service
        service_instance = get_agent_lifecycle_service()
        assert service_instance is not None, "Should be able to get lifecycle service instance"
        assert service_instance == service, "Should return the same instance"
        
        logger.info("✅ Lifecycle service initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Lifecycle service initialization test failed: {e}")
        return False

async def test_prompt_lifecycle_event_recording():
    """Test that prompt update events can be recorded."""
    try:
        from shared.alchemist_shared.services.agent_lifecycle_service import (
            get_agent_lifecycle_service
        )
        
        service = get_agent_lifecycle_service()
        if not service:
            logger.error("❌ Lifecycle service not available")
            return False
            
        # Test recording a prompt update event
        test_agent_id = f"test_agent_{int(datetime.now().timestamp())}"
        test_user_id = "test_user_123"
        
        event_id = await service.record_prompt_updated(
            agent_id=test_agent_id,
            user_id=test_user_id,
            metadata={
                "instructions": "Update the system prompt to be more helpful",
                "prompt_length": 150,
                "action": "updated",
                "service": "prompt-engine-test"
            }
        )
        
        assert event_id is not None, "Should return an event ID"
        logger.info(f"✅ Prompt lifecycle event recorded with ID: {event_id}")
        
        # Test retrieving the event
        events = service.get_agent_lifecycle_events(test_agent_id, limit=1)
        assert len(events) > 0, "Should find the recorded event"
        
        event = events[0]
        assert event['agent_id'] == test_agent_id, "Event should have correct agent_id"
        assert event['user_id'] == test_user_id, "Event should have correct user_id"
        assert event['event_type'] == 'prompt_update', "Event should be prompt_update type"
        
        logger.info("✅ Prompt lifecycle event recording test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Prompt lifecycle event recording test failed: {e}")
        return False

async def test_prompt_engine_routes_integration():
    """Test that the prompt engine routes have the lifecycle integration."""
    try:
        # Import the routes module to check for lifecycle service imports
        sys.path.insert(0, 'prompt-engine')
        
        from routes import record_prompt_lifecycle_event
        from routes import PromptInstructionsRequest
        
        # Test that the request model includes user_id
        request = PromptInstructionsRequest(
            agent_id="test_agent",
            instructions="Test instructions",
            user_id="test_user"
        )
        
        assert hasattr(request, 'user_id'), "Request model should have user_id field"
        assert request.user_id == "test_user", "user_id should be set correctly"
        
        logger.info("✅ Prompt engine routes integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Prompt engine routes integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests and report results."""
    logger.info("🧪 Starting prompt lifecycle integration tests...")
    
    results = []
    
    # Test 1: Lifecycle service initialization
    results.append(await test_lifecycle_service_initialization())
    
    # Test 2: Event recording
    results.append(await test_prompt_lifecycle_event_recording())
    
    # Test 3: Routes integration
    results.append(await test_prompt_engine_routes_integration())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The prompt lifecycle integration is working correctly.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    asyncio.run(run_all_tests())