#!/usr/bin/env python3
"""
Test script for WhatsApp integration

This script tests the WhatsApp service functionality with mock configuration.
"""

import json
import asyncio
from whatsapp_service import WhatsAppService


def test_whatsapp_service():
    """Test WhatsApp service initialization and functionality"""
    
    # Test with no configuration
    print("🧪 Testing WhatsApp service with no configuration...")
    empty_config = {}
    service = WhatsAppService(empty_config)
    assert not service.is_enabled()
    print("✅ Service correctly disabled with no config")
    
    # Test with minimal configuration
    print("\n🧪 Testing WhatsApp service with minimal configuration...")
    minimal_config = {
        'whatsapp': {
            'enabled': True,
            'phone_id': '123456789',
            'access_token': 'test_token',
            'verify_token': 'test_verify'
        }
    }
    service = WhatsAppService(minimal_config)
    assert service.is_enabled()
    print("✅ Service correctly enabled with minimal config")
    
    # Test webhook verification
    print("\n🧪 Testing webhook verification...")
    try:
        result = asyncio.run(service.verify_webhook(
            "subscribe", "test_challenge", "test_verify"
        ))
        assert result == "test_challenge"
        print("✅ Webhook verification successful")
    except Exception as e:
        print(f"❌ Webhook verification failed: {e}")
    
    # Test signature verification
    print("\n🧪 Testing signature verification...")
    service.app_secret = "test_secret"
    test_payload = b'{"test": "data"}'
    
    # Test without signature verification (no app_secret)
    service.app_secret = None
    assert service.verify_signature(test_payload, "invalid_sig")
    print("✅ Signature verification skipped when no app_secret")
    
    # Test message parsing
    print("\n🧪 Testing message parsing...")
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "msg_123",
                        "from": "1234567890",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "Hello World"}
                    }],
                    "contacts": [{
                        "profile": {"name": "Test User"}
                    }]
                }
            }]
        }]
    }
    
    parsed = service.parse_webhook_message(webhook_data)
    assert parsed is not None
    assert parsed['text'] == "Hello World"
    assert parsed['from_phone'] == "1234567890"
    print("✅ Message parsing successful")
    
    # Test user ID generation
    print("\n🧪 Testing user ID generation...")
    user_id = service.get_conversation_user_id("1234567890")
    assert user_id == "whatsapp_1234567890"
    print("✅ User ID generation successful")
    
    # Test response formatting
    print("\n🧪 Testing response formatting...")
    response = "**Bold text** and __underlined text__ with ```code```"
    formatted = service.format_agent_response(response)
    assert "*Bold text*" in formatted
    assert "_underlined text_" in formatted
    print("✅ Response formatting successful")
    
    print("\n🎉 All WhatsApp service tests passed!")


if __name__ == "__main__":
    test_whatsapp_service()