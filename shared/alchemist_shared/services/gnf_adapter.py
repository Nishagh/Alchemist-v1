"""
Global Narrative Framework (GNF) Adapter Service

This service acts as a bridge between the Alchemist platform and the Global Narrative Framework,
providing seamless integration for agent identity management, narrative tracking, and 
responsibility assessment.
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from firebase_admin import firestore

from ..database.firebase_client import FirebaseClient
from ..constants.collections import Collections, DocumentFields
from ..models.agent_models import Agent, DevelopmentStage

SERVER_TIMESTAMP = firestore.SERVER_TIMESTAMP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GNFError(Exception):
    """Custom exception for GNF operations."""
    pass


class InteractionType(str, Enum):
    """Types of agent interactions for narrative tracking."""
    CONVERSATION = "conversation"
    TASK_EXECUTION = "task_execution"
    PROBLEM_SOLVING = "problem_solving"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    MORAL_CHOICE = "moral_choice"
    CONFLICT = "conflict"
    ACHIEVEMENT = "achievement"
    FAILURE = "failure"
    RELATIONSHIP = "relationship"


class ImpactLevel(str, Enum):
    """Impact levels for narrative significance."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmotionalTone(str, Enum):
    """Emotional tones for interactions."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class GNFConfig:
    """Configuration for GNF service connection."""
    service_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class AgentIdentityData:
    """Data structure for agent identity creation."""
    agent_id: str
    name: str
    personality: Dict[str, Any]
    capabilities: Dict[str, Any]
    background: Optional[Dict[str, Any]] = None


@dataclass
class InteractionData:
    """Data structure for interaction tracking."""
    agent_id: str
    interaction_type: InteractionType
    content: str
    participants: List[str] = None
    context: Dict[str, Any] = None
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.participants is None:
            self.participants = []
        if self.context is None:
            self.context = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class GNFAdapter:
    """
    Adapter service for Global Narrative Framework integration.
    
    Provides high-level interface for:
    - Agent identity creation and management
    - Interaction tracking and narrative analysis
    - Responsibility assessment
    - Cross-agent relationship tracking
    """
    
    def __init__(self, config: GNFConfig, firebase_client: Optional[FirebaseClient] = None):
        """
        Initialize GNF adapter.
        
        Args:
            config: GNF service configuration
            firebase_client: Firebase client for data persistence
        """
        self.config = config
        self.firebase_client = firebase_client
        self.session: Optional[aiohttp.ClientSession] = None
        self._identity_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=15)
        self._last_cache_clear = datetime.utcnow()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize the GNF adapter."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Alchemist-GNF-Adapter/1.0'
            }
        )
        
        if self.config.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.api_key}'
            })
        
        # Test connection to GNF service
        try:
            await self._health_check()
            logger.info("GNF service connection established")
        except Exception as e:
            logger.warning(f"GNF service connection failed: {e}")
    
    async def close(self):
        """Close the adapter and cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _health_check(self) -> bool:
        """Check if GNF service is available."""
        if not self.session:
            return False
        
        try:
            async with self.session.get(f"{self.config.service_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"GNF health check failed: {e}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to GNF service with retry logic."""
        if not self.session:
            raise GNFError("GNF adapter not initialized")
        
        url = f"{self.config.service_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.request(method, url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        response_text = await response.text()
                        raise GNFError(f"GNF API error {response.status}: {response_text}")
            
            except aiohttp.ClientError as e:
                if attempt == self.config.retry_attempts - 1:
                    raise GNFError(f"GNF service unavailable after {self.config.retry_attempts} attempts: {e}")
                
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise GNFError("Maximum retry attempts exceeded")
    
    def _clear_expired_cache(self):
        """Clear expired cache entries."""
        now = datetime.utcnow()
        if now - self._last_cache_clear > self._cache_ttl:
            self._identity_cache.clear()
            self._last_cache_clear = now
    
    # ============================================================================
    # AGENT IDENTITY MANAGEMENT
    # ============================================================================
    
    async def create_agent_identity(self, identity_data: AgentIdentityData) -> str:
        """
        Create a new agent identity in GNF.
        
        Args:
            identity_data: Agent identity configuration
            
        Returns:
            GNF identity ID
            
        Raises:
            GNFError: If identity creation fails
        """
        logger.info(f"Creating GNF identity for agent {identity_data.agent_id}")
        
        # Prepare GNF identity payload
        gnf_payload = {
            'agent_id': identity_data.agent_id,
            'name': identity_data.name,
            'personality': identity_data.personality,
            'capabilities': identity_data.capabilities,
            'background': identity_data.background or {}
        }
        
        try:
            # Create identity via GNF API
            response = await self._make_request('POST', '/agents', gnf_payload)
            
            if not response:
                raise GNFError("Failed to create agent identity - no response")
            
            identity_id = response.get('identity_id') or response.get('agent_id')
            
            if not identity_id:
                raise GNFError("No identity ID returned from GNF service")
            
            # Store identity reference in Firebase
            if self.firebase_client:
                await self._store_identity_reference(identity_data.agent_id, identity_id)
            
            # Cache the identity data
            self._identity_cache[identity_data.agent_id] = {
                'identity_id': identity_id,
                'cached_at': datetime.utcnow(),
                'data': response
            }
            
            logger.info(f"Created GNF identity {identity_id} for agent {identity_data.agent_id}")
            return identity_id
            
        except Exception as e:
            logger.error(f"Failed to create GNF identity for agent {identity_data.agent_id}: {e}")
            raise GNFError(f"Identity creation failed: {e}")
    
    async def get_agent_identity(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent identity from GNF.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent identity data or None if not found
        """
        self._clear_expired_cache()
        
        # Check cache first
        if agent_id in self._identity_cache:
            cached = self._identity_cache[agent_id]
            if datetime.utcnow() - cached['cached_at'] < self._cache_ttl:
                return cached['data']
        
        try:
            # Fetch from GNF service
            response = await self._make_request('GET', f'/agents/{agent_id}')
            
            if response:
                # Update cache
                self._identity_cache[agent_id] = {
                    'identity_id': response.get('agent_id'),
                    'cached_at': datetime.utcnow(),
                    'data': response
                }
            
            return response
            
        except GNFError as e:
            logger.warning(f"Failed to fetch identity for agent {agent_id}: {e}")
            return None
    
    async def update_agent_identity(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update agent identity in GNF.
        
        Args:
            agent_id: Agent identifier
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self._make_request('PUT', f'/agents/{agent_id}', updates)
            
            if response:
                # Invalidate cache
                self._identity_cache.pop(agent_id, None)
                logger.info(f"Updated GNF identity for agent {agent_id}")
                return True
            
            return False
            
        except GNFError as e:
            logger.error(f"Failed to update identity for agent {agent_id}: {e}")
            return False
    
    # ============================================================================
    # INTERACTION TRACKING
    # ============================================================================
    
    async def track_interaction(self, interaction: InteractionData) -> Dict[str, Any]:
        """
        Track an agent interaction in GNF.
        
        Args:
            interaction: Interaction data to track
            
        Returns:
            Analysis results from GNF
        """
        logger.debug(f"Tracking interaction for agent {interaction.agent_id}: {interaction.interaction_type}")
        
        # Prepare interaction payload
        payload = {
            'agent_id': interaction.agent_id,
            'type': interaction.interaction_type.value,
            'content': interaction.content,
            'participants': interaction.participants,
            'context': interaction.context,
            'impact': interaction.impact_level.value,
            'emotional_tone': interaction.emotional_tone.value,
            'timestamp': interaction.timestamp.isoformat()
        }
        
        try:
            # Track via GNF API
            response = await self._make_request('POST', '/interactions', payload)
            
            if not response:
                logger.warning(f"No response from GNF interaction tracking for agent {interaction.agent_id}")
                return {}
            
            # Store interaction in Firebase if available
            if self.firebase_client:
                await self._store_interaction_record(interaction, response)
            
            # Clear agent cache to get fresh data
            self._identity_cache.pop(interaction.agent_id, None)
            
            logger.debug(f"Successfully tracked interaction for agent {interaction.agent_id}")
            return response
            
        except GNFError as e:
            logger.error(f"Failed to track interaction for agent {interaction.agent_id}: {e}")
            return {}
    
    async def get_agent_interactions(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent interactions for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of interactions to return
            
        Returns:
            List of interaction records
        """
        try:
            response = await self._make_request('GET', f'/agents/{agent_id}/interactions?limit={limit}')
            return response.get('interactions', []) if response else []
            
        except GNFError as e:
            logger.warning(f"Failed to fetch interactions for agent {agent_id}: {e}")
            return []
    
    # ============================================================================
    # RESPONSIBILITY TRACKING
    # ============================================================================
    
    async def track_agent_action(self, agent_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track an agent action for responsibility assessment.
        
        Args:
            agent_id: Agent identifier
            action_data: Action details and context
            
        Returns:
            Responsibility assessment results
        """
        logger.debug(f"Tracking action for agent {agent_id}: {action_data.get('action_type', 'unknown')}")
        
        payload = {
            'agent_id': agent_id,
            **action_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = await self._make_request('POST', f'/agents/{agent_id}/actions', payload)
            
            if response and self.firebase_client:
                await self._store_responsibility_assessment(agent_id, response)
            
            return response or {}
            
        except GNFError as e:
            logger.error(f"Failed to track action for agent {agent_id}: {e}")
            return {}
    
    async def get_responsibility_report(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get responsibility report for an agent.
        
        Args:
            agent_id: Agent identifier
            days: Number of days to include in report
            
        Returns:
            Responsibility report data
        """
        try:
            response = await self._make_request('GET', f'/agents/{agent_id}/responsibility/report?days={days}')
            return response or {}
            
        except GNFError as e:
            logger.warning(f"Failed to get responsibility report for agent {agent_id}: {e}")
            return {}
    
    # ============================================================================
    # ALCHEMIST INTEGRATION HELPERS
    # ============================================================================
    
    async def sync_agent_with_gnf(self, agent: Agent) -> bool:
        """
        Sync Alchemist agent with GNF data.
        
        Args:
            agent: Alchemist agent instance
            
        Returns:
            True if sync successful, False otherwise
        """
        if not agent.is_gnf_enabled():
            return False
        
        try:
            # Get current GNF data
            gnf_data = await self.get_agent_identity(agent.id)
            
            if not gnf_data:
                return False
            
            # Extract relevant fields for Alchemist agent
            summary = gnf_data.get('identity_summary', {})
            
            sync_data = {
                'development_stage': summary.get('development_stage', 'nascent'),
                'narrative_coherence_score': summary.get('narrative_coherence', 0.5),
                'responsibility_score': summary.get('responsibility_score', 0.5),
                'experience_points': summary.get('experience_level', 0),
                'total_interactions': summary.get('total_interactions', 0),
                'defining_moments_count': summary.get('defining_moments', 0),
                'current_arc': summary.get('current_arc'),
                'dominant_traits': [trait['name'] for trait in summary.get('key_traits', [])[:5]],
                'core_values': summary.get('core_values', []),
                'primary_goals': summary.get('goals', [])
            }
            
            # Update agent with GNF data
            agent.update_gnf_data(sync_data)
            
            logger.info(f"Successfully synced agent {agent.id} with GNF")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync agent {agent.id} with GNF: {e}")
            return False
    
    async def create_identity_for_agent(self, agent: Agent) -> bool:
        """
        Create GNF identity for an existing Alchemist agent.
        
        Args:
            agent: Alchemist agent instance
            
        Returns:
            True if identity created successfully, False otherwise
        """
        if agent.has_narrative_identity():
            return True  # Already has identity
        
        try:
            # Extract identity data from agent
            identity_data = AgentIdentityData(
                agent_id=agent.id,
                name=agent.config.name,
                personality={
                    'traits': agent.dominant_personality_traits or ['helpful', 'responsive'],
                    'values': agent.core_values or ['efficiency', 'accuracy'],
                    'goals': agent.primary_goals or ['assist users effectively']
                },
                capabilities={
                    'knowledge_domains': agent.config.domain.split(',') if agent.config.domain else ['general'],
                    'skills': ['conversation', 'problem_solving'],
                    'use_cases': agent.config.use_cases
                },
                background={
                    'origin': f"Created as {agent.config.name} for {agent.config.description or 'general assistance'}",
                    'creation_date': agent.created_at.isoformat()
                }
            )
            
            # Create identity in GNF
            identity_id = await self.create_agent_identity(identity_data)
            
            # Update agent with identity reference
            agent.set_narrative_identity(identity_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create GNF identity for agent {agent.id}: {e}")
            return False
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    async def _store_identity_reference(self, agent_id: str, identity_id: str):
        """Store identity reference in Firebase."""
        if not self.firebase_client:
            return
        
        try:
            await self.firebase_client.update_document(
                Collections.AGENTS,
                agent_id,
                {
                    DocumentFields.GNF.NARRATIVE_IDENTITY_ID: identity_id,
                    DocumentFields.UPDATED_AT: SERVER_TIMESTAMP
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store identity reference in Firebase: {e}")
    
    async def _store_interaction_record(self, interaction: InteractionData, gnf_response: Dict[str, Any]):
        """Store interaction record in Firebase."""
        if not self.firebase_client:
            return
        
        try:
            record = {
                DocumentFields.AGENT_ID: interaction.agent_id,
                DocumentFields.GNF.INTERACTION_TYPE: interaction.interaction_type.value,
                'content': interaction.content,
                DocumentFields.GNF.PARTICIPANTS: interaction.participants,
                DocumentFields.GNF.IMPACT_LEVEL: interaction.impact_level.value,
                DocumentFields.GNF.EMOTIONAL_TONE: interaction.emotional_tone.value,
                DocumentFields.GNF.NARRATIVE_SIGNIFICANCE: gnf_response.get('narrative_significance', 0.0),
                DocumentFields.GNF.RESPONSIBILITY_IMPACT: gnf_response.get('responsibility_impact', 0.0),
                DocumentFields.TIMESTAMP: interaction.timestamp,
                DocumentFields.CREATED_AT: SERVER_TIMESTAMP
            }
            
            await self.firebase_client.add_document(Collections.AGENT_INTERACTIONS, record)
            
        except Exception as e:
            logger.warning(f"Failed to store interaction record in Firebase: {e}")
    
    async def _store_responsibility_assessment(self, agent_id: str, assessment: Dict[str, Any]):
        """Store responsibility assessment in Firebase."""
        if not self.firebase_client:
            return
        
        try:
            record = {
                DocumentFields.AGENT_ID: agent_id,
                DocumentFields.GNF.RESPONSIBILITY_LEVEL: assessment.get('responsibility_level'),
                DocumentFields.GNF.ACCOUNTABILITY_SCORE: assessment.get('accountability_score', 0.0),
                DocumentFields.GNF.ETHICAL_WEIGHT: assessment.get('ethical_weight', 0.0),
                DocumentFields.GNF.CONTRIBUTING_FACTORS: assessment.get('contributing_factors', []),
                DocumentFields.CREATED_AT: SERVER_TIMESTAMP
            }
            
            await self.firebase_client.add_document(Collections.RESPONSIBILITY_ASSESSMENTS, record)
            
        except Exception as e:
            logger.warning(f"Failed to store responsibility assessment in Firebase: {e}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_gnf_adapter(service_url: str, api_key: Optional[str] = None, 
                      firebase_client: Optional[FirebaseClient] = None) -> GNFAdapter:
    """
    Create a GNF adapter with default configuration.
    
    Args:
        service_url: URL of the GNF service
        api_key: Optional API key for authentication
        firebase_client: Optional Firebase client for data persistence
        
    Returns:
        Configured GNF adapter instance
    """
    config = GNFConfig(
        service_url=service_url,
        api_key=api_key,
        timeout=30,
        retry_attempts=3,
        retry_delay=1.0
    )
    
    return GNFAdapter(config, firebase_client)


async def track_conversation_interaction(adapter: GNFAdapter, agent_id: str, 
                                       user_message: str, agent_response: str,
                                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to track a conversation interaction.
    
    Args:
        adapter: GNF adapter instance
        agent_id: Agent identifier
        user_message: User's message
        agent_response: Agent's response
        context: Optional context information
        
    Returns:
        GNF analysis results
    """
    interaction = InteractionData(
        agent_id=agent_id,
        interaction_type=InteractionType.CONVERSATION,
        content=f"User: {user_message}\nAgent: {agent_response}",
        context=context or {},
        impact_level=ImpactLevel.MEDIUM,
        emotional_tone=EmotionalTone.NEUTRAL
    )
    
    return await adapter.track_interaction(interaction)