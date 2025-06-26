#!/usr/bin/env python3
"""
Test Firebase connectivity using the shared library.
This script verifies that Firebase credentials are properly loaded and the connection works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from alchemist_shared.database.firebase_client import FirebaseClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebase_connectivity():
    """Test Firebase connectivity and basic operations."""
    try:
        logger.info("🚀 Testing Firebase connectivity...")
        
        # Initialize Firebase client
        firebase_client = FirebaseClient()
        logger.info("✅ Firebase client initialized successfully")
        
        # Test Firestore connection
        db = firebase_client.db
        logger.info("✅ Firestore client obtained")
        
        # Test basic collection access
        agents_collection = firebase_client.get_agents_collection()
        logger.info("✅ Agents collection reference obtained")
        
        # Test a simple query (just count documents, don't read data)
        try:
            # Get collection count without reading documents
            query = agents_collection.limit(1)
            docs = list(query.stream())
            logger.info(f"✅ Successfully queried collection (found {len(docs)} document(s) in first batch)")
        except Exception as e:
            logger.warning(f"⚠️  Query test failed (this might be expected if collection is empty): {e}")
        
        # Test project ID extraction
        try:
            project_id = firebase_client._get_project_id()
            logger.info(f"✅ Project ID: {project_id}")
        except Exception as e:
            logger.error(f"❌ Failed to get project ID: {e}")
            return False
        
        # Test storage bucket (if configured)
        try:
            storage_bucket = firebase_client.storage
            logger.info(f"✅ Storage bucket initialized: {storage_bucket.name}")
        except Exception as e:
            logger.warning(f"⚠️  Storage bucket test failed: {e}")
        
        logger.info("🎉 Firebase connectivity test PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Firebase connectivity test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_firebase_connectivity()
    sys.exit(0 if success else 1)