"""
Test health endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_firebase():
    """Mock Firebase service"""
    mock_firebase = Mock()
    mock_firebase._initialized = True
    return mock_firebase


def test_health_endpoint(client, mock_firebase):
    """Test health check endpoint"""
    with patch.object(app.state, 'firebase', mock_firebase):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "Alchemist Billing Service"
        assert "timestamp" in data
        assert "dependencies" in data


def test_readiness_endpoint(client, mock_firebase):
    """Test readiness check endpoint"""
    # Mock collections method
    mock_firebase.db.collections.return_value = []
    
    with patch.object(app.state, 'firebase', mock_firebase):
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ready"
        assert "timestamp" in data


def test_liveness_endpoint(client):
    """Test liveness check endpoint"""
    response = client.get("/api/v1/health/live")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_endpoint_not_ready(client):
    """Test readiness check when Firebase not initialized"""
    mock_firebase = Mock()
    mock_firebase._initialized = False
    
    with patch.object(app.state, 'firebase', mock_firebase):
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["detail"]["status"] == "not_ready"