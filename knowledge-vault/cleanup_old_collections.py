#!/usr/bin/env python3
"""
Cleanup script to delete old Firestore collections from the previous architecture.
This script will delete all documents from the knowledge_base_chunks collection.

Usage:
    python cleanup_old_collections.py [--dry-run]
    
Options:
    --dry-run    Show what would be deleted without actually deleting
"""

import os
import sys
import argparse
from typing import Dict, Any, List
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirestoreCleanup:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.init_firebase()
        
    def init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Get storage bucket name from environment variable
            storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET')
            
            if not storage_bucket:
                raise ValueError("Storage bucket name not specified. Set FIREBASE_STORAGE_BUCKET in your .env file.")
                
            if not firebase_admin._apps:
                firebase_admin.initialize_app(options={
                    'storageBucket': storage_bucket
                })
                
            self.db = firestore.client()
            print(f"✅ Connected to Firestore (Project: {self.db.project})")
            
        except Exception as e:
            print(f"❌ Error initializing Firebase: {str(e)}")
            sys.exit(1)
    
    def delete_collection_in_batches(self, collection_name: str, batch_size: int = 10) -> int:
        """
        Delete all documents in a collection in batches
        
        Args:
            collection_name: Name of the collection to delete
            batch_size: Number of documents to delete per batch
            
        Returns:
            Total number of documents deleted
        """
        collection_ref = self.db.collection(collection_name)
        total_deleted = 0
        
        print(f"\n🔍 Scanning collection: {collection_name}")
        
        while True:
            # Get a batch of documents
            docs = collection_ref.limit(batch_size).stream()
            doc_batch = list(docs)
            
            if not doc_batch:
                break
                
            print(f"📦 Found batch of {len(doc_batch)} documents")
            
            if not self.dry_run:
                # Delete the batch
                batch = self.db.batch()
                for doc in doc_batch:
                    batch.delete(doc.reference)
                    
                batch.commit()
                print(f"🗑️  Deleted {len(doc_batch)} documents")
            else:
                print(f"🔍 [DRY RUN] Would delete {len(doc_batch)} documents")
                
            total_deleted += len(doc_batch)
            
        return total_deleted
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get the total count of documents in a collection"""
        try:
            collection_ref = self.db.collection(collection_name)
            # Get all documents and count them (for smaller collections)
            docs = list(collection_ref.stream())
            return len(docs)
        except Exception as e:
            print(f"⚠️  Could not count documents in {collection_name}: {str(e)}")
            return 0
    
    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        try:
            collections = self.db.collections()
            return [col.id for col in collections]
        except Exception as e:
            print(f"⚠️  Could not list collections: {str(e)}")
            return []
    
    def cleanup_old_architecture(self):
        """Clean up collections from the old architecture"""
        print("🧹 Starting cleanup of old architecture collections...\n")
        
        # List all collections
        collections = self.list_collections()
        print(f"📚 Found collections: {', '.join(collections)}")
        
        old_collections = [
            'knowledge_base_chunks',  # Old chunks collection
        ]
        
        total_deleted = 0
        
        for collection_name in old_collections:
            if collection_name in collections:
                print(f"\n🎯 Processing collection: {collection_name}")
                
                # Get document count
                count = self.get_collection_count(collection_name)
                print(f"📊 Total documents in {collection_name}: {count}")
                
                if count > 0:
                    if not self.dry_run:
                        confirm = input(f"⚠️  Are you sure you want to delete {count} documents from '{collection_name}'? (y/N): ")
                        if confirm.lower() != 'y':
                            print("❌ Skipping collection")
                            continue
                    
                    # Delete the collection
                    deleted = self.delete_collection_in_batches(collection_name)
                    total_deleted += deleted
                    
                    if not self.dry_run:
                        print(f"✅ Deleted {deleted} documents from {collection_name}")
                    else:
                        print(f"🔍 [DRY RUN] Would delete {deleted} documents from {collection_name}")
                else:
                    print(f"ℹ️  Collection {collection_name} is already empty")
            else:
                print(f"ℹ️  Collection {collection_name} does not exist")
        
        print(f"\n🎉 Cleanup complete!")
        if not self.dry_run:
            print(f"📊 Total documents deleted: {total_deleted}")
        else:
            print(f"🔍 [DRY RUN] Total documents that would be deleted: {total_deleted}")
    
    def show_new_architecture_info(self):
        """Show information about the new architecture"""
        print("\n" + "="*60)
        print("📋 NEW ARCHITECTURE INFORMATION")
        print("="*60)
        print("The new architecture uses these collections:")
        print("• knowledge_base_files - File metadata")
        print("• knowledge_base_embeddings/{agent_id}/embeddings - Agent-specific embeddings")
        print("\nExample embedding collection paths:")
        print("• knowledge_base_embeddings/agent123/embeddings")
        print("• knowledge_base_embeddings/agent456/embeddings")
        print("\nThis provides:")
        print("✅ Better organization by agent")
        print("✅ Easier file-specific deletion")
        print("✅ Real-time updates via Firestore listeners")
        print("✅ Scalable architecture")

def main():
    parser = argparse.ArgumentParser(description='Clean up old Firestore collections')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    print("🧹 FIRESTORE CLEANUP TOOL")
    print("="*50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    else:
        print("⚠️  LIVE MODE - Changes will be permanent!")
    
    cleanup = FirestoreCleanup(dry_run=args.dry_run)
    
    try:
        cleanup.cleanup_old_architecture()
        cleanup.show_new_architecture_info()
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()