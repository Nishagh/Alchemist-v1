#!/usr/bin/env python3
"""
Emergency cleanup script for removing 50K+ health check documents
This script removes all documents from the old monitoring/health_checks/results collection
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import List

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import firebase_admin
from firebase_admin import credentials, firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmergencyCleanup:
    """Emergency cleanup for health check documents"""
    
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            # Check if app already exists
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase app already initialized")
            except ValueError:
                # Initialize new app
                cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with service account")
                else:
                    # Try default credentials for Cloud Run
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def count_documents(self, collection_path: str) -> int:
        """Count documents in a collection"""
        try:
            if '/' in collection_path:
                # Handle subcollection path like monitoring/health_checks/results
                parts = collection_path.split('/')
                if len(parts) == 3:
                    collection_ref = (self.db.collection(parts[0])
                                    .document(parts[1])
                                    .collection(parts[2]))
                else:
                    collection_ref = self.db.collection(collection_path)
            else:
                collection_ref = self.db.collection(collection_path)
            
            # Get count using aggregation (more efficient than streaming all docs)
            try:
                from google.cloud.firestore_v1.aggregation import AggregationQuery
                query = collection_ref.select([])
                agg_query = AggregationQuery(query)
                agg_result = agg_query.count().get()
                return agg_result[0][0].value
            except:
                # Fallback to streaming and counting
                docs = collection_ref.stream()
                count = sum(1 for _ in docs)
                return count
                
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_path}: {e}")
            return 0
    
    def delete_collection_batch(self, collection_path: str, batch_size: int = 500) -> int:
        """Delete all documents in a collection in batches"""
        try:
            if '/' in collection_path:
                # Handle subcollection path
                parts = collection_path.split('/')
                if len(parts) == 3:
                    collection_ref = (self.db.collection(parts[0])
                                    .document(parts[1])
                                    .collection(parts[2]))
                else:
                    collection_ref = self.db.collection(collection_path)
            else:
                collection_ref = self.db.collection(collection_path)
            
            total_deleted = 0
            
            while True:
                # Get a batch of documents
                docs = collection_ref.limit(batch_size).stream()
                doc_list = list(docs)
                
                if not doc_list:
                    break
                
                # Delete this batch
                batch = self.db.batch()
                for doc in doc_list:
                    batch.delete(doc.reference)
                
                batch.commit()
                total_deleted += len(doc_list)
                
                logger.info(f"Deleted {len(doc_list)} documents (total: {total_deleted})")
                
                # If we got fewer docs than batch_size, we're done
                if len(doc_list) < batch_size:
                    break
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_path}: {e}")
            return 0
    
    def cleanup_old_health_checks(self):
        """Clean up the old health_check collection structure"""
        logger.info("Starting emergency cleanup of health check documents...")
        
        # Collections to clean up
        cleanup_targets = [
            "monitoring/health_checks/results",  # Main problematic collection
            "health_check",  # Alternative collection name that might exist
        ]
        
        total_deleted = 0
        
        for target in cleanup_targets:
            logger.info(f"Checking collection: {target}")
            
            # Count documents first
            count = self.count_documents(target)
            logger.info(f"Found {count:,} documents in {target}")
            
            if count > 0:
                logger.info(f"Starting deletion of {count:,} documents from {target}...")
                start_time = datetime.now()
                
                deleted = self.delete_collection_batch(target)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"Deleted {deleted:,} documents from {target} in {duration:.1f} seconds")
                total_deleted += deleted
        
        logger.info(f"Emergency cleanup completed. Total documents deleted: {total_deleted:,}")
        
        # Verify cleanup
        logger.info("Verifying cleanup...")
        for target in cleanup_targets:
            remaining = self.count_documents(target)
            logger.info(f"Remaining documents in {target}: {remaining:,}")
    
    def setup_ttl_rules(self):
        """Set up TTL rules for automatic cleanup (manual step - requires console)"""
        logger.info("\n" + "="*50)
        logger.info("MANUAL STEP REQUIRED: Set up TTL rules")
        logger.info("="*50)
        logger.info("To prevent future document explosion, set up TTL rules in Firebase Console:")
        logger.info("1. Go to Firebase Console -> Firestore -> Indexes")
        logger.info("2. Create a TTL policy for collection 'service_health'")
        logger.info("3. Set TTL field to 'updated_at' with expiration of 7 days")
        logger.info("4. This will automatically delete documents older than 7 days")
        logger.info("="*50)

def main():
    """Main cleanup function"""
    try:
        logger.info("="*60)
        logger.info("EMERGENCY FIRESTORE CLEANUP")
        logger.info("="*60)
        logger.info("This script will remove ALL documents from problematic collections")
        logger.info("This action cannot be undone!")
        logger.info("="*60)
        
        # Ask for confirmation
        response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if response != 'yes':
            logger.info("Cleanup cancelled by user")
            return
        
        cleanup = EmergencyCleanup()
        cleanup.cleanup_old_health_checks()
        cleanup.setup_ttl_rules()
        
        logger.info("\n✅ Emergency cleanup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Deploy the optimized monitor service")
        logger.info("2. Set up TTL rules as shown above")
        logger.info("3. Monitor new document creation patterns")
        
    except Exception as e:
        logger.error(f"Emergency cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()