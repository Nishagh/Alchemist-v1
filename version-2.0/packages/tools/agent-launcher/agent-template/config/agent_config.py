"""
Agent configuration loader that fetches agent data from Firestore
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import alchemist-shared components
from alchemist_shared.database import firebase_client
from alchemist_shared.constants.collections import Collections
from alchemist_shared.models.agent_models import Agent, DevelopmentStage
ALCHEMIST_SHARED_AVAILABLE = True

from .settings import settings

logger = logging.getLogger(__name__)

class AgentConfigLoader:
    """
    Loads agent configuration from Firestore with GNF integration
    """
    
    def __init__(self):
        if ALCHEMIST_SHARED_AVAILABLE:
            # Use alchemist-shared Firebase client
            self.firebase_client = firebase_client.get_firestore_client()
            if self.firebase_client:
                self.db = self.firebase_client
            else:
                raise Exception("Failed to get Firebase client from alchemist-shared")
    
    async def load_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """
        Load complete agent configuration with GNF data
        
        Args:
            agent_id: The agent identifier
            
        Returns:
            Complete agent configuration dictionary
        """
        try:
            logger.info(f"Loading configuration for agent: {agent_id}")
            
            # Load base agent configuration
            agent_data = await self._load_base_agent_config(agent_id)
            
            if not agent_data:
                raise ValueError(f"Agent {agent_id} not found in Firestore")
            
            # Enhance with GNF data if enabled
            if settings.enable_gnf:
                gnf_data = await self._load_gnf_data(agent_id)
                agent_data.update(gnf_data)
            
            # Add derived configuration
            agent_data.update({
                'agent_id': agent_id,
                'mcp_server_url': self._get_mcp_server_url(agent_id),
                'enable_gnf': settings.enable_gnf,
                'enable_knowledge_base': settings.enable_knowledge_base,
                'embedding_model': settings.get_embedding_model(),
                'accountability_settings': self._get_accountability_settings(),
                'loaded_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Successfully loaded configuration for agent {agent_id}")
            return agent_data
            
        except Exception as e:
            logger.error(f"Failed to load agent configuration for {agent_id}: {e}")
            raise
    
    async def _load_base_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load base agent configuration from agents collection"""
        try:
            collection_name = Collections.AGENTS if ALCHEMIST_SHARED_AVAILABLE else 'agents'
            agent_ref = self.db.collection(collection_name).document(agent_id)
            agent_doc = agent_ref.get()
            
            if not agent_doc.exists:
                logger.warning(f"Agent document {agent_id} not found")
                return None
            
            agent_data = agent_doc.to_dict()
            
            # Ensure required fields have defaults
            agent_data.setdefault('system_prompt', 'You are a helpful AI assistant.')
            agent_data.setdefault('model', settings.default_model)
            agent_data.setdefault('name', f'Agent {agent_id}')
            agent_data.setdefault('description', 'AI Agent')
            agent_data.setdefault('environment_variables', {})
            
            return agent_data
            
        except Exception as e:
            logger.error(f"Failed to load base agent config: {e}")
            return None
    
    async def _load_gnf_data(self, agent_id: str) -> Dict[str, Any]:
        """Load GNF-specific data for the agent"""
        gnf_data = {}
        
        try:
            # Load narrative identity if it exists
            narrative_identity = await self._load_narrative_identity(agent_id)
            if narrative_identity:
                gnf_data.update(narrative_identity)
            
            # Load agent metrics
            metrics = await self._load_agent_metrics(agent_id)
            if metrics:
                gnf_data.update(metrics)
            
            # Load narrative graph summary
            graph_summary = await self._load_narrative_graph_summary(agent_id)
            if graph_summary:
                gnf_data['narrative_graph_summary'] = graph_summary
            
            return gnf_data
            
        except Exception as e:
            logger.error(f"Failed to load GNF data: {e}")
            return {}
    
    async def _load_narrative_identity(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent narrative identity"""
        try:
            # Check if agent has narrative identity in main agent document
            collection_name = Collections.AGENTS if ALCHEMIST_SHARED_AVAILABLE else 'agents'
            agent_ref = self.db.collection(collection_name).document(agent_id)
            agent_doc = agent_ref.get()
            
            if agent_doc.exists:
                agent_data = agent_doc.to_dict()
                
                # Extract GNF fields
                gnf_fields = {}
                gnf_field_names = [
                    'narrative_identity_id', 'development_stage', 'narrative_coherence_score',
                    'responsibility_score', 'experience_points', 'total_narrative_interactions',
                    'defining_moments_count', 'current_narrative_arc', 'dominant_personality_traits',
                    'core_values', 'primary_goals', 'gnf_enabled', 'last_gnf_sync'
                ]
                
                for field in gnf_field_names:
                    if field in agent_data:
                        gnf_fields[field] = agent_data[field]
                
                # Set defaults for missing GNF fields
                gnf_fields.setdefault('development_stage', 'nascent')
                gnf_fields.setdefault('narrative_coherence_score', 0.5)
                gnf_fields.setdefault('responsibility_score', 0.5)
                gnf_fields.setdefault('experience_points', 0)
                gnf_fields.setdefault('total_narrative_interactions', 0)
                gnf_fields.setdefault('defining_moments_count', 0)
                gnf_fields.setdefault('dominant_personality_traits', [])
                gnf_fields.setdefault('core_values', [])
                gnf_fields.setdefault('primary_goals', [])
                gnf_fields.setdefault('gnf_enabled', True)
                
                return gnf_fields
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load narrative identity: {e}")
            return None
    
    async def _load_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load current agent metrics including story-loss"""
        try:
            metrics_collection = 'agent_metrics'
            metrics_ref = self.db.collection(metrics_collection).document(agent_id)
            metrics_doc = metrics_ref.get()
            
            if metrics_doc.exists:
                metrics_data = metrics_doc.to_dict()
                return {
                    'current_story_loss': metrics_data.get('story_loss', 0.0),
                    'metrics_last_updated': metrics_data.get('timestamp'),
                    'metrics_version': metrics_data.get('version', 1)
                }
            
            return {
                'current_story_loss': 0.0,
                'metrics_last_updated': None,
                'metrics_version': 1
            }
            
        except Exception as e:
            logger.error(f"Failed to load agent metrics: {e}")
            return None
    
    async def _load_narrative_graph_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load narrative graph summary"""
        try:
            graph_collection = 'agent_graphs'
            graph_ref = self.db.collection(graph_collection).document(agent_id)
            graph_doc = graph_ref.get()
            
            if graph_doc.exists:
                graph_data = graph_doc.to_dict()
                return {
                    'node_count': len(graph_data.get('nodes', [])),
                    'edge_count': len(graph_data.get('edges', [])),
                    'last_updated': graph_data.get('last_updated'),
                    'version': graph_data.get('version', 1)
                }
            
            return {
                'node_count': 0,
                'edge_count': 0,
                'last_updated': None,
                'version': 1
            }
            
        except Exception as e:
            logger.error(f"Failed to load narrative graph summary: {e}")
            return None
    
    def _get_mcp_server_url(self, agent_id: str) -> Optional[str]:
        """Get MCP server URL for the agent"""
        if not settings.enable_mcp_tools:
            return None
        return settings.get_mcp_server_url()
    
    def _get_accountability_settings(self) -> Dict[str, Any]:
        """Get accountability settings"""
        return {
            'story_loss_threshold': settings.story_loss_threshold,
            'responsibility_threshold': settings.responsibility_threshold,
            'narrative_coherence_threshold': settings.narrative_coherence_threshold,
            'enable_self_reflection': settings.enable_self_reflection,
            'development_stage_thresholds': settings.development_stage_thresholds
        }
    
    async def validate_agent_config(self, agent_config: Dict[str, Any]) -> bool:
        """Validate agent configuration"""
        try:
            required_fields = ['agent_id', 'system_prompt', 'model']
            
            for field in required_fields:
                if field not in agent_config:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate system prompt
            if not agent_config['system_prompt'].strip():
                logger.error("System prompt cannot be empty")
                return False
            
            # Validate model
            supported_models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-sonnet', 'claude-3-haiku']
            if agent_config['model'] not in supported_models:
                logger.warning(f"Model {agent_config['model']} may not be supported")
            
            logger.info("Agent configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Agent configuration validation failed: {e}")
            return False


# Global instance
agent_config_loader = AgentConfigLoader()