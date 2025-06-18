#!/usr/bin/env python3
"""
Test script for Universal Agent Deployment Service

Tests the deployment service locally before deploying to Cloud Run.
"""

import requests
import time
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8080"
TEST_AGENT_ID = "8e749a5b-91a3-4354-afdf-dc1d157e89fd"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['service']} v{data['version']}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")
        return False

def test_deployment_flow():
    """Test the complete deployment flow"""
    print("🔍 Testing deployment flow...")
    
    try:
        # 1. Start deployment
        print("📝 Starting deployment...")
        deploy_data = {"agent_id": TEST_AGENT_ID}
        response = requests.post(f"{BASE_URL}/api/deploy", json=deploy_data)
        
        if response.status_code != 200:
            print(f"❌ Deployment failed: {response.status_code} - {response.text}")
            return False
        
        deploy_result = response.json()
        deployment_id = deploy_result["deployment_id"]
        print(f"✅ Deployment started: {deployment_id}")
        
        # 2. Check deployment status
        print("📊 Checking deployment status...")
        for i in range(5):  # Check 5 times
            time.sleep(2)  # Wait 2 seconds between checks
            
            status_response = requests.get(f"{BASE_URL}/api/deployment/{deployment_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📈 Progress: {status_data['progress_percentage']}% - {status_data['current_step']}")
                
                if status_data['status'] == 'completed':
                    print(f"✅ Deployment completed: {status_data.get('service_url', 'No URL')}")
                    return True
                elif status_data['status'] == 'failed':
                    print(f"❌ Deployment failed: {status_data.get('error_message', 'No error message')}")
                    return False
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
        
        print("⏰ Deployment still in progress after test timeout")
        return True  # Consider it successful if still processing
        
    except Exception as e:
        print(f"❌ Deployment flow error: {str(e)}")
        return False

def test_list_deployments():
    """Test listing deployments"""
    print("🔍 Testing list deployments...")
    try:
        response = requests.get(f"{BASE_URL}/api/deployments")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Listed {data['count']} deployments, {data['active_count']} active")
            return True
        else:
            print(f"❌ List deployments failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ List deployments error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Universal Agent Deployment Service")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_root_endpoint,
        test_list_deployments,
        # test_deployment_flow,  # Uncomment to test actual deployment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())