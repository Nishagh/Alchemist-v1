#!/usr/bin/env python3
"""
Test script to verify Firebase and OpenAI credentials functionality.

This script tests the alchemist_shared library by:
1. Testing Firebase connection and basic operations
2. Testing OpenAI API connectivity (if credentials are available)
3. Validating shared library imports and functionality
"""

import os
import sys
import logging
from typing import Dict, Any

# Add shared library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test shared library imports
    from alchemist_shared.database.firebase_client import FirebaseClient, get_firestore_client
    from alchemist_shared.config.base_settings import BaseSettings
    from alchemist_shared.constants.collections import Collections
    print("✅ Successfully imported alchemist_shared modules")
except ImportError as e:
    print(f"❌ Failed to import alchemist_shared modules: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_firebase_connection():
    """Test Firebase connection and basic operations."""
    print("\n🔥 Testing Firebase Connection...")
    
    try:
        # Set explicit credentials path for the shared folder
        os.environ['FIREBASE_CREDENTIALS_PATH'] = '/Users/nishants/Desktop/Alchemist-v1/shared/firebase-credentials.json'
        
        # Initialize Firebase client
        firebase_client = FirebaseClient()
        db = firebase_client.db
        
        print("✅ Firebase client initialized successfully")
        
        # Test basic Firestore operation
        test_collection = db.collection('test_connection')
        test_doc = test_collection.document('test_doc')
        
        # Write test data
        test_data = {
            'message': 'Hello from alchemist_shared test',
            'timestamp': '2024-01-01T00:00:00Z',
            'test_run': True
        }
        
        test_doc.set(test_data)
        print("✅ Successfully wrote test document to Firestore")
        
        # Read test data
        doc_snapshot = test_doc.get()
        if doc_snapshot.exists:
            retrieved_data = doc_snapshot.to_dict()
            print(f"✅ Successfully read test document: {retrieved_data.get('message')}")
        else:
            print("⚠️  Test document not found after write")
        
        # Test collection access methods
        agents_collection = firebase_client.get_agents_collection()
        print(f"✅ Agents collection reference: {agents_collection.id}")
        
        # Clean up test document
        test_doc.delete()
        print("✅ Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        logger.error(f"Firebase error details: {e}", exc_info=True)
        return False


def test_openai_connection():
    """Test OpenAI API connection if credentials are available."""
    print("\n🤖 Testing OpenAI Connection...")
    
    # Check for OpenAI API key
    settings = BaseSettings()
    openai_config = settings.get_openai_config()
    
    if not openai_config.get('api_key'):
        print("⚠️  OpenAI API key not found in environment variables")
        print("   Set OPENAI_API_KEY environment variable to test OpenAI connectivity")
        return False
    
    try:
        # Try to import OpenAI (check if it's available in the environment)
        import openai
        
        # Configure OpenAI client
        client = openai.OpenAI(
            api_key=openai_config['api_key'],
            organization=openai_config.get('organization')
        )
        
        # Test simple API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from Alchemist shared library test!'"}
            ],
            max_tokens=50
        )
        
        message = response.choices[0].message.content
        print(f"✅ OpenAI API response: {message}")
        return True
        
    except ImportError:
        print("⚠️  OpenAI library not installed. Install with: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        logger.error(f"OpenAI error details: {e}", exc_info=True)
        return False


def test_settings_configuration():
    """Test configuration and settings functionality."""
    print("\n⚙️  Testing Settings Configuration...")
    
    try:
        settings = BaseSettings()
        
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Service name: {settings.service_name}")
        print(f"✅ Debug mode: {settings.debug}")
        print(f"✅ Is cloud environment: {settings.is_cloud_environment}")
        
        # Test OpenAI config
        openai_config = settings.get_openai_config()
        has_api_key = bool(openai_config.get('api_key'))
        print(f"✅ OpenAI API key configured: {has_api_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings configuration failed: {e}")
        logger.error(f"Settings error details: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    print("🧪 Alchemist Shared Library Credential Test")
    print("=" * 50)
    
    results = {}
    
    # Test settings first
    results['settings'] = test_settings_configuration()
    
    # Test Firebase
    results['firebase'] = test_firebase_connection()
    
    # Test OpenAI
    results['openai'] = test_openai_connection()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.capitalize():12} {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Alchemist shared library is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())