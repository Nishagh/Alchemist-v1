"""
Enhanced Firebase service with GNF collections integration
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Import alchemist-shared components
from alchemist_shared.database.firebase_client import FirebaseClient
from alchemist_shared.constants.collections import Collections
from firebase_admin.firestore import SERVER_TIMESTAMP

from config.settings import settings

logger = logging.getLogger(__name__)


class EnhancedFirebaseService:
    """
    Enhanced Firebase service with comprehensive GNF collections support
    """
    
    def __init__(self):
        # Use alchemist-shared Firebase client exclusively
        try:
            self.firebase_client = FirebaseClient()
            if self.firebase_client:
                self.db = self.firebase_client.db
                logger.info("Enhanced Firebase service initialized with alchemist-shared")
            else:
                raise Exception("Firebase client not available from alchemist-shared")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase service: {e}")
            # Create a no-op service that doesn't crash
            self.firebase_client = None
            self.db = None
            logger.warning("Firebase service initialized in no-op mode")
    
    def _check_firebase_available(self) -> bool:
        """Check if Firebase service is available"""
        return self.db is not None
    
    # ============================================================================
    # AGENT OPERATIONS
    # ============================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration"""
        try:
            collection_name = Collections.AGENTS
            agent_ref = self.db.collection(collection_name).document(agent_id)
            agent_doc = agent_ref.get()
            
            if agent_doc.exists:
                return agent_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent document"""
        try:
            collection_name = Collections.AGENTS
            agent_ref = self.db.collection(collection_name).document(agent_id)
            
            updates['updated_at'] = SERVER_TIMESTAMP
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
            import uuid
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
            
            collection_name = 'conversations'
            conversation_ref = self.db.collection(collection_name)
            doc_ref = conversation_ref.add(conversation_data)[1]
            
            logger.info(f"Created conversation {doc_ref.id} for agent {agent_id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def add_message(self, conversation_id: str, role: str, content: str,
                         token_usage: Optional[Dict[str, int]] = None,
                         accountability_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to conversation with accountability metadata"""
        try:
            message_data = {
                'role': role,
                'content': content,
                'timestamp': SERVER_TIMESTAMP
            }
            
            if token_usage:
                message_data['token_usage'] = token_usage
            
            if accountability_metadata:
                message_data['accountability'] = accountability_metadata
            
            collection_name = 'conversations'
            message_ref = (self.db.collection(collection_name)
                          .document(conversation_id)
                          .collection('messages')
                          .add(message_data)[1])
            
            # Update conversation metadata
            conversation_ref = self.db.collection(collection_name).document(conversation_id)
            conversation_ref.update({
                'updated_at': SERVER_TIMESTAMP,
                'message_count': firestore.Increment(1),
                'last_message': content[:100]
            })
            
            return message_ref.id
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        try:
            collection_name = 'conversations'
            messages_ref = (self.db.collection(collection_name)
                           .document(conversation_id)
                           .collection('messages')
                           .order_by('timestamp')
                           .limit(limit))
            
            messages = []
            for msg_doc in messages_ref.stream():
                msg_data = msg_doc.to_dict()
                msg_data['id'] = msg_doc.id
                messages.append(msg_data)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
    
    # ============================================================================
    # GNF OPERATIONS
    # ============================================================================
    
    async def update_narrative_identity(self, agent_id: str, identity_data: Dict[str, Any]) -> bool:
        """Update agent narrative identity"""
        try:
            # Update the agent document with GNF fields
            collection_name = Collections.AGENTS
            agent_ref = self.db.collection(collection_name).document(agent_id)
            
            gnf_updates = {
                'last_gnf_sync': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP
            }
            gnf_updates.update(identity_data)
            
            agent_ref.update(gnf_updates)
            
            logger.info(f"Updated narrative identity for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update narrative identity for agent {agent_id}: {e}")
            return False
    
    async def store_agent_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """Store agent interaction for narrative tracking"""
        try:
            interaction_data.update({
                'timestamp': SERVER_TIMESTAMP,
                'created_at': SERVER_TIMESTAMP
            })
            
            collection_name = 'agent_interactions'
            interaction_ref = self.db.collection(collection_name).add(interaction_data)[1]
            
            logger.info(f"Stored agent interaction {interaction_ref.id}")
            return interaction_ref.id
            
        except Exception as e:
            logger.error(f"Failed to store agent interaction: {e}")
            raise
    
    async def store_agent_memory(self, memory_data: Dict[str, Any]) -> str:
        """Store agent memory"""
        try:
            memory_data.update({
                'timestamp': SERVER_TIMESTAMP,
                'created_at': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP
            })
            
            collection_name = Collections.AGENT_MEMORIES
            memory_ref = self.db.collection(collection_name).add(memory_data)[1]
            
            logger.info(f"Stored agent memory {memory_ref.id}")
            return memory_ref.id
            
        except Exception as e:
            logger.error(f"Failed to store agent memory: {e}")
            raise
    
    async def store_evolution_event(self, evolution_data: Dict[str, Any]) -> str:
        """Store agent evolution event"""
        try:
            evolution_data.update({
                'timestamp': SERVER_TIMESTAMP,
                'created_at': SERVER_TIMESTAMP
            })
            
            collection_name = Collections.EVOLUTION_EVENTS
            evolution_ref = self.db.collection(collection_name).add(evolution_data)[1]
            
            logger.info(f"Stored evolution event {evolution_ref.id}")
            return evolution_ref.id
            
        except Exception as e:
            logger.error(f"Failed to store evolution event: {e}")
            raise
    
    async def store_responsibility_assessment(self, assessment_data: Dict[str, Any]) -> str:
        """Store responsibility assessment"""
        try:
            assessment_data.update({
                'timestamp': SERVER_TIMESTAMP,
                'created_at': SERVER_TIMESTAMP
            })
            
            collection_name = Collections.RESPONSIBILITY_ASSESSMENTS
            assessment_ref = self.db.collection(collection_name).add(assessment_data)[1]
            
            logger.info(f"Stored responsibility assessment {assessment_ref.id}")
            return assessment_ref.id
            
        except Exception as e:
            logger.error(f"Failed to store responsibility assessment: {e}")
            raise
    
    # ============================================================================
    # METRICS AND MONITORING
    # ============================================================================
    
    async def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]) -> bool:
        """Update agent metrics including story-loss"""
        try:
            metrics_data = {
                'agent_id': agent_id,
                'timestamp': SERVER_TIMESTAMP,
                'version': metrics.get('version', 1)
            }
            metrics_data.update(metrics)
            
            # Update main metrics document
            metrics_ref = self.db.collection('agent_metrics').document(agent_id)
            metrics_ref.set(metrics_data, merge=True)
            
            # Store in time-series for trend analysis
            if 'story_loss' in metrics:
                await self._store_story_loss_time_series(agent_id, metrics['story_loss'])
            
            logger.info(f"Updated metrics for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent metrics: {e}")
            return False
    
    async def _store_story_loss_time_series(self, agent_id: str, story_loss: float):
        """Store story-loss in time-series collection"""
        try:
            # Create time-based document ID for easy querying
            now = datetime.now(timezone.utc)
            doc_id = now.strftime('%Y%m%d_%H%M%S')
            
            time_series_data = {
                'story_loss': story_loss,
                'timestamp': SERVER_TIMESTAMP,
                'metadata': {
                    'agent_id': agent_id,
                    'measurement_type': 'automated'
                }
            }
            
            time_series_ref = (self.db.collection('agent_metrics')
                              .document(agent_id)
                              .collection('time_series')
                              .document(doc_id))
            
            time_series_ref.set(time_series_data)
            
        except Exception as e:
            logger.error(f"Failed to store story-loss time series: {e}")
    
    async def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current agent metrics"""
        try:
            metrics_ref = self.db.collection('agent_metrics').document(agent_id)
            metrics_doc = metrics_ref.get()
            
            if metrics_doc.exists:
                return metrics_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent metrics: {e}")
            return None
    
    async def get_story_loss_trend(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get story-loss trend data"""
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time.replace(hour=end_time.hour - hours)
            
            start_doc_id = start_time.strftime('%Y%m%d_%H%M%S')
            
            time_series_ref = (self.db.collection('agent_metrics')
                              .document(agent_id)
                              .collection('time_series')
                              .where('timestamp', '>=', start_time)
                              .order_by('timestamp'))
            
            trend_data = []
            for doc in time_series_ref.stream():
                data = doc.to_dict()
                trend_data.append({
                    'timestamp': data['timestamp'],
                    'story_loss': data['story_loss'],
                    'metadata': data.get('metadata', {})
                })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Failed to get story-loss trend: {e}")
            return []
    
    # ============================================================================
    # NARRATIVE GRAPH OPERATIONS
    # ============================================================================
    
    async def update_narrative_graph(self, agent_id: str, graph_data: Dict[str, Any]) -> bool:
        """Update agent narrative graph"""
        try:
            graph_updates = {
                'agent_id': agent_id,
                'last_updated': SERVER_TIMESTAMP,
                'version': firestore.Increment(1)
            }
            graph_updates.update(graph_data)
            
            graph_ref = self.db.collection('agent_graphs').document(agent_id)
            graph_ref.set(graph_updates, merge=True)
            
            logger.info(f"Updated narrative graph for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update narrative graph: {e}")
            return False
    
    async def get_narrative_graph(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent narrative graph"""
        try:
            graph_ref = self.db.collection('agent_graphs').document(agent_id)
            graph_doc = graph_ref.get()
            
            if graph_doc.exists:
                return graph_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get narrative graph: {e}")
            return None
    
    # ============================================================================
    # ALERT OPERATIONS
    # ============================================================================
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> str:
        """Create accountability alert"""
        try:
            alert_data.update({
                'created_at': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP,
                'status': 'active'
            })
            
            collection_name = 'alerts'
            alert_ref = self.db.collection(collection_name).add(alert_data)[1]
            
            logger.info(f"Created alert {alert_ref.id}")
            return alert_ref.id
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise
    
    async def create_agent_event(self, event_data: Dict[str, Any]) -> str:
        """Create agent event for monitoring"""
        try:
            event_data.update({
                'timestamp': SERVER_TIMESTAMP,
                'created_at': SERVER_TIMESTAMP
            })
            
            collection_name = 'agent_events'
            event_ref = self.db.collection(collection_name).add(event_data)[1]
            
            logger.info(f"Created agent event {event_ref.id}")
            return event_ref.id
            
        except Exception as e:
            logger.error(f"Failed to create agent event: {e}")
            raise
    
    # ============================================================================
    # KNOWLEDGE BASE OPERATIONS
    # ============================================================================
    
    async def get_agent_knowledge_embeddings(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get knowledge embeddings for agent"""
        try:
            collection_name = Collections.KNOWLEDGE_EMBEDDINGS
            embeddings_ref = (self.db.collection(collection_name)
                             .where('agent_id', '==', agent_id)
                             .limit(limit))
            
            embeddings = []
            for doc in embeddings_ref.stream():
                embedding_data = doc.to_dict()
                embedding_data['id'] = doc.id
                embeddings.append(embedding_data)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to get knowledge embeddings: {e}")
            return []
    
    # ============================================================================
    # MCP OPERATIONS
    # ============================================================================
    
    async def get_mcp_server_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get MCP server configuration"""
        try:
            collection_name = Collections.MCP_SERVERS
            mcp_ref = self.db.collection(collection_name).document(agent_id)
            mcp_doc = mcp_ref.get()
            
            if mcp_doc.exists:
                return mcp_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get MCP server config: {e}")
            return None


# Global service instance
firebase_service = EnhancedFirebaseService()