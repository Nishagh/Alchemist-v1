"""
Tests for Agent Name Service functionality in StorageService.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from alchemist.services.storage_service import StorageService


class TestAgentNameService:
    """Test cases for agent name management functionality."""
    
    @pytest.fixture
    def storage_service(self):
        """Create StorageService instance with mocked Firestore."""
        with patch('alchemist.services.storage_service.get_firestore_client') as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db
            service = StorageService()
            service.db = mock_db
            return service, mock_db
    
    @pytest.mark.asyncio
    async def test_get_agent_name_success(self, storage_service):
        """Test successful agent name retrieval."""
        service, mock_db = storage_service
        
        # Mock Firestore response
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {'name': 'Test Agent', 'id': 'test-agent-id'}
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Test the method
        result = await service.get_agent_name('test-agent-id')
        
        # Assertions
        assert result == 'Test Agent'
        mock_db.collection.assert_called_with('agents')
        mock_db.collection.return_value.document.assert_called_with('test-agent-id')
    
    @pytest.mark.asyncio
    async def test_get_agent_name_not_found(self, storage_service):
        """Test agent name retrieval when agent doesn't exist."""
        service, mock_db = storage_service
        
        # Mock Firestore response for non-existent agent
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Test the method
        result = await service.get_agent_name('non-existent-agent')
        
        # Assertions
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_agent_name_exception(self, storage_service):
        """Test agent name retrieval with database exception."""
        service, mock_db = storage_service
        
        # Mock Firestore to raise an exception
        mock_db.collection.return_value.document.return_value.get.side_effect = Exception("Database error")
        
        # Test the method
        result = await service.get_agent_name('test-agent-id')
        
        # Assertions
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_agent_name_success(self, storage_service):
        """Test successful agent name update."""
        service, mock_db = storage_service
        
        # Mock existing agent
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock update method
        mock_update = MagicMock()
        mock_db.collection.return_value.document.return_value.update = mock_update
        
        # Test the method
        result = await service.update_agent_name('test-agent-id', 'New Agent Name')
        
        # Assertions
        assert result is True
        mock_update.assert_called_once()
        
        # Check that update was called with correct data
        call_args = mock_update.call_args[0][0]
        assert call_args['name'] == 'New Agent Name'
        assert 'updated_at' in call_args
    
    @pytest.mark.asyncio
    async def test_update_agent_name_not_found(self, storage_service):
        """Test agent name update when agent doesn't exist."""
        service, mock_db = storage_service
        
        # Mock non-existent agent
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Test the method
        result = await service.update_agent_name('non-existent-agent', 'New Name')
        
        # Assertions
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_agent_name_invalid_input(self, storage_service):
        """Test agent name update with invalid inputs."""
        service, mock_db = storage_service
        
        # Test empty agent_id
        result = await service.update_agent_name('', 'New Name')
        assert result is False
        
        # Test empty name
        result = await service.update_agent_name('test-agent-id', '')
        assert result is False
        
        # Test non-string name
        result = await service.update_agent_name('test-agent-id', 123)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_agent_name_exception(self, storage_service):
        """Test agent name update with database exception."""
        service, mock_db = storage_service
        
        # Mock existing agent but update fails
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value.update.side_effect = Exception("Database error")
        
        # Test the method
        result = await service.update_agent_name('test-agent-id', 'New Name')
        
        # Assertions
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])