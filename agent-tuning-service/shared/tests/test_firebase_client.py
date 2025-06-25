"""
Tests for Firebase client functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from alchemist_shared.database.firebase_client import FirebaseClient


class TestFirebaseClient:
    """Test cases for Firebase client."""
    
    def test_singleton_pattern(self):
        """Test that FirebaseClient follows singleton pattern."""
        with patch('alchemist_shared.database.firebase_client.firebase_admin'):
            client1 = FirebaseClient()
            client2 = FirebaseClient()
            
            assert client1 is client2
    
    @patch('alchemist_shared.database.firebase_client.firebase_admin')
    @patch('alchemist_shared.database.firebase_client.firestore')
    def test_initialization_cloud_environment(self, mock_firestore, mock_firebase_admin):
        """Test Firebase initialization in cloud environment."""
        with patch('alchemist_shared.database.firebase_client.os.environ.get') as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                'K_SERVICE': 'test-service',
                'GOOGLE_CLOUD_PROJECT': 'test-project'
            }.get(key, default)
            
            mock_app = MagicMock()
            mock_firebase_admin.initialize_app.return_value = mock_app
            mock_firestore.client.return_value = MagicMock()
            
            # Reset singleton
            FirebaseClient._instance = None
            
            client = FirebaseClient()
            
            # Should initialize without credentials file
            mock_firebase_admin.initialize_app.assert_called_once()
            mock_firestore.client.assert_called_once_with(mock_app)
    
    @patch('alchemist_shared.database.firebase_client.firebase_admin')
    @patch('alchemist_shared.database.firebase_client.firestore')
    @patch('alchemist_shared.database.firebase_client.os.path.exists')
    def test_initialization_local_environment(self, mock_exists, mock_firestore, mock_firebase_admin):
        """Test Firebase initialization in local environment."""
        with patch('alchemist_shared.database.firebase_client.os.environ.get') as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/creds.json'
            }.get(key, default)
            
            mock_exists.return_value = True
            mock_app = MagicMock()
            mock_firebase_admin.initialize_app.return_value = mock_app
            mock_firestore.client.return_value = MagicMock()
            
            # Reset singleton
            FirebaseClient._instance = None
            
            client = FirebaseClient()
            
            # Should initialize with credentials file
            mock_firebase_admin.initialize_app.assert_called_once()
            mock_firestore.client.assert_called_once_with(mock_app)
    
    def test_get_collection(self):
        """Test getting a Firestore collection."""
        with patch('alchemist_shared.database.firebase_client.firebase_admin'), \
             patch('alchemist_shared.database.firebase_client.firestore'):
            
            # Reset singleton
            FirebaseClient._instance = None
            
            client = FirebaseClient()
            mock_db = MagicMock()
            client._firestore_client = mock_db
            
            collection = client.get_collection('test_collection')
            
            mock_db.collection.assert_called_once_with('test_collection')
    
    def test_get_document(self):
        """Test getting a Firestore document."""
        with patch('alchemist_shared.database.firebase_client.firebase_admin'), \
             patch('alchemist_shared.database.firebase_client.firestore'):
            
            # Reset singleton
            FirebaseClient._instance = None
            
            client = FirebaseClient()
            mock_db = MagicMock()
            client._firestore_client = mock_db
            
            document = client.get_document('test_collection', 'test_doc')
            
            mock_db.collection.assert_called_once_with('test_collection')
            mock_db.collection().document.assert_called_once_with('test_doc')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])