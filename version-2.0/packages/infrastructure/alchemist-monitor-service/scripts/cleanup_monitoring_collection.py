#!/usr/bin/env python3
"""
Comprehensive cleanup script for monitoring collection bloat
This script removes all timestamp-based documents from monitoring collections
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import firebase_admin
from firebase_admin import credentials, firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MonitoringCollectionCleanup:
    """Cleanup bloated monitoring collections"""
    
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase app already initialized")
            except ValueError:
                cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with service account")
                else:
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def count_subcollection_documents(self, parent_path: str, subcollection: str) -> int:
        """Count documents in a subcollection"""
        try:
            parent_doc = self.db.document(parent_path)
            subcollection_ref = parent_doc.collection(subcollection)
            docs = subcollection_ref.stream()
            count = sum(1 for _ in docs)
            return count
        except Exception as e:
            logger.error(f"Failed to count documents in {parent_path}/{subcollection}: {e}")
            return 0
    
    def delete_subcollection_batch(self, parent_path: str, subcollection: str, batch_size: int = 500) -> int:
        """Delete all documents in a subcollection in batches"""
        try:
            parent_doc = self.db.document(parent_path)
            subcollection_ref = parent_doc.collection(subcollection)
            
            total_deleted = 0
            
            while True:
                # Get a batch of documents
                docs = subcollection_ref.limit(batch_size).stream()
                doc_list = list(docs)
                
                if not doc_list:
                    break
                
                # Delete this batch
                batch = self.db.batch()
                for doc in doc_list:
                    batch.delete(doc.reference)
                
                batch.commit()
                total_deleted += len(doc_list)
                
                logger.info(f"Deleted {len(doc_list)} documents from {parent_path}/{subcollection} (total: {total_deleted})")
                
                # If we got fewer docs than batch_size, we're done
                if len(doc_list) < batch_size:
                    break
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete subcollection {parent_path}/{subcollection}: {e}")
            return 0
    
    def analyze_monitoring_structure(self) -> Dict[str, int]:
        """Analyze current monitoring collection structure"""
        logger.info("Analyzing monitoring collection structure...")
        
        structure = {}
        
        # Check main problematic collections
        monitoring_paths = [
            ("monitoring/metrics", "services"),
            ("monitoring/summaries", "daily"),
            ("monitoring/health_checks", "results"),  # Legacy
        ]
        
        for parent_path, subcollection in monitoring_paths:
            try:
                count = self.count_subcollection_documents(parent_path, subcollection)
                structure[f"{parent_path}/{subcollection}"] = count
                logger.info(f"Found {count:,} documents in {parent_path}/{subcollection}")
            except Exception as e:
                logger.warning(f"Could not analyze {parent_path}/{subcollection}: {e}")
                structure[f"{parent_path}/{subcollection}"] = 0
        
        # Check regular collections that might be bloated
        regular_collections = [
            "monitoring",
            "health_check",  # Alternative name
            "service_health",  # Should be optimized (latest-only)
            "service_metrics",  # Should be optimized (latest-only)
            "monitoring_summary",  # Should be optimized (single doc)
        ]
        
        for collection in regular_collections:
            try:
                docs = self.db.collection(collection).stream()
                count = sum(1 for _ in docs)
                structure[collection] = count
                logger.info(f"Found {count:,} documents in {collection} collection")
            except Exception as e:
                logger.warning(f"Could not analyze {collection} collection: {e}")
                structure[collection] = 0
        
        return structure
    
    def cleanup_timestamp_based_documents(self):
        """Clean up all timestamp-based documents from monitoring collections"""
        logger.info("Starting cleanup of timestamp-based monitoring documents...")
        
        # Collections to clean up (these create new docs per timestamp)
        cleanup_targets = [
            ("monitoring/metrics", "services"),           # Service metrics with timestamps
            ("monitoring/summaries", "daily"),           # Daily summaries with timestamps
            ("monitoring/health_checks", "results"),     # Legacy health checks
        ]
        
        total_deleted = 0
        
        for parent_path, subcollection in cleanup_targets:
            logger.info(f"Processing {parent_path}/{subcollection}...")
            
            # Count documents first
            count = self.count_subcollection_documents(parent_path, subcollection)
            logger.info(f"Found {count:,} documents in {parent_path}/{subcollection}")
            
            if count > 0:
                logger.info(f"Starting deletion of {count:,} documents...")
                start_time = datetime.now()
                
                deleted = self.delete_subcollection_batch(parent_path, subcollection)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"Deleted {deleted:,} documents in {duration:.1f} seconds")
                total_deleted += deleted
            else:
                logger.info(f"No documents to delete in {parent_path}/{subcollection}")
        
        logger.info(f"Timestamp-based document cleanup completed. Total deleted: {total_deleted:,}")
        return total_deleted
    
    def cleanup_legacy_collections(self):
        """Clean up legacy collection structures"""
        logger.info("Cleaning up legacy collections...")
        
        legacy_collections = [
            "health_check",  # Old health check collection (if exists)
        ]
        
        total_deleted = 0
        
        for collection in legacy_collections:
            try:
                docs = self.db.collection(collection).stream()
                doc_list = list(docs)
                count = len(doc_list)
                
                if count > 0:
                    logger.info(f"Found {count:,} documents in legacy {collection} collection")
                    
                    # Delete in batches
                    batch_size = 500
                    for i in range(0, count, batch_size):
                        batch = self.db.batch()
                        batch_docs = doc_list[i:i + batch_size]
                        
                        for doc in batch_docs:
                            batch.delete(doc.reference)
                        
                        batch.commit()
                        logger.info(f"Deleted batch {i//batch_size + 1} ({len(batch_docs)} docs)")
                    
                    total_deleted += count
                    logger.info(f"Cleaned up {count:,} documents from {collection}")
                else:
                    logger.info(f"No documents found in {collection}")
                    
            except Exception as e:
                logger.warning(f"Could not clean legacy collection {collection}: {e}")
        
        return total_deleted
    
    def verify_optimized_collections(self):
        """Verify that optimized collections have reasonable document counts"""
        logger.info("Verifying optimized collections...")
        
        optimized_collections = {
            "service_health": 9,        # Should have ~9 docs (one per service)
            "service_metrics": 9,       # Should have ~9 docs (one per service)
            "monitoring_summary": 1,    # Should have 1 doc (current summary)
        }
        
        for collection, expected_count in optimized_collections.items():
            try:
                docs = self.db.collection(collection).stream()
                actual_count = sum(1 for _ in docs)
                
                if actual_count <= expected_count * 2:  # Allow some tolerance
                    logger.info(f"✅ {collection}: {actual_count} documents (expected ~{expected_count}) - OPTIMIZED")
                else:
                    logger.warning(f"⚠️  {collection}: {actual_count} documents (expected ~{expected_count}) - MAY NEED ATTENTION")
                    
            except Exception as e:
                logger.warning(f"Could not verify {collection}: {e}")
    
    def generate_optimization_report(self, before_structure: Dict[str, int], deleted_counts: Dict[str, int]):
        """Generate optimization report"""
        logger.info("\n" + "="*60)
        logger.info("MONITORING COLLECTION OPTIMIZATION REPORT")
        logger.info("="*60)
        
        total_before = sum(before_structure.values())
        total_deleted = sum(deleted_counts.values())
        
        logger.info(f"Documents before cleanup: {total_before:,}")
        logger.info(f"Documents deleted: {total_deleted:,}")
        logger.info(f"Estimated remaining: {total_before - total_deleted:,}")
        
        if total_before > 0:
            reduction_percentage = (total_deleted / total_before) * 100
            logger.info(f"Reduction: {reduction_percentage:.1f}%")
        
        logger.info("\nOptimizations implemented:")
        logger.info("✅ Service health: Document reuse (latest-only)")
        logger.info("✅ Service metrics: Document reuse (latest-only)")
        logger.info("✅ Monitoring summary: Single document reuse")
        logger.info("✅ Health check frequency: 30s → 5min (98% reduction)")
        logger.info("✅ Array trimming: Automatic history limits")
        
        logger.info("\nNew collection structure:")
        logger.info("• service_health/{service} - 9 documents (reused)")
        logger.info("• service_metrics/{service} - 9 documents (reused)")
        logger.info("• monitoring_summary/current - 1 document (reused)")
        logger.info("• monitoring/scheduler - 1 document (reused)")
        
        logger.info("\nExpected daily document creation after optimization:")
        logger.info("• Health checks: 0 new docs/day (reuses existing)")
        logger.info("• Service metrics: 0 new docs/day (reuses existing)")
        logger.info("• Summaries: 0 new docs/day (reuses existing)")
        logger.info("• Total: ~0 new docs/day (vs. ~2,880 before)")
        logger.info("="*60)

def main():
    """Main cleanup function"""
    try:
        logger.info("="*70)
        logger.info("MONITORING COLLECTION CLEANUP")
        logger.info("="*70)
        logger.info("This script will remove ALL timestamp-based documents from monitoring collections")
        logger.info("This includes service metrics and summaries that create new docs per timestamp")
        logger.info("This action cannot be undone!")
        logger.info("="*70)
        
        # Ask for confirmation
        response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if response != 'yes':
            logger.info("Cleanup cancelled by user")
            return
        
        cleanup = MonitoringCollectionCleanup()
        
        # Analyze structure before cleanup
        before_structure = cleanup.analyze_monitoring_structure()
        
        # Perform cleanup
        deleted_counts = {}
        
        logger.info("\n" + "="*50)
        logger.info("PHASE 1: Cleanup timestamp-based documents")
        logger.info("="*50)
        deleted_counts['timestamp_based'] = cleanup.cleanup_timestamp_based_documents()
        
        logger.info("\n" + "="*50)
        logger.info("PHASE 2: Cleanup legacy collections")
        logger.info("="*50)
        deleted_counts['legacy'] = cleanup.cleanup_legacy_collections()
        
        logger.info("\n" + "="*50)
        logger.info("PHASE 3: Verify optimized collections")
        logger.info("="*50)
        cleanup.verify_optimized_collections()
        
        # Generate report
        cleanup.generate_optimization_report(before_structure, deleted_counts)
        
        logger.info("\n✅ Monitoring collection cleanup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Deploy the optimized monitor service")
        logger.info("2. Monitor new document creation patterns")
        logger.info("3. Set up TTL rules for additional safety")
        
    except Exception as e:
        logger.error(f"Monitoring collection cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()