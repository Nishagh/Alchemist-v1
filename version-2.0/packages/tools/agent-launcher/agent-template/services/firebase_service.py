"""
Simplified Firebase service with alchemist-shared only support
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

# Import alchemist-shared components
from alchemist_shared.database.firebase_client import FirebaseClient
from firebase_admin.firestore import SERVER_TIMESTAMP, firestore, FieldFilter

from config.settings import settings

logger = logging.getLogger(__name__)


class EnhancedFirebaseService:
    """
    Enhanced Firebase service with comprehensive GNF collections support
    Uses alchemist-shared exclusively
    """
    
    def __init__(self):
        # Use alchemist-shared Firebase client exclusively
        self.firebase_client = FirebaseClient()
        self.db = self.firebase_client.db
        logger.info("Enhanced Firebase service initialized with alchemist-shared")
    
    def _check_firebase_available(self) -> bool:
        """Check if Firebase service is available"""
        return self.db is not None
    
    async def get_narrative_graph(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent narrative graph"""
        try:
            if not self._check_firebase_available():
                return None
                
            graph_ref = self.db.collection('agent_graphs').document(agent_id)
            graph_doc = graph_ref.get()
            
            if graph_doc.exists:
                return graph_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get narrative graph: {e}")
            return None
    
    async def get_documents(self, collection_path: str) -> Optional[Dict[str, Any]]:
        """Get a document's data from a collection"""
        try:
            if not self._check_firebase_available():
                return None
                
            doc_ref = self.db.collection(collection_path)
            docs = doc_ref.get()
            documents = []
            for doc in docs:
                documents.append(doc.to_dict())            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get document data from {collection_path}: {e}")
            return None
    
    async def query_documents(self, collection_name: str, field: str, value: Any) -> List[Dict[str, Any]]:
        """Query documents from a collection by field value"""
        try:
            if not self._check_firebase_available():
                return []
                
            query = self.db.collection(collection_name).where(filter=FieldFilter(field, '==', value))
            docs = query.get()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id  # Include document ID
                results.append(data)
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to query documents from {collection_name} where {field}=={value}: {e}")
            return []
    
    # ============================================================================
    # AGENT OPERATIONS
    # ============================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration"""
        if not self._check_firebase_available():
            return None
            
        try:
            agent_ref = self.db.collection('agents').document(agent_id)
            agent_doc = agent_ref.get()
            
            if agent_doc.exists:
                return agent_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent configuration"""
        if not self._check_firebase_available():
            return True  # Mock success
            
        try:
            updates['updated_at'] = SERVER_TIMESTAMP
            agent_ref = self.db.collection('agents').document(agent_id)
            agent_ref.update(updates)
            
            logger.info(f"Updated agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            return False
    
    # ============================================================================
    # CONVERSATION OPERATIONS
    # ============================================================================
    
    async def create_conversation(self, agent_id: str, user_id: Optional[str] = None, 
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation"""
        if not self._check_firebase_available():
            # Return a mock conversation ID when Firebase is not available
            return str(uuid.uuid4())
            
        try:
            conversation_data = {
                'agent_id': agent_id,
                'user_id': user_id,
                'status': 'active',
                'message_count': 0,
                'created_at': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP
            }
            
            if metadata:
                conversation_data['metadata'] = metadata
            
            conversation_ref = self.db.collection('conversations').add(conversation_data)
            conversation_id = conversation_ref[1].id
            
            logger.info(f"Created conversation {conversation_id} for agent {agent_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to create conversation for agent {agent_id}: {e}")
            return str(uuid.uuid4())  # Return mock ID on error
    
    async def add_message(self, conversation_id: str, role: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None, 
                         token_usage: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to conversation"""
        if not self._check_firebase_available():
            return str(uuid.uuid4())
            
        try:
            message_data = {
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'timestamp': SERVER_TIMESTAMP,
                'created_at': SERVER_TIMESTAMP
            }
            
            if metadata:
                message_data['metadata'] = metadata
                
            if token_usage:
                message_data['token_usage'] = token_usage
            
            message_ref = self.db.collection('messages').add(message_data)
            message_id = message_ref[1].id
            
            # Update conversation message count
            conversation_ref = self.db.collection('conversations').document(conversation_id)
            conversation_ref.update({
                'message_count': firestore.Increment(1),
                'updated_at': SERVER_TIMESTAMP,
                'last_message_at': SERVER_TIMESTAMP
            })
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            return str(uuid.uuid4())
    
    # ============================================================================
    # GNF/ACCOUNTABILITY OPERATIONS
    # ============================================================================
    
    async def update_narrative_identity(self, agent_id: str, identity_data: Dict[str, Any]) -> bool:
        """Update agent's narrative identity"""
        if not self._check_firebase_available():
            return True
            
        try:
            identity_data['updated_at'] = SERVER_TIMESTAMP
            
            # Store in gnf_narrative_identities collection
            identity_ref = self.db.collection('gnf_narrative_identities').document(agent_id)
            identity_ref.set(identity_data, merge=True)
            
            logger.info(f"Updated narrative identity for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update narrative identity for agent {agent_id}: {e}")
            return False
    
    async def store_agent_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """Store agent interaction for accountability tracking"""
        if not self._check_firebase_available():
            return str(uuid.uuid4())
            
        try:
            interaction_data['timestamp'] = SERVER_TIMESTAMP
            interaction_ref = self.db.collection('gnf_agent_interactions').add(interaction_data)
            return interaction_ref[1].id
            
        except Exception as e:
            logger.error(f"Failed to store agent interaction: {e}")
            return str(uuid.uuid4())
    
    async def store_responsibility_assessment(self, assessment_data: Dict[str, Any]) -> str:
        """Store responsibility assessment"""
        if not self._check_firebase_available():
            return str(uuid.uuid4())
            
        try:
            assessment_data['timestamp'] = SERVER_TIMESTAMP
            assessment_data['created_at'] = SERVER_TIMESTAMP
            
            assessment_ref = self.db.collection('gnf_responsibility_assessments').add(assessment_data)
            assessment_id = assessment_ref[1].id
            
            logger.info(f"Stored responsibility assessment {assessment_id}")
            return assessment_id
            
        except Exception as e:
            logger.error(f"Failed to store responsibility assessment: {e}")
            return str(uuid.uuid4())
    
    async def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]) -> bool:
        """Update agent metrics"""
        if not self._check_firebase_available():
            return True
            
        try:
            metrics['updated_at'] = SERVER_TIMESTAMP
            metrics['agent_id'] = agent_id
            
            # Store metrics with timestamp for time series
            metrics_ref = self.db.collection('gnf_agent_metrics').document(agent_id)
            metrics_ref.set(metrics, merge=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent metrics for {agent_id}: {e}")
            return False
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        if not self._check_firebase_available():
            return []
            
        try:
            messages_ref = self.db.collection('messages')\
                              .where('conversation_id', '==', conversation_id)\
                              .order_by('timestamp')\
                              .limit(limit)
            
            messages = []
            for doc in messages_ref.stream():
                message_data = doc.to_dict()
                message_data['id'] = doc.id
                messages.append(message_data)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
    
    async def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent metrics"""
        if not self._check_firebase_available():
            return None
            
        try:
            metrics_ref = self.db.collection('gnf_agent_metrics').document(agent_id)
            metrics_doc = metrics_ref.get()
            
            if metrics_doc.exists:
                return metrics_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent metrics for {agent_id}: {e}")
            return None


# Global instance
firebase_service = EnhancedFirebaseService()