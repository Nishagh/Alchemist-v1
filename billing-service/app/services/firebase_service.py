"""
Firebase service for database operations and authentication
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from firebase_admin import auth
from google.cloud.firestore import Client as FirestoreClient
from google.cloud.firestore import FieldFilter, Query, SERVER_TIMESTAMP
from google.cloud import firestore

# Import centralized Firebase client
from alchemist_shared.database.firebase_client import FirebaseClient

from app.config.settings import settings
# Import collection constants
from app.constants.collections import Collections, DocumentFields, StatusValues

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase service for Firestore operations"""
    
    def __init__(self):
        self.db: Optional[FirestoreClient] = None
        self._firebase_client: Optional[FirebaseClient] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Firebase using centralized client"""
        if self._initialized:
            return
        
        try:
            # Use centralized Firebase client
            self._firebase_client = FirebaseClient()
            self.db = self._firebase_client.db
            self._initialized = True
            logger.info("Billing service Firebase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _ensure_initialized(self):
        """Ensure Firebase is initialized"""
        if not self._initialized or not self.db:
            raise RuntimeError("Firebase service not initialized. Call initialize() first.")
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return decoded token"""
        self._ensure_initialized()
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid token: {e}")
    
    # ========== USER CREDITS OPERATIONS ==========
    
    async def get_user_credits_account(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user credits account"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection(Collections.USER_ACCOUNTS).document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return {DocumentFields.ID: doc.id, **doc.to_dict()}
            return None
            
        except Exception as e:
            logger.error(f"Error getting user credits account: {e}")
            raise
    
    async def create_user_credits_account(self, user_id: str, initial_credits: float = 0.0) -> Dict[str, Any]:
        """Create new user credits account"""
        self._ensure_initialized()
        
        try:
            account_data = {
                DocumentFields.USER_ID: user_id,
                DocumentFields.Billing.CREDIT_BALANCE: initial_credits,
                DocumentFields.Billing.TOTAL_CREDITS_PURCHASED: 0.0,
                DocumentFields.Billing.TOTAL_CREDITS_USED: 0.0,
                DocumentFields.Billing.ACCOUNT_STATUS: StatusValues.Account.TRIAL,
                "trial_credits_remaining": initial_credits,
                DocumentFields.CREATED_AT: SERVER_TIMESTAMP,
                DocumentFields.UPDATED_AT: SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection(Collections.USER_ACCOUNTS).document(user_id)
            doc_ref.set(account_data)
            
            return {"id": user_id, **account_data}
            
        except Exception as e:
            logger.error(f"Error creating user credits account: {e}")
            raise
    
    async def update_user_balance(self, user_id: str, amount: float, transaction_type: str, 
                                 transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user balance atomically"""
        self._ensure_initialized()
        
        try:
            # Use Firestore transaction for atomic updates
            transaction_ref = self.db.transaction()
            
            @firestore.transactional
            def update_balance_transaction(transaction, user_doc_ref, amount, tx_type, tx_data):
                # Get current account
                account_doc = user_doc_ref.get(transaction=transaction)
                
                if not account_doc.exists:
                    raise ValueError(f"User credits account not found: {user_id}")
                
                account_data = account_doc.to_dict()
                current_balance = account_data.get("balance", {})
                
                # Calculate new balance
                new_total = current_balance.get("total_credits", 0.0) + amount
                
                if new_total < 0:
                    raise ValueError("Insufficient credits")
                
                # Update balance
                new_balance = current_balance.copy()
                new_balance["total_credits"] = new_total
                
                # Update bonus/base credits based on transaction type
                if tx_type == "purchase":
                    new_balance["base_credits"] = new_balance.get("base_credits", 0.0) + tx_data.get("base_credits", amount)
                    new_balance["bonus_credits"] = new_balance.get("bonus_credits", 0.0) + tx_data.get("bonus_credits", 0.0)
                
                # Update account
                account_data["balance"] = new_balance
                account_data["updated_at"] = SERVER_TIMESTAMP
                
                transaction.update(user_doc_ref, account_data)
                
                # Create transaction record
                tx_record = {
                    "user_id": user_id,
                    "amount": amount,
                    "type": tx_type,
                    "balance_before": current_balance.get("total_credits", 0.0),
                    "balance_after": new_total,
                    "timestamp": SERVER_TIMESTAMP,
                    "transaction_data": tx_data
                }
                
                tx_ref = self.db.collection(settings.CREDIT_TRANSACTIONS_COLLECTION).document()
                transaction.set(tx_ref, tx_record)
                
                return {"account": account_data, "transaction": tx_record}
            
            user_doc_ref = self.db.collection(settings.USER_CREDITS_COLLECTION).document(user_id)
            result = update_balance_transaction(transaction_ref, user_doc_ref, amount, transaction_type, transaction_data)
            
            # Record lifecycle event for billing transaction
            try:
                from alchemist_shared.services.agent_lifecycle_service import get_agent_lifecycle_service
                lifecycle_service = get_agent_lifecycle_service()
                if lifecycle_service:
                    await lifecycle_service.record_billing_transaction(
                        user_id=user_id,
                        transaction_type=transaction_type,
                        amount=amount,
                        agent_id=transaction_data.get('agent_id'),
                        metadata={
                            'billing_event': True,
                            'balance_before': result['transaction']['balance_before'],
                            'balance_after': result['transaction']['balance_after'],
                            'transaction_data': transaction_data
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to record billing lifecycle event: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            raise
    
    # ========== CREDIT PACKAGES OPERATIONS ==========
    
    async def get_credit_packages(self) -> List[Dict[str, Any]]:
        """Get all available credit packages"""
        self._ensure_initialized()
        
        try:
            packages_ref = self.db.collection(settings.CREDIT_PACKAGES_COLLECTION)
            docs = packages_ref.order_by("price").stream()
            
            packages = []
            for doc in docs:
                packages.append({"id": doc.id, **doc.to_dict()})
            
            # If no packages in database, return default packages
            if not packages:
                from app.config.settings import DEFAULT_CREDIT_PACKAGES
                return DEFAULT_CREDIT_PACKAGES
            
            return packages
            
        except Exception as e:
            logger.error(f"Error getting credit packages: {e}")
            raise
    
    # ========== CREDIT ORDERS OPERATIONS ==========
    
    async def create_credit_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new credit order"""
        self._ensure_initialized()
        
        try:
            order_data["created_at"] = SERVER_TIMESTAMP
            order_data["updated_at"] = SERVER_TIMESTAMP
            
            doc_ref = self.db.collection(settings.CREDIT_ORDERS_COLLECTION).document()
            doc_ref.set(order_data)
            
            return {"id": doc_ref.id, **order_data}
            
        except Exception as e:
            logger.error(f"Error creating credit order: {e}")
            raise
    
    async def get_credit_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get credit order by ID"""
        self._ensure_initialized()
        
        try:
            doc_ref = self.db.collection(settings.CREDIT_ORDERS_COLLECTION).document(order_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            return None
            
        except Exception as e:
            logger.error(f"Error getting credit order: {e}")
            raise
    
    async def update_credit_order(self, order_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update credit order"""
        self._ensure_initialized()
        
        try:
            update_data["updated_at"] = SERVER_TIMESTAMP
            
            doc_ref = self.db.collection(settings.CREDIT_ORDERS_COLLECTION).document(order_id)
            doc_ref.update(update_data)
            
            # Return updated order
            updated_doc = doc_ref.get()
            return {"id": updated_doc.id, **updated_doc.to_dict()}
            
        except Exception as e:
            logger.error(f"Error updating credit order: {e}")
            raise
    
    # ========== TRANSACTIONS OPERATIONS ==========
    
    async def get_user_transactions(self, user_id: str, limit: int = 20, 
                                   transaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user transaction history"""
        self._ensure_initialized()
        
        try:
            query = self.db.collection(settings.CREDIT_TRANSACTIONS_COLLECTION)\
                           .where("user_id", "==", user_id)\
                           .order_by("timestamp", direction=Query.DESCENDING)\
                           .limit(limit)
            
            if transaction_type:
                query = query.where("type", "==", transaction_type)
            
            docs = query.stream()
            
            transactions = []
            for doc in docs:
                transactions.append({"id": doc.id, **doc.to_dict()})
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            raise