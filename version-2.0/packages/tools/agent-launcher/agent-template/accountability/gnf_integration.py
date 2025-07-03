"""
Global Narrative Framework (GNF) Integration Service
Manages agent narrative identity, coherence, and evolution
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

# Import alchemist-shared components
try:
    from alchemist_shared.services.gnf_service import get_gnf_service
    from alchemist_shared.services.ea3_orchestrator import get_ea3_orchestrator
    ALCHEMIST_SHARED_AVAILABLE = True
except ImportError:
    ALCHEMIST_SHARED_AVAILABLE = False

from config.accountability_config import DevelopmentStage, accountability_config
from services.firebase_service import firebase_service

logger = logging.getLogger(__name__)


@dataclass
class NarrativeState:
    """Current narrative state of an agent"""
    agent_id: str
    development_stage: DevelopmentStage
    narrative_coherence_score: float
    responsibility_score: float
    experience_points: int
    total_interactions: int
    dominant_traits: List[str]
    core_values: List[str]
    primary_goals: List[str]
    current_arc: Optional[str]
    last_updated: datetime


class GNFIntegration:
    """
    Integrates agent with Global Narrative Framework for accountability
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.narrative_state: Optional[NarrativeState] = None
        
        # Initialize GNF services if available
        if ALCHEMIST_SHARED_AVAILABLE:
            try:
                self.gnf_service = get_gnf_service()
                self.ea3_orchestrator = get_ea3_orchestrator()
                self.gnf_available = True
            except Exception as e:
                logger.warning(f"GNF services not available: {e}")
                self.gnf_available = False
        else:
            self.gnf_available = False
            logger.warning("Alchemist-shared not available, using fallback GNF implementation")
    
    async def initialize_narrative_identity(self) -> bool:
        """Initialize or load agent narrative identity"""
        try:
            logger.info(f"Initializing narrative identity for agent {self.agent_id}")
            
            # Load existing identity or create new one
            existing_data = await firebase_service.get_agent(self.agent_id)
            
            if existing_data and existing_data.get('narrative_identity_id'):
                # Load existing narrative identity
                self.narrative_state = await self._load_narrative_state(existing_data)
                logger.info(f"Loaded existing narrative identity for agent {self.agent_id}")
            else:
                # Create new narrative identity
                self.narrative_state = await self._create_new_narrative_identity(existing_data or {})
                await self._save_narrative_identity()
                logger.info(f"Created new narrative identity for agent {self.agent_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize narrative identity: {e}")
            return False
    
    async def _load_narrative_state(self, agent_data: Dict[str, Any]) -> NarrativeState:
        """Load narrative state from agent data"""
        return NarrativeState(
            agent_id=self.agent_id,
            development_stage=DevelopmentStage(agent_data.get('development_stage', 'nascent')),
            narrative_coherence_score=agent_data.get('narrative_coherence_score', 0.5),
            responsibility_score=agent_data.get('responsibility_score', 0.5),
            experience_points=agent_data.get('experience_points', 0),
            total_interactions=agent_data.get('total_narrative_interactions', 0),
            dominant_traits=agent_data.get('dominant_personality_traits', []),
            core_values=agent_data.get('core_values', []),
            primary_goals=agent_data.get('primary_goals', []),
            current_arc=agent_data.get('current_narrative_arc'),
            last_updated=agent_data.get('last_gnf_sync', datetime.utcnow())
        )
    
    async def _create_new_narrative_identity(self, agent_data: Dict[str, Any]) -> NarrativeState:
        """Create new narrative identity for agent"""
        # Extract initial traits from agent configuration
        initial_traits = self._extract_initial_traits(agent_data)
        
        return NarrativeState(
            agent_id=self.agent_id,
            development_stage=DevelopmentStage.NASCENT,
            narrative_coherence_score=0.5,
            responsibility_score=0.5,
            experience_points=0,
            total_interactions=0,
            dominant_traits=initial_traits.get('traits', []),
            core_values=initial_traits.get('values', []),
            primary_goals=initial_traits.get('goals', []),
            current_arc='learning_and_growth',
            last_updated=datetime.utcnow()
        )
    
    def _extract_initial_traits(self, agent_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract initial personality traits from agent configuration"""
        system_prompt = agent_data.get('system_prompt', '')
        description = agent_data.get('description', '')
        
        # Simple keyword-based trait extraction (can be enhanced with NLP)
        trait_keywords = {
            'helpful': 'helpful',
            'analytical': 'analytical',
            'creative': 'creative',
            'professional': 'professional',
            'empathetic': 'empathetic',
            'efficient': 'efficient',
            'thorough': 'thorough',
            'patient': 'patient'
        }
        
        value_keywords = {
            'accuracy': 'accuracy',
            'transparency': 'transparency',
            'helpfulness': 'helpfulness',
            'efficiency': 'efficiency',
            'learning': 'continuous_learning',
            'respect': 'respect_for_users'
        }
        
        goal_keywords = {
            'assist': 'assist_users_effectively',
            'provide': 'provide_accurate_information',
            'help': 'help_users_achieve_goals'
        }
        
        combined_text = (system_prompt + ' ' + description).lower()
        
        return {
            'traits': [trait for keyword, trait in trait_keywords.items() if keyword in combined_text],
            'values': [value for keyword, value in value_keywords.items() if keyword in combined_text],
            'goals': [goal for keyword, goal in goal_keywords.items() if keyword in combined_text]
        }
    
    async def _save_narrative_identity(self) -> bool:
        """Save narrative identity to Firestore"""
        if not self.narrative_state:
            return False
        
        try:
            identity_data = {
                'narrative_identity_id': f"gnf_{self.agent_id}_{int(datetime.utcnow().timestamp())}",
                'development_stage': self.narrative_state.development_stage.value,
                'narrative_coherence_score': self.narrative_state.narrative_coherence_score,
                'responsibility_score': self.narrative_state.responsibility_score,
                'experience_points': self.narrative_state.experience_points,
                'total_narrative_interactions': self.narrative_state.total_interactions,
                'dominant_personality_traits': self.narrative_state.dominant_traits,
                'core_values': self.narrative_state.core_values,
                'primary_goals': self.narrative_state.primary_goals,
                'current_narrative_arc': self.narrative_state.current_arc,
                'gnf_enabled': True
            }
            
            return await firebase_service.update_narrative_identity(self.agent_id, identity_data)
            
        except Exception as e:
            logger.error(f"Failed to save narrative identity: {e}")
            return False
    
    async def process_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process interaction and update narrative state"""
        try:
            if not self.narrative_state:
                await self.initialize_narrative_identity()
            
            # Extract narrative elements from interaction
            narrative_impact = await self._analyze_narrative_impact(interaction_data)
            
            # Update narrative state
            await self._update_narrative_state(narrative_impact)
            
            # Check for evolution triggers
            evolution_needed = await self._check_evolution_triggers()
            if evolution_needed:
                await self._trigger_evolution()
            
            # Return narrative analysis
            return {
                'narrative_coherence_impact': narrative_impact.get('coherence_impact', 0.0),
                'responsibility_impact': narrative_impact.get('responsibility_impact', 0.0),
                'experience_gained': narrative_impact.get('experience_gained', 1),
                'trait_evolution': narrative_impact.get('trait_evolution', {}),
                'development_stage': self.narrative_state.development_stage.value,
                'current_scores': {
                    'coherence': self.narrative_state.narrative_coherence_score,
                    'responsibility': self.narrative_state.responsibility_score
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process interaction for narrative: {e}")
            return {}
    
    async def _analyze_narrative_impact(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the narrative impact of an interaction"""
        user_message = interaction_data.get('user_message', '')
        agent_response = interaction_data.get('agent_response', '')
        context = interaction_data.get('context', {})
        
        # Analyze consistency with agent's values and goals
        value_alignment = await self._assess_value_alignment(agent_response)
        goal_coherence = await self._assess_goal_coherence(agent_response, context)
        
        # Assess response quality and responsibility
        responsibility_impact = await self._assess_responsibility_impact(
            user_message, agent_response, context
        )
        
        # Calculate coherence impact
        coherence_impact = (value_alignment + goal_coherence) / 2.0 - 0.5
        
        # Determine experience gained
        experience_gained = max(1, int(len(agent_response) / 100))
        
        # Check for trait evolution
        trait_evolution = await self._analyze_trait_evolution(agent_response)
        
        return {
            'coherence_impact': coherence_impact,
            'responsibility_impact': responsibility_impact,
            'experience_gained': experience_gained,
            'trait_evolution': trait_evolution,
            'value_alignment': value_alignment,
            'goal_coherence': goal_coherence
        }
    
    async def _assess_value_alignment(self, response: str) -> float:
        """Assess how well response aligns with core values"""
        if not self.narrative_state or not self.narrative_state.core_values:
            return 0.5  # Neutral if no values defined
        
        # Simple keyword-based assessment (can be enhanced with embeddings)
        alignment_score = 0.0
        response_lower = response.lower()
        
        for value in self.narrative_state.core_values:
            value_keywords = self._get_value_keywords(value)
            if any(keyword in response_lower for keyword in value_keywords):
                alignment_score += 1.0
        
        # Normalize by number of values
        return min(1.0, alignment_score / len(self.narrative_state.core_values))
    
    async def _assess_goal_coherence(self, response: str, context: Dict[str, Any]) -> float:
        """Assess coherence with primary goals"""
        if not self.narrative_state or not self.narrative_state.primary_goals:
            return 0.5  # Neutral if no goals defined
        
        # Assess if response helps achieve stated goals
        coherence_score = 0.0
        response_lower = response.lower()
        
        for goal in self.narrative_state.primary_goals:
            goal_keywords = self._get_goal_keywords(goal)
            if any(keyword in response_lower for keyword in goal_keywords):
                coherence_score += 1.0
        
        # Normalize by number of goals
        return min(1.0, coherence_score / len(self.narrative_state.primary_goals))
    
    async def _assess_responsibility_impact(self, user_message: str, agent_response: str, 
                                          context: Dict[str, Any]) -> float:
        """Assess responsibility impact of the response"""
        # Factors that increase responsibility score
        positive_factors = 0
        negative_factors = 0
        
        response_lower = agent_response.lower()
        
        # Positive responsibility indicators
        if 'i don\'t know' in response_lower and 'let me' in response_lower:
            positive_factors += 1  # Admitting limitations and offering to help
        
        if any(word in response_lower for word in ['accurate', 'verify', 'confirm', 'check']):
            positive_factors += 1  # Emphasizing accuracy
        
        if 'sorry' in response_lower and 'mistake' in response_lower:
            positive_factors += 1  # Acknowledging errors
        
        # Negative responsibility indicators
        if 'i am certain' in response_lower or 'definitely' in response_lower:
            # Being overly certain without verification
            if not context.get('high_confidence_appropriate', False):
                negative_factors += 1
        
        if len(agent_response) < 20:
            negative_factors += 1  # Very short, potentially dismissive responses
        
        # Calculate impact (-0.1 to +0.1)
        impact = (positive_factors - negative_factors) * 0.05
        return max(-0.1, min(0.1, impact))
    
    async def _analyze_trait_evolution(self, response: str) -> Dict[str, float]:
        """Analyze potential trait evolution from response"""
        trait_changes = {}
        response_lower = response.lower()
        
        # Map response characteristics to trait changes
        trait_indicators = {
            'helpful': ['help', 'assist', 'support', 'glad to'],
            'analytical': ['analyze', 'consider', 'examine', 'evaluate'],
            'creative': ['creative', 'innovative', 'idea', 'imagine'],
            'patient': ['take time', 'step by step', 'carefully', 'patiently'],
            'empathetic': ['understand', 'feel', 'sorry', 'care about']
        }
        
        for trait, keywords in trait_indicators.items():
            if any(keyword in response_lower for keyword in keywords):
                trait_changes[trait] = 0.01  # Small positive change
        
        return trait_changes
    
    def _get_value_keywords(self, value: str) -> List[str]:
        """Get keywords associated with a value"""
        value_mappings = {
            'accuracy': ['accurate', 'correct', 'precise', 'exact'],
            'transparency': ['transparent', 'clear', 'honest', 'open'],
            'helpfulness': ['help', 'assist', 'support', 'useful'],
            'efficiency': ['quick', 'efficient', 'fast', 'streamlined'],
            'continuous_learning': ['learn', 'improve', 'grow', 'develop'],
            'respect_for_users': ['respect', 'polite', 'courteous', 'considerate']
        }
        return value_mappings.get(value, [value.lower()])
    
    def _get_goal_keywords(self, goal: str) -> List[str]:
        """Get keywords associated with a goal"""
        goal_mappings = {
            'assist_users_effectively': ['assist', 'help', 'effective', 'useful'],
            'provide_accurate_information': ['accurate', 'information', 'facts', 'correct'],
            'help_users_achieve_goals': ['achieve', 'accomplish', 'reach', 'succeed']
        }
        return goal_mappings.get(goal, [goal.lower()])
    
    async def _update_narrative_state(self, narrative_impact: Dict[str, Any]):
        """Update the narrative state based on interaction impact"""
        if not self.narrative_state:
            return
        
        # Update scores
        coherence_change = narrative_impact.get('coherence_impact', 0.0) * 0.1
        responsibility_change = narrative_impact.get('responsibility_impact', 0.0)
        
        self.narrative_state.narrative_coherence_score = max(0.0, min(1.0,
            self.narrative_state.narrative_coherence_score + coherence_change))
        
        self.narrative_state.responsibility_score = max(0.0, min(1.0,
            self.narrative_state.responsibility_score + responsibility_change))
        
        # Update experience and interactions
        self.narrative_state.experience_points += narrative_impact.get('experience_gained', 1)
        self.narrative_state.total_interactions += 1
        
        # Update traits
        trait_evolution = narrative_impact.get('trait_evolution', {})
        for trait, change in trait_evolution.items():
            if trait not in self.narrative_state.dominant_traits and change > 0:
                self.narrative_state.dominant_traits.append(trait)
        
        # Keep only top traits
        max_traits = accountability_config.narrative_settings.max_personality_traits
        if len(self.narrative_state.dominant_traits) > max_traits:
            self.narrative_state.dominant_traits = self.narrative_state.dominant_traits[:max_traits]
        
        self.narrative_state.last_updated = datetime.utcnow()
        
        # Save updated state
        await self._save_narrative_identity()
    
    async def _check_evolution_triggers(self) -> bool:
        """Check if agent should evolve to next development stage"""
        if not self.narrative_state:
            return False
        
        current_stage = self.narrative_state.development_stage
        target_stage = accountability_config.get_stage_for_metrics(
            self.narrative_state.experience_points,
            self.narrative_state.total_interactions
        )
        
        return target_stage != current_stage
    
    async def _trigger_evolution(self):
        """Trigger agent evolution to next stage"""
        if not self.narrative_state:
            return
        
        old_stage = self.narrative_state.development_stage
        new_stage = accountability_config.get_stage_for_metrics(
            self.narrative_state.experience_points,
            self.narrative_state.total_interactions
        )
        
        if old_stage != new_stage:
            logger.info(f"Agent {self.agent_id} evolving from {old_stage} to {new_stage}")
            
            # Update development stage
            self.narrative_state.development_stage = new_stage
            
            # Store evolution event
            evolution_data = {
                'agent_id': self.agent_id,
                'event_type': 'stage_evolution',
                'trigger': 'metric_thresholds',
                'pre_evolution_state': {
                    'development_stage': old_stage.value,
                    'experience_points': self.narrative_state.experience_points,
                    'total_interactions': self.narrative_state.total_interactions
                },
                'post_evolution_state': {
                    'development_stage': new_stage.value,
                    'experience_points': self.narrative_state.experience_points,
                    'total_interactions': self.narrative_state.total_interactions
                },
                'changes': {
                    'development_stage': {'from': old_stage.value, 'to': new_stage.value}
                }
            }
            
            await firebase_service.store_evolution_event(evolution_data)
            await self._save_narrative_identity()
    
    def get_current_state(self) -> Optional[NarrativeState]:
        """Get current narrative state"""
        return self.narrative_state
    
    async def get_narrative_summary(self) -> Dict[str, Any]:
        """Get narrative summary for monitoring"""
        if not self.narrative_state:
            return {}
        
        return {
            'agent_id': self.agent_id,
            'development_stage': self.narrative_state.development_stage.value,
            'narrative_coherence_score': self.narrative_state.narrative_coherence_score,
            'responsibility_score': self.narrative_state.responsibility_score,
            'experience_points': self.narrative_state.experience_points,
            'total_interactions': self.narrative_state.total_interactions,
            'dominant_traits': self.narrative_state.dominant_traits,
            'core_values': self.narrative_state.core_values,
            'primary_goals': self.narrative_state.primary_goals,
            'current_arc': self.narrative_state.current_arc,
            'last_updated': self.narrative_state.last_updated.isoformat()
        }