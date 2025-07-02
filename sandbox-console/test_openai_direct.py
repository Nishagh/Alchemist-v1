#!/usr/bin/env python3
"""
Test OpenAI API key directly to verify it works.
"""
import os
import openai
from alchemist_shared.config.base_settings import BaseSettings

def test_openai_api_direct():
    """Test OpenAI API key directly."""
    print("Testing OpenAI API Key Directly:")
    print("=" * 50)
    
    # Get key from alchemist-shared
    settings = BaseSettings()
    api_key = settings.openai_api_key
    
    if not api_key:
        print("❌ No OpenAI API key found in alchemist-shared settings")
        return
    
    print(f"Testing key ending: ...{api_key[-4:]}")
    
    try:
        # Set the API key
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test. Please respond with just 'OK'."}],
            max_tokens=10
        )
        
        print("✅ OpenAI API key is working!")
        print(f"Response: {response.choices[0].message.content}")
        
    except openai.RateLimitError as e:
        print("❌ Rate limit / quota error:")
        print(f"   {e}")
    except openai.AuthenticationError as e:
        print("❌ Authentication error:")
        print(f"   {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    test_openai_api_direct()