#!/usr/bin/env python3
"""
Firestore Collection Migration Script

This script migrates data from the old Firestore structure to the new optimized structure.
It handles collection renaming, data consolidation, and field standardization.

Usage:
    python firestore_migration.py --dry-run  # Preview changes without applying
    python firestore_migration.py --execute  # Apply migrations
    python firestore_migration.py --rollback # Rollback to previous structure

Requirements:
    - Firebase Admin SDK credentials
    - Sufficient Firestore read/write permissions
    - Backup of existing data (recommended)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client as FirestoreClient, WriteBatch

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from alchemist_shared.constants.collections import Collections, DocumentFields, StatusValues, get_collection_mapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FirestoreMigration:
    """Handles Firestore data migration between old and new structures."""
    
    def __init__(self, credentials_path: Optional[str] = None, project_id: str = "alchemist-e69bb"):
        """Initialize migration with Firebase credentials."""
        self.project_id = project_id
        self.db: Optional[FirestoreClient] = None
        self.migration_stats = {
            'collections_migrated': 0,
            'documents_migrated': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Initialize Firebase
        self._initialize_firebase(credentials_path)
    
    def _initialize_firebase(self, credentials_path: Optional[str]):
        """Initialize Firebase Admin SDK."""
        try:
            if not firebase_admin._apps:
                if credentials_path and os.path.exists(credentials_path):
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred, {'projectId': self.project_id})
                else:
                    # Use default credentials
                    firebase_admin.initialize_app()
                
                logger.info(f"Firebase initialized for project: {self.project_id}")
            
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def validate_environment(self) -> bool:
        """Validate that the environment is ready for migration."""
        logger.info("Validating environment...")
        
        try:
            # Test Firestore connection
            collections = list(self.db.collections())
            logger.info(f"Found {len(collections)} collections in Firestore")
            
            # Check for required collections
            collection_names = [col.id for col in collections]
            old_collections = list(get_collection_mapping().keys())
            
            existing_old_collections = [col for col in old_collections if col in collection_names]
            logger.info(f"Found {len(existing_old_collections)} collections to migrate: {existing_old_collections}")
            
            if not existing_old_collections:
                logger.warning("No old collections found to migrate")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False
    
    def backup_collection(self, collection_name: str, backup_prefix: str = "backup_") -> bool:
        """Create a backup of a collection before migration."""
        logger.info(f"Creating backup of collection: {collection_name}")
        
        try:
            source_collection = self.db.collection(collection_name)
            backup_collection = self.db.collection(f"{backup_prefix}{collection_name}")
            
            # Get all documents from source collection
            docs = source_collection.stream()
            batch = self.db.batch()
            batch_count = 0
            
            for doc in docs:
                backup_doc_ref = backup_collection.document(doc.id)
                batch.set(backup_doc_ref, doc.to_dict())
                batch_count += 1
                
                # Commit batch every 500 operations (Firestore limit)
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
            
            # Commit remaining operations
            if batch_count > 0:
                batch.commit()
            
            logger.info(f"Backup created successfully: {backup_prefix}{collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup collection {collection_name}: {e}")
            return False
    
    def migrate_collection_rename(self, old_name: str, new_name: str, dry_run: bool = True) -> bool:
        """Migrate data from old collection name to new collection name."""
        logger.info(f"Migrating collection: {old_name} -> {new_name} (dry_run={dry_run})")
        
        try:
            old_collection = self.db.collection(old_name)
            docs = list(old_collection.stream())
            
            if not docs:
                logger.info(f"No documents found in {old_name}")
                return True
            
            logger.info(f"Found {len(docs)} documents to migrate from {old_name}")
            
            if dry_run:
                logger.info(f"DRY RUN: Would migrate {len(docs)} documents from {old_name} to {new_name}")
                return True
            
            # Perform actual migration
            new_collection = self.db.collection(new_name)
            batch = self.db.batch()
            batch_count = 0
            
            for doc in docs:
                data = doc.to_dict()
                
                # Apply field transformations based on collection type
                transformed_data = self._transform_document_fields(old_name, new_name, data)
                
                new_doc_ref = new_collection.document(doc.id)
                batch.set(new_doc_ref, transformed_data)
                batch_count += 1
                
                # Commit batch every 500 operations
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
            
            # Commit remaining operations
            if batch_count > 0:
                batch.commit()
            
            self.migration_stats['documents_migrated'] += len(docs)
            logger.info(f"Successfully migrated {len(docs)} documents from {old_name} to {new_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate collection {old_name} to {new_name}: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    def _transform_document_fields(self, old_collection: str, new_collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform document fields from old to new schema."""
        transformed = data.copy()
        
        # Apply collection-specific transformations
        if old_collection == Collections.Deprecated.ALCHEMIST_AGENTS and new_collection == Collections.AGENTS:
            # Agent collection transformations
            if 'userId' in transformed and DocumentFields.Agent.OWNER_ID not in transformed:
                transformed[DocumentFields.Agent.OWNER_ID] = transformed['userId']
        
        elif old_collection == Collections.Deprecated.DEV_CONVERSATIONS and new_collection == Collections.CONVERSATIONS:
            # Dev conversations transformation - mark as non-production
            transformed[DocumentFields.Conversation.IS_PRODUCTION] = False
            transformed[DocumentFields.Conversation.DEPLOYMENT_TYPE] = 'pre_deployment'
            
            # Rename fields to new schema
            if 'agentId' in transformed:
                transformed[DocumentFields.AGENT_ID] = transformed.pop('agentId')
            if 'userMessage' in transformed:
                transformed[DocumentFields.Conversation.MESSAGE_CONTENT] = transformed.pop('userMessage')
            if 'agentResponse' in transformed:
                transformed[DocumentFields.Conversation.AGENT_RESPONSE] = transformed.pop('agentResponse')
            if 'cost' in transformed:
                transformed[DocumentFields.Conversation.COST_USD] = transformed.pop('cost')
        
        elif old_collection == Collections.Deprecated.USER_CREDITS and new_collection == Collections.USER_ACCOUNTS:
            # User credits to user accounts transformation
            if 'balance' in transformed and isinstance(transformed['balance'], dict):
                balance = transformed.pop('balance')
                transformed[DocumentFields.Billing.CREDIT_BALANCE] = balance.get('total_credits', 0)
                transformed[DocumentFields.Billing.TOTAL_CREDITS_PURCHASED] = balance.get('base_credits', 0)
                transformed[DocumentFields.Billing.TOTAL_CREDITS_USED] = 0  # Will be calculated from transactions
            
            # Set default account status
            if DocumentFields.Billing.ACCOUNT_STATUS not in transformed:
                transformed[DocumentFields.Billing.ACCOUNT_STATUS] = StatusValues.Account.TRIAL
        
        elif old_collection == Collections.Deprecated.KNOWLEDGE_BASE_FILES and new_collection == Collections.KNOWLEDGE_FILES:
            # Knowledge base files transformation
            if 'filename' in transformed:
                transformed[DocumentFields.Knowledge.ORIGINAL_FILENAME] = transformed.pop('filename')
            if 'file_size' in transformed:
                transformed[DocumentFields.Knowledge.FILE_SIZE_BYTES] = transformed.pop('file_size')
            if 'upload_date' in transformed:
                transformed['uploaded_at'] = transformed.pop('upload_date')
        
        # Add standard timestamps if missing
        now = datetime.now(timezone.utc)
        if DocumentFields.CREATED_AT not in transformed and 'created_at' not in transformed:
            transformed[DocumentFields.CREATED_AT] = now
        if DocumentFields.UPDATED_AT not in transformed and 'updated_at' not in transformed:
            transformed[DocumentFields.UPDATED_AT] = now
        
        return transformed
    
    def consolidate_conversations(self, dry_run: bool = True) -> bool:
        """Consolidate dev_conversations and conversations into unified conversations collection."""
        logger.info(f"Consolidating conversations collections (dry_run={dry_run})")
        
        try:
            # Get production conversations
            prod_conversations = list(self.db.collection('conversations').stream())
            # Get dev conversations
            dev_conversations = list(self.db.collection(Collections.Deprecated.DEV_CONVERSATIONS).stream())
            
            total_conversations = len(prod_conversations) + len(dev_conversations)
            logger.info(f"Found {len(prod_conversations)} production + {len(dev_conversations)} dev conversations = {total_conversations} total")
            
            if dry_run:
                logger.info(f"DRY RUN: Would consolidate {total_conversations} conversations")
                return True
            
            # Create new unified conversations collection
            new_collection = self.db.collection(Collections.CONVERSATIONS)
            batch = self.db.batch()
            batch_count = 0
            
            # Migrate production conversations (mark as production)
            for doc in prod_conversations:
                data = doc.to_dict()
                data[DocumentFields.Conversation.IS_PRODUCTION] = True
                data[DocumentFields.Conversation.DEPLOYMENT_TYPE] = 'deployed'
                
                # Transform field names
                transformed_data = self._transform_document_fields('conversations', Collections.CONVERSATIONS, data)
                
                new_doc_ref = new_collection.document(doc.id)
                batch.set(new_doc_ref, transformed_data)
                batch_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
            
            # Migrate dev conversations (mark as non-production)
            for doc in dev_conversations:
                data = doc.to_dict()
                transformed_data = self._transform_document_fields(Collections.Deprecated.DEV_CONVERSATIONS, Collections.CONVERSATIONS, data)
                
                new_doc_ref = new_collection.document(f"dev_{doc.id}")  # Prefix to avoid conflicts
                batch.set(new_doc_ref, transformed_data)
                batch_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
            
            # Commit remaining operations
            if batch_count > 0:
                batch.commit()
            
            self.migration_stats['documents_migrated'] += total_conversations
            logger.info(f"Successfully consolidated {total_conversations} conversations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consolidate conversations: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    def run_migration(self, dry_run: bool = True, create_backups: bool = True) -> bool:
        """Run the complete migration process."""
        logger.info(f"Starting Firestore migration (dry_run={dry_run}, create_backups={create_backups})")
        
        # Validate environment
        if not self.validate_environment():
            logger.error("Environment validation failed")
            return False
        
        # Get collection mapping
        collection_mapping = get_collection_mapping()
        
        try:
            # Phase 1: Create backups
            if create_backups and not dry_run:
                logger.info("Phase 1: Creating backups...")
                for old_name in collection_mapping.keys():
                    if not self.backup_collection(old_name):
                        logger.error(f"Failed to backup {old_name}, aborting migration")
                        return False
                logger.info("Backup phase completed successfully")
            
            # Phase 2: Migrate collections
            logger.info("Phase 2: Migrating collections...")
            
            # Special handling for conversations consolidation
            if Collections.Deprecated.DEV_CONVERSATIONS in collection_mapping:
                if not self.consolidate_conversations(dry_run):
                    logger.error("Failed to consolidate conversations")
                    return False
            
            # Migrate other collections
            for old_name, new_name in collection_mapping.items():
                if old_name == Collections.Deprecated.DEV_CONVERSATIONS:
                    continue  # Already handled in consolidation
                
                if not self.migrate_collection_rename(old_name, new_name, dry_run):
                    logger.error(f"Failed to migrate {old_name} to {new_name}")
                    return False
                
                self.migration_stats['collections_migrated'] += 1
            
            # Phase 3: Validate migration
            if not dry_run:
                logger.info("Phase 3: Validating migration...")
                if not self._validate_migration():
                    logger.warning("Migration validation found issues")
                    self.migration_stats['warnings'] += 1
            
            # Print migration statistics
            self._print_migration_stats()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    def _validate_migration(self) -> bool:
        """Validate that the migration was successful."""
        logger.info("Validating migration results...")
        
        try:
            # Check that new collections exist and have data
            collection_mapping = get_collection_mapping()
            
            for old_name, new_name in collection_mapping.items():
                old_collection = self.db.collection(old_name)
                new_collection = self.db.collection(new_name)
                
                old_count = len(list(old_collection.limit(1).stream()))
                new_count = len(list(new_collection.limit(1).stream()))
                
                if old_count > 0 and new_count == 0:
                    logger.error(f"Migration validation failed: {new_name} is empty but {old_name} has data")
                    return False
                
                logger.info(f"Validation: {new_name} collection exists and has data")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False
    
    def _print_migration_stats(self):
        """Print migration statistics."""
        logger.info("=== Migration Statistics ===")
        logger.info(f"Collections migrated: {self.migration_stats['collections_migrated']}")
        logger.info(f"Documents migrated: {self.migration_stats['documents_migrated']}")
        logger.info(f"Errors: {self.migration_stats['errors']}")
        logger.info(f"Warnings: {self.migration_stats['warnings']}")
        logger.info("============================")
    
    def rollback_migration(self, backup_prefix: str = "backup_") -> bool:
        """Rollback migration by restoring from backups."""
        logger.info("Rolling back migration...")
        
        try:
            collection_mapping = get_collection_mapping()
            
            for old_name in collection_mapping.keys():
                backup_collection_name = f"{backup_prefix}{old_name}"
                
                # Check if backup exists
                backup_collection = self.db.collection(backup_collection_name)
                backup_docs = list(backup_collection.limit(1).stream())
                
                if not backup_docs:
                    logger.warning(f"No backup found for {old_name}, skipping rollback")
                    continue
                
                # Restore from backup
                logger.info(f"Restoring {old_name} from backup...")
                
                # Clear current collection
                current_collection = self.db.collection(old_name)
                current_docs = current_collection.stream()
                batch = self.db.batch()
                batch_count = 0
                
                for doc in current_docs:
                    batch.delete(doc.reference)
                    batch_count += 1
                    
                    if batch_count >= 500:
                        batch.commit()
                        batch = self.db.batch()
                        batch_count = 0
                
                if batch_count > 0:
                    batch.commit()
                
                # Restore from backup
                backup_docs = backup_collection.stream()
                batch = self.db.batch()
                batch_count = 0
                
                for doc in backup_docs:
                    restored_doc_ref = current_collection.document(doc.id)
                    batch.set(restored_doc_ref, doc.to_dict())
                    batch_count += 1
                    
                    if batch_count >= 500:
                        batch.commit()
                        batch = self.db.batch()
                        batch_count = 0
                
                if batch_count > 0:
                    batch.commit()
                
                logger.info(f"Successfully restored {old_name}")
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(description='Migrate Firestore collections to new structure')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying them')
    parser.add_argument('--execute', action='store_true', help='Execute the migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback to previous structure')
    parser.add_argument('--credentials', type=str, help='Path to Firebase credentials file')
    parser.add_argument('--project-id', type=str, default='alchemist-e69bb', help='Firebase project ID')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backups (not recommended)')
    
    args = parser.parse_args()
    
    if not any([args.dry_run, args.execute, args.rollback]):
        logger.error("Must specify one of --dry-run, --execute, or --rollback")
        parser.print_help()
        return 1
    
    if args.execute and args.rollback:
        logger.error("Cannot specify both --execute and --rollback")
        return 1
    
    try:
        # Initialize migration
        migration = FirestoreMigration(args.credentials, args.project_id)
        
        if args.rollback:
            success = migration.rollback_migration()
        else:
            success = migration.run_migration(
                dry_run=args.dry_run,
                create_backups=not args.no_backup
            )
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())