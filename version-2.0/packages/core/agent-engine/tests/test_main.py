"""
Tests for the Agent Engine main application.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestAgentEngineAPI:
    """Test cases for the Agent Engine API."""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        with patch('main.initialize_services'), \
             patch('alchemist_shared.database.FirebaseClient') as mock_firebase:
            
            # Mock Firebase client
            mock_firebase.return_value = MagicMock()
            
            # Import after patching
            from main import app
            return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "agent-engine"
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agent-engine"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])