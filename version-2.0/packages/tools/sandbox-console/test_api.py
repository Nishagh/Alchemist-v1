#!/usr/bin/env python3
"""
Simple test script to verify the sandbox console API endpoints are working.
"""
import requests
import json
import os

def test_cors():
    """Test CORS functionality"""
    try:
        response = requests.get("http://localhost:8080/cors-test")
        print(f"CORS Test: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"CORS Test Failed: {e}")
        return False

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8080/health")
        print(f"Health Check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return False

def test_create_conversation():
    """Test conversation creation"""
    try:
        # Use a test agent ID
        test_agent_id = "test-agent-123"
        
        response = requests.post(
            "http://localhost:8080/api/agent/create_conversation",
            json={"agent_id": test_agent_id},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Create Conversation: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "success" and "conversation_id" in data
        return False
    except Exception as e:
        print(f"Create Conversation Failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Sandbox Console API Endpoints...")
    print("="*50)
    
    tests = [
        ("CORS Test", test_cors),
        ("Health Check", test_health),
        ("Create Conversation", test_create_conversation)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        results[test_name] = test_func()
    
    print("\n" + "="*50)
    print("Test Results Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")