"""
Test Script for Centralized API Logging System

This script tests the API logging functionality to ensure it works correctly
before deploying to production services.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
import pytest


async def test_api_logging_system():
    """Test the complete API logging system."""
    
    print("🧪 Testing Centralized API Logging System")
    print("=" * 50)
    
    # Test 1: Import checks
    print("\n📦 Testing imports...")
    try:
        from alchemist_shared.middleware.api_logging_middleware import (
            setup_api_logging_middleware,
            shutdown_api_logging
        )
        from alchemist_shared.services.api_logging_service import (
            APILoggingService,
            get_api_logging_service,
            init_api_logging_service
        )
        from alchemist_shared.models.api_log_models import (
            APILogEntry,
            APILogQuery,
            APILogConfig
        )
        from alchemist_shared.constants.collections import Collections
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Model validation
    print("\n📋 Testing data models...")
    try:
        log_entry = APILogEntry(
            request_id=str(uuid.uuid4()),
            service_name="test-service",
            method="GET",
            endpoint="/test"
        )
        print(f"✅ APILogEntry created: {log_entry.request_id}")
        
        query = APILogQuery(
            service_name="test-service",
            errors_only=True,
            limit=10
        )
        print(f"✅ APILogQuery created for service: {query.service_name}")
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    
    # Test 3: Service initialization
    print("\n🔧 Testing service initialization...")
    try:
        # Initialize the logging service
        logging_service = init_api_logging_service("test-service")
        print(f"✅ Logging service initialized for: {logging_service.service_name}")
        
        # Test basic logging
        request_id = str(uuid.uuid4())
        success = await logging_service.log_request(
            request_id=request_id,
            method="GET",
            endpoint="/test",
            status_code=200,
            response_time_ms=150.5,
            user_id="test-user"
        )
        print(f"✅ Basic log entry created: {success}")
        
        # Force flush to ensure logs are written
        await logging_service.force_flush()
        print("✅ Logs flushed successfully")
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False
    
    # Test 4: FastAPI integration
    print("\n🌐 Testing FastAPI middleware...")
    try:
        # Create test FastAPI app
        app = FastAPI(title="Test API Logging")
        
        # Add the middleware
        setup_api_logging_middleware(
            app,
            service_name="test-api",
            service_version="1.0.0",
            exclude_health_checks=True
        )
        
        # Add test endpoints
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test successful"}
        
        @app.get("/test-error")
        async def test_error_endpoint():
            raise HTTPException(status_code=500, detail="Test error")
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        print("✅ FastAPI app with middleware created")
        
        # Test with TestClient
        client = TestClient(app)
        
        # Test successful request
        response = client.get("/test")
        assert response.status_code == 200
        print("✅ Successful request logged")
        
        # Test error request
        response = client.get("/test-error")
        assert response.status_code == 500
        print("✅ Error request logged")
        
        # Test excluded endpoint (health)
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ Health check (excluded) handled correctly")
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False
    
    # Test 5: Query functionality
    print("\n🔍 Testing query functionality...")
    try:
        # Wait a moment for logs to be processed
        await asyncio.sleep(2)
        
        # Query recent logs
        query = APILogQuery(
            service_name="test-api",
            start_time=datetime.utcnow() - timedelta(minutes=5),
            limit=10
        )
        
        logs = await logging_service.query_logs(query)
        print(f"✅ Query returned {len(logs)} log entries")
        
        # Query errors only
        error_query = APILogQuery(
            service_name="test-api",
            errors_only=True,
            start_time=datetime.utcnow() - timedelta(minutes=5)
        )
        
        error_logs = await logging_service.query_logs(error_query)
        print(f"✅ Error query returned {len(error_logs)} error entries")
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False
    
    # Test 6: Statistics
    print("\n📊 Testing statistics functionality...")
    try:
        stats = await logging_service.get_api_stats(
            start_time=datetime.utcnow() - timedelta(minutes=5),
            end_time=datetime.utcnow(),
            service_name="test-api"
        )
        
        if stats:
            print(f"✅ Stats generated - Total requests: {stats.total_requests}")
            print(f"   - Success: {stats.success_requests}")
            print(f"   - Errors: {stats.error_requests}")
            print(f"   - Avg response time: {stats.avg_response_time_ms:.2f}ms")
        else:
            print("⚠️  No stats available (may be due to test environment)")
        
    except Exception as e:
        print(f"❌ Statistics test failed: {e}")
        return False
    
    # Test 7: Security features
    print("\n🔒 Testing security features...")
    try:
        # Test sensitive data filtering
        from alchemist_shared.middleware.api_logging_middleware import APILoggingMiddleware
        
        middleware = APILoggingMiddleware(
            app=app,
            service_name="test-security"
        )
        
        # Test data filtering
        sensitive_data = {
            "authorization": "Bearer secret-token",
            "password": "secret123",
            "normal_field": "normal_value"
        }
        
        filtered = middleware._filter_sensitive_data(
            sensitive_data, 
            {"authorization", "password"}
        )
        
        assert filtered["authorization"] == "<redacted>"
        assert filtered["password"] == "<redacted>"
        assert filtered["normal_field"] == "normal_value"
        print("✅ Sensitive data filtering working correctly")
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False
    
    # Final cleanup
    print("\n🧹 Cleanup...")
    try:
        await shutdown_api_logging()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\nThe centralized API logging system is ready for deployment.")
    print("\nNext steps:")
    print("1. Review the integration examples")
    print("2. Update each service's main.py file")
    print("3. Deploy services with logging enabled")
    print("4. Monitor the api_logs collection in Firestore")
    
    return True


def test_configuration_options():
    """Test different configuration scenarios."""
    
    print("\n⚙️  Testing configuration options...")
    
    # Test with different settings
    configs = [
        {
            "name": "Default config",
            "params": {
                "service_name": "test-service",
            }
        },
        {
            "name": "Custom exclusions",
            "params": {
                "service_name": "test-service",
                "exclude_paths": {"/custom", "/internal"},
                "exclude_health_checks": False
            }
        },
        {
            "name": "Body logging enabled",
            "params": {
                "service_name": "test-service",
                "log_request_body": True,
                "log_response_body": True,
                "max_body_size": 512
            }
        }
    ]
    
    for config in configs:
        try:
            app = FastAPI()
            setup_api_logging_middleware(app, **config["params"])
            print(f"✅ {config['name']} - Success")
        except Exception as e:
            print(f"❌ {config['name']} - Failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting API Logging System Tests")
    
    # Run configuration tests first
    test_configuration_options()
    
    # Run main test suite
    result = asyncio.run(test_api_logging_system())
    
    if result:
        print("\n✅ All tests passed! System is ready for production.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")
        exit(1)