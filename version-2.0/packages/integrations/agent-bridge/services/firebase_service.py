"""
Firebase/Firestore integration service for WhatsApp BSP backend
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1.base_query import FieldFilter

from models.account_models import ManagedAccount
from models.webhook_models import WebhookLog
from config.settings import get_settings


class FirebaseService:
    """Service for Firebase/Firestore operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self._db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            try:
                firebase_admin.get_app()
                self._db = firestore.client()
                return
            except ValueError:
                # Firebase not initialized yet
                pass
            
            # Initialize Firebase
            credentials_path = self.settings.firebase_credentials_path
            
            if os.path.exists(credentials_path):
                # Use service account credentials file
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': self.settings.firebase_project_id
                })
            else:
                # Use default credentials (for Cloud Run deployment)
                firebase_admin.initialize_app()
            
            self._db = firestore.client()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Firebase: {str(e)}")
    
    @property
    def db(self):
        """Get Firestore database client"""
        if self._db is None:
            self._initialize_firebase()
        return self._db
    
    # Managed Account Operations
    
    async def create_managed_account(self, account_data: Dict[str, Any]) -> str:
        """Create a new managed account document"""
        try:
            # Add timestamp
            account_data['created_at'] = datetime.utcnow()
            account_data['updated_at'] = datetime.utcnow()
            
            # Create document
            doc_ref = self.db.collection(self.settings.managed_accounts_collection).add(account_data)
            return doc_ref[1].id  # Return document ID
            
        except Exception as e:
            raise RuntimeError(f"Failed to create managed account: {str(e)}")
    
    async def get_managed_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get managed account by ID"""
        try:
            doc_ref = self.db.collection(self.settings.managed_accounts_collection).document(account_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            raise RuntimeError(f"Failed to get managed account: {str(e)}")
    
    async def get_managed_account_by_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get managed account by deployment ID"""
        try:
            query = self.db.collection(self.settings.managed_accounts_collection).where(
                filter=FieldFilter("deployment_id", "==", deployment_id)
            ).limit(1)
            
            docs = query.stream()
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            raise RuntimeError(f"Failed to get managed account by deployment: {str(e)}")
    
    async def update_managed_account(self, account_id: str, updates: Dict[str, Any]) -> bool:
        """Update managed account"""
        try:
            # Add update timestamp
            updates['updated_at'] = datetime.utcnow()
            
            doc_ref = self.db.collection(self.settings.managed_accounts_collection).document(account_id)
            doc_ref.update(updates)
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to update managed account: {str(e)}")
    
    async def delete_managed_account(self, account_id: str) -> bool:
        """Delete managed account"""
        try:
            doc_ref = self.db.collection(self.settings.managed_accounts_collection).document(account_id)
            doc_ref.delete()
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to delete managed account: {str(e)}")
    
    async def list_managed_accounts_by_deployment(self, deployment_id: str) -> List[Dict[str, Any]]:
        """List all managed accounts for a deployment"""
        try:
            query = self.db.collection(self.settings.managed_accounts_collection).where(
                filter=FieldFilter("deployment_id", "==", deployment_id)
            ).order_by("created_at", direction=firestore.Query.DESCENDING)
            
            accounts = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                accounts.append(data)
            
            return accounts
            
        except Exception as e:
            raise RuntimeError(f"Failed to list managed accounts: {str(e)}")
    
    # Webhook Log Operations
    
    async def create_webhook_log(self, log_data: Dict[str, Any]) -> str:
        """Create a webhook processing log"""
        try:
            # Add timestamp
            log_data['created_at'] = datetime.utcnow()
            
            # Create document
            doc_ref = self.db.collection(self.settings.webhook_logs_collection).add(log_data)
            return doc_ref[1].id
            
        except Exception as e:
            raise RuntimeError(f"Failed to create webhook log: {str(e)}")
    
    async def get_webhook_logs(self, account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get webhook logs for an account"""
        try:
            query = self.db.collection(self.settings.webhook_logs_collection).where(
                filter=FieldFilter("account_id", "==", account_id)
            ).order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
            
            logs = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                logs.append(data)
            
            return logs
            
        except Exception as e:
            raise RuntimeError(f"Failed to get webhook logs: {str(e)}")
    
    # Account Status Operations
    
    async def update_account_status(self, account_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Update account status"""
        try:
            updates = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            if details:
                updates.update(details)
            
            return await self.update_managed_account(account_id, updates)
            
        except Exception as e:
            raise RuntimeError(f"Failed to update account status: {str(e)}")
    
    async def update_verification_status(self, account_id: str, verified: bool, verification_details: Optional[Dict[str, Any]] = None) -> bool:
        """Update verification status"""
        try:
            updates = {
                'status': 'active' if verified else 'verification_failed',
                'updated_at': datetime.utcnow()
            }
            
            if verified:
                updates['verified_at'] = datetime.utcnow()
            
            if verification_details:
                updates.update(verification_details)
            
            return await self.update_managed_account(account_id, updates)
            
        except Exception as e:
            raise RuntimeError(f"Failed to update verification status: {str(e)}")
    
    # Health and Analytics
    
    async def get_account_statistics(self, account_id: str, days: int = 30) -> Dict[str, Any]:
        """Get account statistics"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date.replace(day=end_date.day - days) if end_date.day > days else end_date.replace(month=end_date.month - 1, day=end_date.day + 30 - days)
            
            # Query webhook logs for statistics
            query = self.db.collection(self.settings.webhook_logs_collection).where(
                filter=FieldFilter("account_id", "==", account_id)
            ).where(
                filter=FieldFilter("created_at", ">=", start_date)
            ).where(
                filter=FieldFilter("created_at", "<=", end_date)
            )
            
            total_messages = 0
            error_count = 0
            
            for doc in query.stream():
                data = doc.to_dict()
                total_messages += len(data.get('processed_messages', []))
                if data.get('status') == 'error':
                    error_count += 1
            
            return {
                'account_id': account_id,
                'period_days': days,
                'total_messages': total_messages,
                'error_count': error_count,
                'success_rate': (total_messages - error_count) / max(total_messages, 1),
                'health_score': max(0, 1 - (error_count / max(total_messages, 1)))
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get account statistics: {str(e)}")
    
    # Utility Methods
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Firebase service health"""
        try:
            # Try to read from a collection
            collections = list(self.db.collections())
            
            return {
                'service': 'firebase',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'collections_accessible': len(collections) > 0,
                'project_id': self.settings.firebase_project_id
            }
            
        except Exception as e:
            return {
                'service': 'firebase',
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Clean up old webhook logs"""
        try:
            cutoff_date = datetime.utcnow().replace(day=datetime.utcnow().day - days_to_keep)
            
            query = self.db.collection(self.settings.webhook_logs_collection).where(
                filter=FieldFilter("created_at", "<", cutoff_date)
            )
            
            deleted_count = 0
            batch = self.db.batch()
            
            for doc in query.stream():
                batch.delete(doc.reference)
                deleted_count += 1
                
                # Commit in batches of 500 (Firestore limit)
                if deleted_count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Commit remaining deletions
            if deleted_count % 500 != 0:
                batch.commit()
            
            return deleted_count
            
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup old logs: {str(e)}")


# Global Firebase service instance
firebase_service = FirebaseService()


def get_firebase_service() -> FirebaseService:
    """Get Firebase service instance"""
    return firebase_service