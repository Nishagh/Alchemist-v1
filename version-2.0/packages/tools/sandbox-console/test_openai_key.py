#!/usr/bin/env python3
"""
Test script to check which OpenAI API key is being used.
"""
import os
from alchemist_shared.config.base_settings import BaseSettings

def test_openai_key_sources():
    """Test what OpenAI API key sources are available."""
    print("OpenAI API Key Sources:")
    print("=" * 50)
    
    # Check environment variable directly
    env_key = os.getenv('OPENAI_API_KEY')
    print(f"Environment OPENAI_API_KEY: {'Set' if env_key else 'Not set'}")
    if env_key:
        print(f"  Value ending: ...{env_key[-4:] if len(env_key) >= 4 else env_key}")
    
    # Check alchemist-shared settings
    settings = BaseSettings()
    shared_key = settings.openai_api_key
    print(f"Alchemist-shared openai_api_key: {'Set' if shared_key else 'Not set'}")
    if shared_key:
        print(f"  Value ending: ...{shared_key[-4:] if len(shared_key) >= 4 else shared_key}")
    
    # Check if they match
    if env_key and shared_key:
        match = env_key == shared_key
        print(f"Keys match: {'✅' if match else '❌'}")
    
    print("\nRecommendation:")
    if shared_key:
        print("✅ Alchemist-shared has OpenAI key - sandbox console should use this")
    elif env_key:
        print("⚠️  Only environment variable set - need to configure alchemist-shared")
    else:
        print("❌ No OpenAI API key found in either source")

if __name__ == "__main__":
    test_openai_key_sources()