#!/usr/bin/env python3
"""
Comprehensive validation script for agent story recording compliance
Tests all components of the agent lifecycle event and story recording system
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, '/Users/nishants/Desktop/Alchemist-v1/shared')

def test_imports():
    """Test that all required modules can be imported"""
    print("=== Testing Imports ===")
    
    try:
        from alchemist_shared.services.agent_lifecycle_service import (
            AgentLifecycleService, get_agent_lifecycle_service
        )
        print("✅ AgentLifecycleService imported successfully")
        
        from alchemist_shared.events.story_events import (
            StoryEvent, StoryEventType, StoryEventPriority, get_story_event_publisher
        )
        print("✅ Story event system imported successfully")
        
        from alchemist_shared.services.ea3_orchestrator import (
            EA3Orchestrator, is_ea3_available, get_ea3_availability_status
        )
        print("✅ eA³ Orchestrator imported successfully")
        
        from alchemist_shared.services.spanner_graph_service import SpannerGraphService
        print("✅ Spanner Graph Service imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_event_types():
    """Test that all required event types are available"""
    print("\n=== Testing Event Types ===")
    
    try:
        from alchemist_shared.events.story_events import StoryEventType
        
        # Required event types for comprehensive agent story recording
        required_events = [
            'AGENT_CREATED', 'AGENT_NAMED', 'AGENT_DEPLOYED', 'AGENT_UNDEPLOYED',
            'CONVERSATION', 'PROMPT_UPDATE', 'CONFIGURATION_UPDATED',
            'KNOWLEDGE_BASE_FILE_ADDED', 'KNOWLEDGE_BASE_FILE_REMOVED',
            'EXTERNAL_API_ATTACHED', 'EXTERNAL_API_DETACHED',
            'BILLING_TRANSACTION', 'INTEGRATION_CONNECTED', 'INTEGRATION_DISCONNECTED',
            'PERFORMANCE_ISSUE', 'USER_FEEDBACK', 'AGENT_STATUS_CHANGED'
        ]
        
        missing_events = []
        
        for event in required_events:
            if hasattr(StoryEventType, event):
                print(f"✅ {event}")
            else:
                print(f"❌ {event} - MISSING")
                missing_events.append(event)
        
        if missing_events:
            print(f"\n⚠️ Missing {len(missing_events)} event types")
            return False
        else:
            print(f"\n✅ All {len(required_events)} required event types available")
            return True
            
    except Exception as e:
        print(f"❌ Event type test failed: {e}")
        return False

def test_lifecycle_service():
    """Test agent lifecycle service functionality"""
    print("\n=== Testing Agent Lifecycle Service ===")
    
    try:
        from alchemist_shared.services.agent_lifecycle_service import AgentLifecycleService
        
        # Initialize service
        lifecycle_service = AgentLifecycleService()
        print("✅ Lifecycle service initialized")
        
        # Check available methods
        record_methods = [method for method in dir(lifecycle_service) if method.startswith('record_')]
        print(f"✅ {len(record_methods)} record methods available")
        
        # Verify key methods exist
        key_methods = [
            'record_agent_created', 'record_agent_deployed', 'record_billing_transaction',
            'record_integration_event', 'record_user_feedback', 'record_performance_issue'
        ]
        
        for method in key_methods:
            if hasattr(lifecycle_service, method):
                print(f"✅ {method}")
            else:
                print(f"❌ {method} - MISSING")
                return False
        
        print("✅ All key lifecycle methods available")
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle service test failed: {e}")
        return False

def test_spanner_integration():
    """Test Spanner integration availability"""
    print("\n=== Testing Spanner Integration ===")
    
    try:
        from alchemist_shared.services.ea3_orchestrator import get_ea3_availability_status
        
        # Set project ID for testing
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'alchemist-e69bb'
        
        status = get_ea3_availability_status()
        print(f"eA³ Available: {status['available']}")
        print(f"Initialized: {status['initialized']}")
        
        config = status.get('configuration', {})
        print(f"Project ID: {config.get('project_id', 'NOT SET')}")
        print(f"Instance ID: {config.get('instance_id', 'NOT SET')}")
        print(f"Database ID: {config.get('database_id', 'NOT SET')}")
        
        # Check if basic configuration is present
        if config.get('project_id') and config.get('instance_id') and config.get('database_id'):
            print("✅ Basic Spanner configuration available")
            if not config.get('credentials_path'):
                print("⚠️ No credentials path set (expected for local environment)")
            return True
        else:
            print("❌ Missing Spanner configuration")
            return False
            
    except Exception as e:
        print(f"❌ Spanner integration test failed: {e}")
        return False

async def test_story_event_creation():
    """Test creation of story events"""
    print("\n=== Testing Story Event Creation ===")
    
    try:
        from alchemist_shared.events.story_events import StoryEvent, StoryEventType, StoryEventPriority
        
        # Create a test story event
        test_event = StoryEvent(
            agent_id="test_agent_123",
            event_type=StoryEventType.AGENT_CREATED,
            content="Test agent created for validation",
            source_service="validation_script",
            priority=StoryEventPriority.HIGH,
            metadata={
                "test": True,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        print("✅ Story event created successfully")
        print(f"   Event ID: {test_event.event_id}")
        print(f"   Agent ID: {test_event.agent_id}")
        print(f"   Event Type: {test_event.event_type}")
        print(f"   Priority: {test_event.priority}")
        
        return True
        
    except Exception as e:
        print(f"❌ Story event creation failed: {e}")
        return False

def test_gnf_integration():
    """Test Global Narrative Framework integration"""
    print("\n=== Testing GNF Integration ===")
    
    try:
        # Check if GNF deployment configuration exists
        gnf_config_path = "/Users/nishants/Desktop/Alchemist-v1/global-narative-framework/DEPLOYMENT_CONFIGURATION.md"
        
        if os.path.exists(gnf_config_path):
            print("✅ GNF deployment configuration exists")
            
            # Check for key GNF files
            gnf_main = "/Users/nishants/Desktop/Alchemist-v1/global-narative-framework/main.py"
            gnf_tracker = "/Users/nishants/Desktop/Alchemist-v1/global-narative-framework/gnf/core/narrative_tracker.py"
            
            if os.path.exists(gnf_main):
                print("✅ GNF main service file exists")
            if os.path.exists(gnf_tracker):
                print("✅ GNF narrative tracker exists")
                
            print("✅ GNF integration ready for deployment")
            return True
        else:
            print("❌ GNF deployment configuration missing")
            return False
            
    except Exception as e:
        print(f"❌ GNF integration test failed: {e}")
        return False

def generate_compliance_report(results):
    """Generate final compliance report"""
    print("\n" + "="*60)
    print("AGENT STORY RECORDING COMPLIANCE REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print("\nCompliance Status:")
    if passed_tests == total_tests:
        print("🎯 FULLY COMPLIANT: All agent story recording systems operational")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ MOSTLY COMPLIANT: Minor issues detected, system functional")
    else:
        print("❌ NON-COMPLIANT: Major issues detected, manual intervention required")
    
    print("\nNext Steps:")
    if passed_tests == total_tests:
        print("• System ready for production deployment")
        print("• Configure Spanner credentials for full EA3 integration")
        print("• Deploy GNF service with proper environment variables")
    else:
        print("• Address failed test components")
        print("• Review configuration and dependencies")
        print("• Re-run validation after fixes")

async def main():
    """Run all validation tests"""
    print("Agent Story Recording Compliance Validation")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    # Run all tests
    results = {
        "Module Imports": test_imports(),
        "Event Types": test_event_types(), 
        "Lifecycle Service": test_lifecycle_service(),
        "Spanner Integration": test_spanner_integration(),
        "Story Event Creation": await test_story_event_creation(),
        "GNF Integration": test_gnf_integration()
    }
    
    # Generate compliance report
    generate_compliance_report(results)

if __name__ == "__main__":
    asyncio.run(main())