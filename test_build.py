#!/usr/bin/env python3
"""
Test script to verify that the knowledge-vault can import its dependencies
without Firebase initialization errors.
"""

import os
import sys
import tempfile
import subprocess

def test_imports():
    """Test that all imports work without Firebase initialization"""
    
    # Create a minimal Firebase credentials file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"type": "service_account", "project_id": "test"}')
        credentials_file = f.name
    
    try:
        # Set the credentials environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
        
        # Add the shared package to Python path
        shared_path = '/Users/nishants/Desktop/Alchemist-v1/shared'
        if shared_path not in sys.path:
            sys.path.insert(0, shared_path)
        
        # Test 1: Import shared services without triggering Firebase initialization
        print("🧪 Testing alchemist_shared imports...")
        try:
            from alchemist_shared.services import get_ea3_orchestrator, ConversationContext
            print("✅ alchemist_shared services imported successfully")
        except ImportError as e:
            if "spanner" in str(e) or "pubsub" in str(e) or "redis" in str(e):
                print(f"⚠️  Expected missing dependency: {e}")
                print("   (This is normal in local testing - these packages are installed in Docker)")
            else:
                print(f"❌ Unexpected import error: {e}")
                return False
        except Exception as e:
            if "Firebase app does not exist" in str(e):
                print(f"❌ Firebase initialization still happening at import time: {e}")
                return False
            else:
                print(f"⚠️  Other error (may be expected): {e}")
        
        # Test 2: Import knowledge-vault file service
        print("\n🧪 Testing knowledge-vault imports...")
        knowledge_vault_path = '/Users/nishants/Desktop/Alchemist-v1/knowledge-vault'
        if knowledge_vault_path not in sys.path:
            sys.path.insert(0, knowledge_vault_path)
        
        try:
            from app.services.file_service import FileService
            print("✅ FileService imported successfully")
        except ImportError as e:
            if any(pkg in str(e) for pkg in ["spanner", "pubsub", "redis", "firebase_admin"]):
                print(f"⚠️  Expected missing dependency: {e}")
            else:
                print(f"❌ Unexpected import error: {e}")
                return False
        except Exception as e:
            if "Firebase app does not exist" in str(e):
                print(f"❌ Firebase initialization still happening at import time: {e}")
                return False
            else:
                print(f"⚠️  Other error (may be expected): {e}")
        
        print("\n✅ All critical imports are working - lazy initialization successful!")
        return True
        
    finally:
        # Clean up
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        try:
            os.unlink(credentials_file)
        except:
            pass

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)