"""
Firebase client for Global Narrative Framework storage operations.
Enhanced to work with the optimized Firebase structure and GNF integration.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1 import FieldFilter
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from .collection_constants import (
    AGENTS, CONVERSATIONS, AGENT_MEMORIES, AGENT_EVOLUTION_EVENTS,
    AGENT_RESPONSIBILITY_RECORDS, CROSS_AGENT_INTERACTIONS, 
    GLOBAL_NARRATIVE_TIMELINE, AgentFields, ConversationFields,
    MemoryFields, EvolutionFields, ResponsibilityFields,
    is_valid_collection, get_migrated_collection
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase client for GNF data operations."""
    
    def __init__(self, credentials_path: Optional[str] = None, project_id: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv('FIREBASE_CREDENTIALS_PATH')
        self.project_id = project_id or os.getenv('FIREBASE_PROJECT_ID')
        self.db = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # In-memory storage fallback
        self._memory_store = {
            'agents': {},
            'conversations': {},
            'agent_memories': {},
            'agent_evolution_events': {},
            'agent_responsibility_records': {},
            'cross_agent_interactions': {},
            'global_narrative_timeline': {}
        }
        
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if there's already an app initialized
            if firebase_admin._apps:
                logger.info("Using existing Firebase app")
                self.db = firestore.client()
            else:
                # Initialize new app
                if self.credentials_path and os.path.exists(self.credentials_path):
                    try:
                        # Try to validate credentials first
                        import json
                        with open(self.credentials_path, 'r') as f:
                            cred_data = json.load(f)
                        
                        # Check if required fields exist
                        required_fields = ['type', 'project_id', 'private_key', 'client_email']
                        if all(field in cred_data for field in required_fields):
                            cred = credentials.Certificate(self.credentials_path)
                            firebase_admin.initialize_app(cred)
                            logger.info("Firebase initialized with service account credentials")
                        else:
                            raise ValueError("Invalid credentials format")
                            
                    except Exception as e:
                        logger.warning(f"Failed to initialize with service account: {e}")
                        logger.info("Attempting to use default credentials...")
                        firebase_admin.initialize_app()
                else:
                    logger.info("No credentials path found, using default credentials")
                    firebase_admin.initialize_app()
                
                self.db = firestore.client()
            
            # Test the connection with a simple operation
            try:
                # Try to get collections to verify connection works
                collections = list(self.db.collections())
                logger.info(f"Firebase connection verified - found {len(collections)} collections")
            except Exception as e:
                logger.warning(f"Firebase connection test failed: {e}")
                # Don't fail completely, just log the warning
            
            logger.info("Firebase initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            logger.warning("Firebase unavailable - using mock mode")
            self.db = None
    
    def _is_available(self) -> bool:
        """Check if Firebase is available."""
        return self.db is not None
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """Create a new agent document."""
        if not self._is_available():
            logger.warning("Firebase unavailable - using mock response")
            return agent_data[AgentFields.AGENT_ID]
            
        try:
            agent_ref = self.db.collection(AGENTS).document(agent_data[AgentFields.AGENT_ID])
            agent_document = {
                **agent_data,
                AgentFields.CREATED_AT: SERVER_TIMESTAMP,
                AgentFields.UPDATED_AT: SERVER_TIMESTAMP
            }
            
            # Initialize GNF metadata if not present
            if 'gnf_metadata' not in agent_document:
                agent_document['gnf_metadata'] = {
                    'gnf_enabled': True,
                    'gnf_version': '2.0.0',
                    'last_narrative_update': SERVER_TIMESTAMP,
                    'total_interactions_tracked': 0,
                    'narrative_coherence_score': 0.5,
                    'identity_stability_score': 0.5
                }
            
            await self._run_in_executor(agent_ref.set, agent_document)
            logger.info(f"Created agent: {agent_data[AgentFields.AGENT_ID]}")
            return agent_data[AgentFields.AGENT_ID]
        except Exception as e:
            logger.error(f"Failed to create agent {agent_data[AgentFields.AGENT_ID]}: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent by ID."""
        try:
            agent_ref = self.db.collection(AGENTS).document(agent_id)
            doc = await self._run_in_executor(agent_ref.get)
            
            if doc.exists:
                data = doc.to_dict()
                data[AgentFields.AGENT_ID] = agent_id
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent document."""
        try:
            agent_ref = self.db.collection(AGENTS).document(agent_id)
            update_data = {
                **updates,
                AgentFields.UPDATED_AT: SERVER_TIMESTAMP
            }
            
            # Update GNF metadata if narrative fields were updated
            gnf_fields = ['gnf_identity', 'gnf_analysis']
            if any(field in updates for field in gnf_fields):
                update_data[AgentFields.LAST_NARRATIVE_UPDATE] = SERVER_TIMESTAMP
            
            await self._run_in_executor(agent_ref.update, update_data)
            logger.info(f"Updated agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            return False
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent and related data."""
        try:
            batch = self.db.batch()
            
            # Delete agent document
            agent_ref = self.db.collection(AGENTS).document(agent_id)
            batch.delete(agent_ref)
            
            # Delete related conversations (enhanced interactions)
            conversations = await self._run_in_executor(
                self.db.collection(CONVERSATIONS)
                .where(ConversationFields.AGENT_ID, '==', agent_id)
                .get
            )
            
            for conversation in conversations:
                batch.delete(conversation.reference)
            
            # Delete related memories
            memories = await self._run_in_executor(
                self.db.collection(AGENT_MEMORIES)
                .where(MemoryFields.AGENT_ID, '==', agent_id)
                .get
            )
            
            for memory in memories:
                batch.delete(memory.reference)
            
            # Delete evolution events
            evolution_events = await self._run_in_executor(
                self.db.collection(AGENT_EVOLUTION_EVENTS)
                .where(EvolutionFields.AGENT_ID, '==', agent_id)
                .get
            )
            
            for event in evolution_events:
                batch.delete(event.reference)
            
            # Delete responsibility records
            responsibility_records = await self._run_in_executor(
                self.db.collection(AGENT_RESPONSIBILITY_RECORDS)
                .where(ResponsibilityFields.AGENT_ID, '==', agent_id)
                .get
            )
            
            for record in responsibility_records:
                batch.delete(record.reference)
            
            await self._run_in_executor(batch.commit)
            logger.info(f"Deleted agent and related data: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            return False
    
    async def store_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """Store enhanced conversation with GNF analysis."""
        try:
            conversation_ref = self.db.collection(CONVERSATIONS).document()
            
            # Ensure required fields are present
            conversation_document = {
                **interaction_data,
                ConversationFields.TIMESTAMP: SERVER_TIMESTAMP,
                ConversationFields.CREATED_AT: SERVER_TIMESTAMP,
                ConversationFields.IS_PRODUCTION: interaction_data.get('is_production', False),
                ConversationFields.DEPLOYMENT_TYPE: interaction_data.get('deployment_type', 'pre_deployment')
            }
            
            # Initialize GNF processing metadata if not present
            if 'gnf_processing' not in conversation_document:
                conversation_document['gnf_processing'] = {
                    'analysis_completed': False,
                    'processing_time_ms': 0,
                    'memory_consolidation_triggered': False,
                    'evolution_check_performed': False,
                    'gnf_version': '2.0.0'
                }
            
            await self._run_in_executor(conversation_ref.set, conversation_document)
            
            conversation_id = conversation_ref.id
            logger.info(f"Stored enhanced conversation: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise
    
    async def get_agent_interactions(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent conversations (enhanced interactions) with limit."""
        try:
            conversations_ref = (self.db.collection(CONVERSATIONS)
                               .where(ConversationFields.AGENT_ID, '==', agent_id)
                               .order_by(ConversationFields.TIMESTAMP, direction=firestore.Query.DESCENDING)
                               .limit(limit))
            
            docs = await self._run_in_executor(conversations_ref.get)
            
            conversations = []
            for doc in docs:
                data = doc.to_dict()
                data['interaction_id'] = doc.id  # Maintain backward compatibility
                data['conversation_id'] = doc.id
                conversations.append(data)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get conversations for agent {agent_id}: {e}")
            return []
    
    async def store_memory(self, memory_data: Dict[str, Any]) -> str:
        """Store consolidated memory in enhanced structure."""
        try:
            memory_ref = self.db.collection(AGENT_MEMORIES).document()
            
            # Ensure required fields are present
            memory_document = {
                **memory_data,
                MemoryFields.CREATED_AT: SERVER_TIMESTAMP,
                MemoryFields.LAST_REINFORCED: SERVER_TIMESTAMP
            }
            
            # Generate memory_id if not present
            if MemoryFields.MEMORY_ID not in memory_document:
                memory_document[MemoryFields.MEMORY_ID] = memory_ref.id
            
            # Initialize metadata if not present
            if 'metadata' not in memory_document:
                memory_document['metadata'] = {
                    'importance_score': 0.5,
                    'consolidation_strength': 0.5,
                    'emotional_valence': 0.0,
                    'access_frequency': 0,
                    'last_accessed': SERVER_TIMESTAMP,
                    'decay_rate': 0.1,
                    'tags': [],
                    'themes': [],
                    'related_memories': [],
                    'source_interactions': [],
                    'linked_experiences': []
                }
            
            await self._run_in_executor(memory_ref.set, memory_document)
            
            memory_id = memory_ref.id
            logger.info(f"Stored enhanced memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def search_memories(self, agent_id: str, query: str, memory_type: Optional[str] = None, 
                            limit: int = 20) -> List[Dict[str, Any]]:
        """Search agent memories in enhanced structure."""
        try:
            memories_ref = self.db.collection(AGENT_MEMORIES).where(MemoryFields.AGENT_ID, '==', agent_id)
            
            if memory_type:
                memories_ref = memories_ref.where(MemoryFields.MEMORY_TYPE, '==', memory_type)
            
            # Order by importance score first, then by creation date
            memories_ref = memories_ref.order_by(MemoryFields.IMPORTANCE_SCORE, direction=firestore.Query.DESCENDING)
            memories_ref = memories_ref.order_by(MemoryFields.CREATED_AT, direction=firestore.Query.DESCENDING)
            memories_ref = memories_ref.limit(limit)
            
            docs = await self._run_in_executor(memories_ref.get)
            
            memories = []
            for doc in docs:
                data = doc.to_dict()
                data['memory_id'] = doc.id
                
                # Simple text search in content
                if query.lower() in str(data.get('content', '')).lower():
                    memories.append(data)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories for agent {agent_id}: {e}")
            return []
    
    async def store_evolution_event(self, evolution_data: Dict[str, Any]) -> str:
        """Store agent evolution event in enhanced structure."""
        try:
            evolution_ref = self.db.collection(AGENT_EVOLUTION_EVENTS).document()
            
            # Ensure required fields are present
            evolution_document = {
                **evolution_data,
                EvolutionFields.CREATED_AT: SERVER_TIMESTAMP
            }
            
            # Generate event_id if not present
            if EvolutionFields.EVENT_ID not in evolution_document:
                evolution_document[EvolutionFields.EVENT_ID] = evolution_ref.id
            
            # Set default values for required fields
            if EvolutionFields.SIGNIFICANCE_LEVEL not in evolution_document:
                evolution_document[EvolutionFields.SIGNIFICANCE_LEVEL] = 'moderate'
            
            if EvolutionFields.EVENT_TYPE not in evolution_document:
                evolution_document[EvolutionFields.EVENT_TYPE] = 'personality_development'
            
            # Maintain backward compatibility
            if 'timestamp' not in evolution_document:
                evolution_document['timestamp'] = evolution_document[EvolutionFields.CREATED_AT]
            
            await self._run_in_executor(evolution_ref.set, evolution_document)
            
            evolution_id = evolution_ref.id
            logger.info(f"Stored enhanced evolution event: {evolution_id}")
            return evolution_id
            
        except Exception as e:
            logger.error(f"Failed to store evolution event: {e}")
            raise
    
    async def get_agent_evolution_history(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent evolution history from enhanced structure."""
        try:
            evolution_ref = (self.db.collection(AGENT_EVOLUTION_EVENTS)
                           .where(EvolutionFields.AGENT_ID, '==', agent_id)
                           .order_by(EvolutionFields.CREATED_AT, direction=firestore.Query.DESCENDING)
                           .limit(limit))
            
            docs = await self._run_in_executor(evolution_ref.get)
            
            events = []
            for doc in docs:
                data = doc.to_dict()
                data['evolution_id'] = doc.id  # Maintain backward compatibility
                data[EvolutionFields.EVENT_ID] = doc.id
                events.append(data)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get evolution history for agent {agent_id}: {e}")
            return []
    
    async def store_global_event(self, event_data: Dict[str, Any]) -> str:
        """Store global narrative event."""
        try:
            event_ref = self.db.collection(GLOBAL_NARRATIVE_TIMELINE).document()
            
            # Ensure required fields are present
            enhanced_event_data = {
                **event_data,
                'occurred_at': event_data.get('occurred_at', SERVER_TIMESTAMP),
                'detected_at': SERVER_TIMESTAMP
            }
            
            # Generate event_id if not present
            if 'event_id' not in enhanced_event_data:
                enhanced_event_data['event_id'] = event_ref.id
            
            # Set defaults for enhanced structure
            if 'significance_level' not in enhanced_event_data:
                enhanced_event_data['significance_level'] = 'moderate'
                
            if 'confidence_level' not in enhanced_event_data:
                enhanced_event_data['confidence_level'] = 0.8
                
            if 'validation_status' not in enhanced_event_data:
                enhanced_event_data['validation_status'] = 'confirmed'
            
            await self._run_in_executor(event_ref.set, enhanced_event_data)
            
            event_id = event_ref.id
            logger.info(f"Stored global event: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to store global event: {e}")
            raise
    
    async def get_global_timeline(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get global narrative timeline."""
        try:
            timeline_ref = (self.db.collection(GLOBAL_NARRATIVE_TIMELINE)
                          .order_by('occurred_at', direction=firestore.Query.DESCENDING)
                          .limit(limit))
            
            docs = await self._run_in_executor(timeline_ref.get)
            
            events = []
            for doc in docs:
                data = doc.to_dict()
                data['event_id'] = doc.id
                events.append(data)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get global timeline: {e}")
            return []
    
    async def get_cross_agent_interactions_legacy(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get cross-agent interactions (legacy method for backward compatibility)."""
        try:
            # This method now delegates to the enhanced cross-agent interactions
            return await self.get_cross_agent_interactions(limit=limit)
            
        except Exception as e:
            logger.error(f"Failed to get cross-agent interactions: {e}")
            return []
    
    async def get_agent_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        try:
            # Count agents
            agents_count = len(await self._run_in_executor(
                self.db.collection(AGENTS).get
            ))
            
            # Count conversations (enhanced interactions)
            conversations_count = len(await self._run_in_executor(
                self.db.collection(CONVERSATIONS).get
            ))
            
            # Count memories
            memories_count = len(await self._run_in_executor(
                self.db.collection(AGENT_MEMORIES).get
            ))
            
            # Count evolution events
            evolution_count = len(await self._run_in_executor(
                self.db.collection(AGENT_EVOLUTION_EVENTS).get
            ))
            
            # Count responsibility records
            responsibility_count = len(await self._run_in_executor(
                self.db.collection(AGENT_RESPONSIBILITY_RECORDS).get
            ))
            
            # Count cross-agent interactions
            cross_agent_count = len(await self._run_in_executor(
                self.db.collection(CROSS_AGENT_INTERACTIONS).get
            ))
            
            return {
                'total_agents': agents_count,
                'total_conversations': conversations_count,
                'total_memories': memories_count,
                'total_evolution_events': evolution_count,
                'total_responsibility_records': responsibility_count,
                'total_cross_agent_interactions': cross_agent_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    async def list_agents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all agents with basic info."""
        try:
            agents_ref = (self.db.collection(AGENTS)
                         .order_by(AgentFields.CREATED_AT, direction=firestore.Query.DESCENDING)
                         .limit(limit))
            
            docs = await self._run_in_executor(agents_ref.get)
            
            agents = []
            for doc in docs:
                data = doc.to_dict()
                # Return summary info with enhanced GNF fields
                agents.append({
                    'agent_id': doc.id,
                    'name': data.get(AgentFields.NAME, 'Unknown'),
                    'development_stage': data.get(AgentFields.EVOLUTION_DEVELOPMENT_STAGE, 'nascent'),
                    'gnf_enabled': data.get(AgentFields.GNF_ENABLED, False),
                    'narrative_coherence_score': data.get(AgentFields.NARRATIVE_COHERENCE_SCORE, 0.0),
                    'created_at': data.get(AgentFields.CREATED_AT),
                    'updated_at': data.get(AgentFields.UPDATED_AT)
                })
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def get_agent_actions(self, agent_id: str, limit: int = 100, days: int = 30) -> List[Dict[str, Any]]:
        """Get agent actions/decisions for responsibility analysis."""
        try:
            if self.db:
                # Calculate date threshold
                from datetime import timedelta
                threshold_date = datetime.utcnow() - timedelta(days=days)
                
                # Use enhanced responsibility records collection
                actions_ref = self.db.collection(AGENT_RESPONSIBILITY_RECORDS).where(
                    filter=FieldFilter(ResponsibilityFields.AGENT_ID, '==', agent_id)
                ).where(
                    filter=FieldFilter(ResponsibilityFields.PERFORMED_AT, '>=', threshold_date)
                ).order_by(ResponsibilityFields.PERFORMED_AT, direction=firestore.Query.DESCENDING).limit(limit)
                
                actions = await self._run_in_executor(
                    lambda: [doc.to_dict() for doc in actions_ref.stream()]
                )
                
                return actions
            else:
                # Return empty list if no Firebase connection
                return []
                
        except Exception as e:
            logger.error(f"Failed to get agent actions for {agent_id}: {e}")
            return []
    
    # ========================================================================
    # NEW ENHANCED GNF COLLECTION METHODS
    # ========================================================================
    
    async def store_responsibility_record(self, record_data: Dict[str, Any]) -> str:
        """Store agent responsibility record."""
        try:
            record_ref = self.db.collection(AGENT_RESPONSIBILITY_RECORDS).document()
            
            # Ensure required fields are present
            record_document = {
                **record_data,
                ResponsibilityFields.PERFORMED_AT: record_data.get('performed_at', SERVER_TIMESTAMP),
                'recorded_at': SERVER_TIMESTAMP
            }
            
            # Generate action_id if not present
            if ResponsibilityFields.ACTION_ID not in record_document:
                record_document[ResponsibilityFields.ACTION_ID] = record_ref.id
            
            # Set default values
            if ResponsibilityFields.SUCCESS_LEVEL not in record_document:
                record_document[ResponsibilityFields.SUCCESS_LEVEL] = 0.5
                
            if ResponsibilityFields.ACTION_TYPE not in record_document:
                record_document[ResponsibilityFields.ACTION_TYPE] = 'decision'
            
            await self._run_in_executor(record_ref.set, record_document)
            
            record_id = record_ref.id
            logger.info(f"Stored responsibility record: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to store responsibility record: {e}")
            raise
    
    async def get_agent_responsibility_history(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent responsibility records."""
        try:
            records_ref = (self.db.collection(AGENT_RESPONSIBILITY_RECORDS)
                          .where(ResponsibilityFields.AGENT_ID, '==', agent_id)
                          .order_by(ResponsibilityFields.PERFORMED_AT, direction=firestore.Query.DESCENDING)
                          .limit(limit))
            
            docs = await self._run_in_executor(records_ref.get)
            
            records = []
            for doc in docs:
                data = doc.to_dict()
                data[ResponsibilityFields.ACTION_ID] = doc.id
                records.append(data)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get responsibility history for agent {agent_id}: {e}")
            return []
    
    async def store_cross_agent_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """Store cross-agent interaction."""
        try:
            interaction_ref = self.db.collection(CROSS_AGENT_INTERACTIONS).document()
            
            # Ensure required fields are present
            interaction_document = {
                **interaction_data,
                'created_at': SERVER_TIMESTAMP
            }
            
            # Generate interaction_id if not present
            if 'interaction_id' not in interaction_document:
                interaction_document['interaction_id'] = interaction_ref.id
            
            # Set defaults
            if 'interaction_type' not in interaction_document:
                interaction_document['interaction_type'] = 'collaboration'
                
            if 'interaction_quality' not in interaction_document:
                interaction_document['interaction_quality'] = 'neutral'
            
            await self._run_in_executor(interaction_ref.set, interaction_document)
            
            interaction_id = interaction_ref.id
            logger.info(f"Stored cross-agent interaction: {interaction_id}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Failed to store cross-agent interaction: {e}")
            raise
    
    async def get_cross_agent_interactions(self, agent_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get cross-agent interactions, optionally filtered by agent."""
        try:
            interactions_ref = self.db.collection(CROSS_AGENT_INTERACTIONS)
            
            if agent_id:
                interactions_ref = interactions_ref.where('participating_agents', 'array_contains', agent_id)
            
            interactions_ref = interactions_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = await self._run_in_executor(interactions_ref.get)
            
            interactions = []
            for doc in docs:
                data = doc.to_dict()
                data['interaction_id'] = doc.id
                interactions.append(data)
            
            return interactions
            
        except Exception as e:
            logger.error(f"Failed to get cross-agent interactions: {e}")
            return []
    
    async def store_global_narrative_event(self, event_data: Dict[str, Any]) -> str:
        """Store global narrative timeline event."""
        try:
            event_ref = self.db.collection(GLOBAL_NARRATIVE_TIMELINE).document()
            
            # Ensure required fields are present
            event_document = {
                **event_data,
                'occurred_at': event_data.get('occurred_at', SERVER_TIMESTAMP),
                'detected_at': SERVER_TIMESTAMP
            }
            
            # Generate event_id if not present
            if 'event_id' not in event_document:
                event_document['event_id'] = event_ref.id
            
            # Set defaults
            if 'significance_level' not in event_document:
                event_document['significance_level'] = 'moderate'
                
            if 'confidence_level' not in event_document:
                event_document['confidence_level'] = 0.8
                
            if 'validation_status' not in event_document:
                event_document['validation_status'] = 'confirmed'
            
            await self._run_in_executor(event_ref.set, event_document)
            
            event_id = event_ref.id
            logger.info(f"Stored global narrative event: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to store global narrative event: {e}")
            raise
    
    async def get_global_narrative_timeline(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get global narrative timeline events."""
        try:
            events_ref = (self.db.collection(GLOBAL_NARRATIVE_TIMELINE)
                         .order_by('occurred_at', direction=firestore.Query.DESCENDING)
                         .limit(limit))
            
            docs = await self._run_in_executor(events_ref.get)
            
            events = []
            for doc in docs:
                data = doc.to_dict()
                data['event_id'] = doc.id
                events.append(data)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get global narrative timeline: {e}")
            return []
    
    async def get_memory_timeline(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent memory timeline ordered by importance and recency."""
        try:
            memories_ref = (self.db.collection(AGENT_MEMORIES)
                           .where(MemoryFields.AGENT_ID, '==', agent_id)
                           .order_by(MemoryFields.IMPORTANCE_SCORE, direction=firestore.Query.DESCENDING)
                           .limit(limit))
            
            docs = await self._run_in_executor(memories_ref.get)
            
            memories = []
            for doc in docs:
                data = doc.to_dict()
                data[MemoryFields.MEMORY_ID] = doc.id
                memories.append(data)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get memory timeline for agent {agent_id}: {e}")
            return []
    
    async def get_memory_patterns(self, agent_id: str) -> Dict[str, Any]:
        """Get memory pattern analysis for agent."""
        try:
            memories = await self.search_memories(agent_id, "", limit=1000)
            
            # Analyze patterns
            memory_types = {}
            tag_frequency = {}
            theme_frequency = {}
            
            for memory in memories:
                # Memory type distribution
                memory_type = memory.get(MemoryFields.MEMORY_TYPE, 'unknown')
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
                
                # Tag frequency
                metadata = memory.get('metadata', {})
                tags = metadata.get('tags', [])
                for tag in tags:
                    tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
                
                # Theme frequency
                themes = metadata.get('themes', [])
                for theme in themes:
                    theme_frequency[theme] = theme_frequency.get(theme, 0) + 1
            
            return {
                'total_memories': len(memories),
                'memory_type_distribution': memory_types,
                'most_common_tags': sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
                'recurring_themes': sorted(theme_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
                'average_importance': sum(m.get('metadata', {}).get('importance_score', 0) for m in memories) / len(memories) if memories else 0,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory patterns for agent {agent_id}: {e}")
            return {}
    
    async def backup_agent(self, agent_id: str) -> Dict[str, Any]:
        """Create complete backup of agent data."""
        try:
            backup_data = {}
            
            # Get agent data
            backup_data['agent'] = await self.get_agent(agent_id)
            
            # Get interactions
            backup_data['interactions'] = await self.get_agent_interactions(agent_id, limit=1000)
            
            # Get memories
            backup_data['memories'] = await self.search_memories(agent_id, '', limit=1000)
            
            # Get evolution history
            backup_data['evolution_history'] = await self.get_agent_evolution_history(agent_id, limit=1000)
            
            backup_data['backup_timestamp'] = datetime.utcnow().isoformat()
            
            return backup_data
            
        except Exception as e:
            logger.error(f"Failed to backup agent {agent_id}: {e}")
            return {}
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """Run synchronous Firebase operations in thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    def close(self):
        """Close the executor."""
        self.executor.shutdown(wait=True)


# Global Firebase client instance
_firebase_client = None

def get_firebase_client() -> FirebaseClient:
    """Get singleton Firebase client."""
    global _firebase_client
    if _firebase_client is None:
        _firebase_client = FirebaseClient()
    return _firebase_client