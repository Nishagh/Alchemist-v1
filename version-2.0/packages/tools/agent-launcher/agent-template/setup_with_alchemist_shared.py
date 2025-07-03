#!/usr/bin/env python3
"""
Setup script demonstrating alchemist-shared integration
"""

import os
import sys
from pathlib import Path
from alchemist_shared.config.base_settings import BaseSettings

settings = BaseSettings()

def check_alchemist_shared():
    """Check if alchemist-shared is available"""
    try:
        from alchemist_shared.config.base_settings import BaseSettings
        from alchemist_shared.config.environment import get_project_id
        from alchemist_shared.database.firebase_client import FirebaseClient
        print("✅ alchemist-shared is available")
        return True
    except ImportError as e:
        print(f"❌ alchemist-shared not available: {e}")
        return False

def check_credentials():
    """Check if credentials are accessible through alchemist-shared"""
    try:
        from alchemist_shared.config.base_settings import BaseSettings
        from alchemist_shared.config.environment import get_project_id
        
        settings = BaseSettings()
        
        # Check OpenAI API key
        openai_config = settings.get_openai_config()
        if openai_config and openai_config.get("api_key"):
            api_key = openai_config.get("api_key")
            print(f"✅ OpenAI API key found: {api_key[:8]}...")
        else:
            print("⚠️  OpenAI API key not found in alchemist-shared")
        
        # Check Firebase credentials
        firebase_creds = settings.google_application_credentials
        if firebase_creds:
            print(f"✅ Firebase credentials path: {firebase_creds}")
        else:
            print("⚠️  Firebase credentials not found in alchemist-shared")
        
        # Check Firebase project ID
        project_id = get_project_id()
        if project_id:
            print(f"✅ Firebase project ID: {project_id}")
        else:
            print("⚠️  Firebase project ID not found in alchemist-shared")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check credentials: {e}")
        return False

def test_services():
    """Test that services can be initialized"""
    try:
        from alchemist_shared.database.firebase_client import FirebaseClient
        from alchemist_shared.config.base_settings import BaseSettings
        
        # Test Firebase client
        try:
            firebase_client = FirebaseClient()
            print("✅ Firebase client initialized successfully")
        except Exception as e:
            print(f"⚠️  Firebase client initialization failed: {e}")
        
        # Test BaseSettings
        try:
            settings = BaseSettings()
            openai_config = settings.get_openai_config()
            if openai_config:
                print("✅ BaseSettings and OpenAI config loaded successfully")
            else:
                print("⚠️  OpenAI config not available in BaseSettings")
        except Exception as e:
            print(f"⚠️  BaseSettings initialization failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test services: {e}")
        return False

def main():
    """Main setup verification"""
    print("🚀 Accountable AI Agent - Alchemist-Shared Setup Check")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the agent-template directory")
        sys.exit(1)
    
    # Check alchemist-shared availability
    if not check_alchemist_shared():
        print("\n📦 To install alchemist-shared:")
        print("pip install -e ../alchemist-shared")
        sys.exit(1)
    
    # Check credentials
    print("\n🔑 Checking credentials...")
    if not check_credentials():
        print("\n⚠️  Some credentials may not be configured in alchemist-shared")
        print("This is normal if you're setting up for the first time")
    
    # Test services
    print("\n🧪 Testing service initialization...")
    test_services()
    
    print("\n✅ Setup check complete!")
    print("\n🎯 To run the agent:")
    print("python main.py")
    
    print("\n📖 Configuration notes:")
    print("- Credentials are automatically loaded from alchemist-shared")
    print("- Set AGENT_ID in your .env file")
    print("- Adjust GNF and accountability settings as needed")

if __name__ == "__main__":
    main()