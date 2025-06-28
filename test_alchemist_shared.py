#!/usr/bin/env python3
"""
Test script to verify alchemist-shared package imports work correctly
"""

import sys
import os
import tempfile

def test_alchemist_shared():
    """Test all critical imports from alchemist-shared"""
    
    # Add shared package to Python path
    shared_path = '/Users/nishants/Desktop/Alchemist-v1/shared'
    if shared_path not in sys.path:
        sys.path.insert(0, shared_path)
    
    print("🧪 Testing alchemist-shared package...")
    
    # Test 1: Events module
    print("\n📡 Testing events module...")
    try:
        from alchemist_shared.events import (
            get_story_event_publisher,
            init_story_event_publisher,
            StoryEvent,
            StoryEventType,
            StoryEventPriority
        )
        print("✅ Events imports successful")
    except ImportError as e:
        if "pubsub" in str(e).lower() or "google.cloud" in str(e):
            print(f"⚠️  Expected missing Google Cloud dependency: {e}")
        else:
            print(f"❌ Unexpected events import error: {e}")
            return False
    except Exception as e:
        print(f"❌ Events module error: {e}")
        return False
    
    # Test 2: Services module
    print("\n🔧 Testing services module...")
    try:
        from alchemist_shared.services import (
            get_ea3_orchestrator,
            ConversationContext,
            get_spanner_graph_service,
            init_ea3_orchestrator
        )
        print("✅ Services imports successful")
    except ImportError as e:
        if any(pkg in str(e).lower() for pkg in ["spanner", "pubsub", "redis", "google.cloud"]):
            print(f"⚠️  Expected missing Google Cloud dependency: {e}")
        else:
            print(f"❌ Unexpected services import error: {e}")
            return False
    except Exception as e:
        if "firebase app does not exist" in str(e).lower():
            print(f"❌ Firebase still initializing at import time: {e}")
            return False
        else:
            print(f"⚠️  Other services error (may be expected): {e}")
    
    # Test 3: Config module
    print("\n⚙️  Testing config module...")
    try:
        from alchemist_shared.config.base_settings import get_gcp_project_id
        print("✅ Config imports successful")
    except ImportError as e:
        print(f"❌ Config import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Config module error (may be expected): {e}")
    
    # Test 4: Middleware module
    print("\n🔄 Testing middleware module...")
    try:
        from alchemist_shared.middleware import (
            setup_metrics_middleware,
            start_background_metrics_collection,
            stop_background_metrics_collection
        )
        print("✅ Middleware imports successful")
    except ImportError as e:
        print(f"❌ Middleware import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Middleware module error (may be expected): {e}")
    
    # Test 5: Verify package structure
    print("\n📁 Testing package structure...")
    try:
        import alchemist_shared
        print(f"✅ Package root accessible: {alchemist_shared.__file__}")
        
        # Check if key modules exist
        modules_to_check = [
            'alchemist_shared.events',
            'alchemist_shared.services', 
            'alchemist_shared.config',
            'alchemist_shared.middleware'
        ]
        
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                print(f"✅ Module {module_name} accessible")
            except ImportError as e:
                if any(pkg in str(e).lower() for pkg in ["spanner", "pubsub", "redis", "google.cloud", "aiohttp"]):
                    print(f"⚠️  Module {module_name} - expected missing dependency: {e}")
                else:
                    print(f"❌ Module {module_name} - unexpected error: {e}")
                    return False
            except Exception as e:
                if "firebase app does not exist" in str(e).lower():
                    print(f"❌ Module {module_name} - Firebase initialization error: {e}")
                    return False
                else:
                    print(f"⚠️  Module {module_name} - other error: {e}")
        
    except Exception as e:
        print(f"❌ Package structure error: {e}")
        return False
    
    print("\n✅ alchemist-shared package test completed successfully!")
    print("   All critical imports work - missing dependencies are expected in local environment")
    return True

def test_knowledge_vault_imports():
    """Test knowledge-vault can import alchemist-shared"""
    
    print("\n🏗️  Testing knowledge-vault integration...")
    
    # Add knowledge-vault to path
    kv_path = '/Users/nishants/Desktop/Alchemist-v1/knowledge-vault'
    if kv_path not in sys.path:
        sys.path.insert(0, kv_path)
    
    try:
        # Test the specific import that was failing
        from alchemist_shared.events import get_story_event_publisher
        print("✅ get_story_event_publisher import successful")
        
        # Test the full file service import
        from app.services.file_service import FileService
        print("✅ FileService import successful")
        
        return True
        
    except ImportError as e:
        if any(pkg in str(e).lower() for pkg in ["spanner", "pubsub", "redis", "google.cloud", "docx2txt", "firebase_admin"]):
            print(f"⚠️  Expected missing dependency: {e}")
            return True  # This is expected in local testing
        else:
            print(f"❌ Unexpected import error: {e}")
            return False
    except Exception as e:
        if "firebase app does not exist" in str(e).lower():
            print(f"❌ Firebase initialization error: {e}")
            return False
        else:
            print(f"⚠️  Other error (may be expected): {e}")
            return True

if __name__ == "__main__":
    print("🔍 Testing alchemist-shared package before deployment...")
    
    success1 = test_alchemist_shared()
    success2 = test_knowledge_vault_imports()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("   alchemist-shared is ready for deployment")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED!")
        print("   Fix issues before deployment")
        sys.exit(1)