"""
Narrative Tracker - Core narrative processing and cross-agent interaction management.
"""

import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import defaultdict

from .identity_schema import AgentIdentity
from ..storage.firebase_client import FirebaseClient
from ..storage.collection_constants import (
    AGENTS, CONVERSATIONS, AGENT_MEMORIES, AGENT_EVOLUTION_EVENTS,
    AGENT_RESPONSIBILITY_RECORDS, CROSS_AGENT_INTERACTIONS, 
    GLOBAL_NARRATIVE_TIMELINE, AgentFields, ConversationFields
)
from ..storage.models import (
    InteractionRecord, GlobalEvent, DevelopmentStage,
    InteractionType, ImpactLevel, EmotionalTone, AgentIdentityFirebase
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NarrativeAnalysis:
    """Results of narrative analysis for an interaction."""
    
    def __init__(self):
        self.personality_impact = False
        self.experience_significance = 0.0
        self.arc_transition = False
        self.character_development = None
        self.learning_outcome = ""
        self.tags = []
        self.new_arc = ""
        self.arc_context = ""
        self.responsibility_impact = 0.0
        self.ethical_implications = []


class NarrativeTracker:
    """
    Core narrative tracking system that processes agent interactions and maintains
    coherent narrative development across all agents.
    """
    
    def __init__(self, firebase_client: Optional[FirebaseClient] = None):
        self.firebase_client = firebase_client
        self.agents: Dict[str, AgentIdentity] = {}
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.global_narrative = {
            'threads': [],
            'cross_agent_events': [],
            'world_state': {},
            'timeline': []
        }
        
        # Narrative analysis configuration
        self.narrative_rules = self._setup_narrative_rules()
        self.evolution_thresholds = self._setup_evolution_thresholds()
        
    def _setup_narrative_rules(self) -> Dict[str, Any]:
        """Setup narrative analysis rules."""
        return {
            'personality_development': {
                'interaction_threshold': 3,
                'significance_threshold': 0.6,
                'reinforcement_patterns': [
                    'repeated_behavior',
                    'consistent_choices',
                    'value_alignment'
                ]
            },
            'arc_progression': {
                'experience_thresholds': {
                    DevelopmentStage.NASCENT: 5,
                    DevelopmentStage.DEVELOPING: 15,
                    DevelopmentStage.ESTABLISHED: 30,
                    DevelopmentStage.MATURE: 50
                },
                'transition_triggers': [
                    'major_conflict',
                    'significant_achievement',
                    'relationship_milestone',
                    'moral_crisis',
                    'learning_breakthrough'
                ]
            },
            'responsibility_tracking': {
                'action_weight_threshold': 0.7,
                'ethical_significance_threshold': 0.5,
                'consequence_tracking_depth': 3
            }
        }
    
    def _setup_evolution_thresholds(self) -> Dict[str, float]:
        """Setup thresholds for triggering evolution events."""
        return {
            'personality_shift': 0.7,
            'behavioral_change': 0.5,
            'narrative_coherence': 0.6,
            'responsibility_development': 0.6,
            'relationship_depth': 0.8
        }
    
    async def create_agent(self, agent_id: str, config: Optional[Dict[str, Any]] = None) -> AgentIdentity:
        """Create a new agent with narrative tracking."""
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already exists")
        
        # Create agent identity
        agent = AgentIdentity(agent_id, config)
        agent.name = config.get('name', f"Agent-{agent_id}") if config else f"Agent-{agent_id}"
        self.agents[agent_id] = agent
        
        # Store in Firebase with enhanced structure
        if self.firebase_client:
            try:
                # Create enhanced agent document structure
                agent_document = {
                    AgentFields.AGENT_ID: agent_id,
                    AgentFields.NAME: agent.name,
                    AgentFields.DESCRIPTION: config.get('description', f'AI Agent {agent.name}') if config else f'AI Agent {agent.name}',
                    AgentFields.TYPE: config.get('type', 'general') if config else 'general',
                    AgentFields.OWNER_ID: config.get('owner_id', 'system') if config else 'system',
                    AgentFields.DEPLOYMENT_STATUS: 'pending',
                    AgentFields.CREATED_AT: datetime.utcnow(),
                    AgentFields.UPDATED_AT: datetime.utcnow(),
                    
                    # Initialize GNF identity structure
                    'gnf_identity': agent.to_firebase_model().dict().get('core', {}),
                    
                    # Initialize GNF metadata
                    'gnf_metadata': {
                        'gnf_enabled': True,
                        'gnf_version': '2.0.0',
                        'last_narrative_update': datetime.utcnow(),
                        'total_interactions_tracked': 0,
                        'narrative_coherence_score': 0.5,
                        'identity_stability_score': 0.5
                    }
                }
                
                await self.firebase_client.create_agent(agent_document)
            except Exception as e:
                logger.error(f"Failed to store agent {agent_id} in Firebase: {e}")
        
        # Create global event using enhanced structure
        creation_event = GlobalEvent(
            event_type='agent_creation',
            description=f"Agent {agent.name} ({agent_id}) was created",
            participants=[agent_id],
            data={'name': agent.name, 'config': config or {}}
        )
        
        await self._store_global_event(creation_event)
        
        # Emit event
        await self._emit_event('agent_created', {
            'agent_id': agent_id,
            'agent': agent,
            'config': config
        })
        
        # Record lifecycle event for agent creation
        try:
            from alchemist_shared.services.agent_lifecycle_service import get_agent_lifecycle_service
            lifecycle_service = get_agent_lifecycle_service()
            if lifecycle_service:
                await lifecycle_service.record_agent_created(
                    agent_id=agent_id,
                    agent_name=agent.name,
                    user_id=config.get('owner_id', 'system') if config else 'system',
                    metadata={
                        'gnf_created': True,
                        'development_stage': agent.development_stage.value if hasattr(agent, 'development_stage') else 'nascent',
                        'personality_traits': [trait.name for trait in agent.core.traits][:5] if hasattr(agent, 'core') and hasattr(agent.core, 'traits') else [],
                        'narrative_voice': agent.narrative.narrative_voice if hasattr(agent, 'narrative') else 'first_person'
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to record lifecycle event for agent creation: {e}")
        
        logger.info(f"Created agent: {agent_id} ({agent.name})")
        return agent
    
    async def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent by ID, loading from Firebase if not in memory."""
        if agent_id in self.agents:
            return self.agents[agent_id]
        
        # Try loading from Firebase
        if self.firebase_client:
            try:
                agent_data = await self.firebase_client.get_agent(agent_id)
                if agent_data:
                    firebase_model = AgentIdentityFirebase(**agent_data)
                    agent = AgentIdentity.from_firebase_model(firebase_model)
                    self.agents[agent_id] = agent
                    return agent
            except Exception as e:
                logger.error(f"Failed to load agent {agent_id} from Firebase: {e}")
        
        return None
    
    async def track_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track and process an agent interaction, analyzing its narrative implications.
        """
        agent_id = interaction_data['agent_id']
        agent = await self.get_agent(agent_id)
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Create interaction record
        interaction = InteractionRecord(
            agent_id=agent_id,
            interaction_type=InteractionType(interaction_data.get('type', 'conversation')),
            content=interaction_data['content'],
            participants=interaction_data.get('participants', []),
            context=interaction_data.get('context', {}),
            impact_level=ImpactLevel(interaction_data.get('impact', 'medium')),
            emotional_tone=EmotionalTone(interaction_data.get('emotional_tone', 'neutral'))
        )
        
        # Analyze narrative implications
        analysis = await self._analyze_narrative_implications(interaction, agent)
        
        # Update interaction with analysis results
        interaction.narrative_significance = analysis.experience_significance
        interaction.personality_impact = analysis.personality_impact.__dict__ if hasattr(analysis.personality_impact, '__dict__') else {}
        interaction.learning_outcome = analysis.learning_outcome
        interaction.responsibility_impact = analysis.responsibility_impact
        
        # Process narrative updates
        await self._process_narrative_updates(agent, interaction, analysis)
        
        # Store interaction using enhanced conversation structure
        if self.firebase_client:
            try:
                # Create enhanced conversation document
                conversation_data = {
                    ConversationFields.AGENT_ID: agent_id,
                    ConversationFields.MESSAGE_CONTENT: interaction.content,
                    ConversationFields.AGENT_RESPONSE: interaction.context.get('response', ''),
                    ConversationFields.IS_PRODUCTION: interaction.context.get('is_production', False),
                    ConversationFields.DEPLOYMENT_TYPE: interaction.context.get('deployment_type', 'pre_deployment'),
                    ConversationFields.TIMESTAMP: datetime.utcnow(),
                    ConversationFields.CREATED_AT: datetime.utcnow(),
                    
                    # GNF Analysis fields
                    'gnf_analysis': {
                        'narrative_analysis': {
                            'narrative_significance': analysis.experience_significance,
                            'interaction_type': interaction.interaction_type.value,
                            'impact_level': interaction.impact_level.value,
                            'emotional_tone': interaction.emotional_tone.value,
                            'personality_impact': analysis.personality_impact.__dict__ if hasattr(analysis.personality_impact, '__dict__') else {},
                            'learning_outcome': {'knowledge_gained': analysis.learning_outcome},
                            'responsibility_impact': {'responsibility_level': analysis.responsibility_impact}
                        },
                        'cross_agent_data': {
                            'participants': interaction.participants
                        }
                    },
                    
                    # GNF Processing metadata
                    'gnf_processing': {
                        'analysis_completed': True,
                        'processing_time_ms': 0,
                        'memory_consolidation_triggered': analysis.experience_significance > 0.5,
                        'evolution_check_performed': True,
                        'gnf_version': '2.0.0'
                    }
                }
                
                await self.firebase_client.store_interaction(conversation_data)
            except Exception as e:
                logger.error(f"Failed to store interaction: {e}")
        
        # Update agent in Firebase
        await self._persist_agent(agent)
        
        # Handle cross-agent interactions
        if len(interaction.participants) > 1:
            await self._process_cross_agent_interaction(interaction, analysis)
        
        # Emit event
        await self._emit_event('interaction_tracked', {
            'agent_id': agent_id,
            'interaction': interaction,
            'analysis': analysis
        })
        
        # Record lifecycle event for significant interactions
        if analysis.experience_significance > 0.7:  # Only record high-significance interactions
            try:
                from alchemist_shared.services.agent_lifecycle_service import get_agent_lifecycle_service
                lifecycle_service = get_agent_lifecycle_service()
                if lifecycle_service:
                    from alchemist_shared.events.story_events import StoryEventType
                    await lifecycle_service.record_event(
                        agent_id=agent_id,
                        event_type=StoryEventType.CONVERSATION,
                        title=f"Significant {interaction.interaction_type.value} interaction",
                        description=f"Agent had a significant interaction: {interaction.content[:100]}...",
                        user_id=interaction_data.get('user_id', 'system'),
                        metadata={
                            'gnf_interaction': True,
                            'narrative_significance': analysis.experience_significance,
                            'personality_impact': analysis.personality_impact,
                            'emotional_tone': interaction.emotional_tone.value,
                            'impact_level': interaction.impact_level.value,
                            'learning_outcome': analysis.learning_outcome
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to record lifecycle event for interaction: {e}")
        
        return {
            'interaction_id': f"int_{uuid.uuid4().hex[:8]}",
            'narrative_impact': analysis.__dict__,
            'agent_state': agent.get_identity_summary()
        }
    
    async def _analyze_narrative_implications(self, interaction: InteractionRecord, agent: AgentIdentity) -> NarrativeAnalysis:
        """Analyze the narrative implications of an interaction."""
        analysis = NarrativeAnalysis()
        
        # Calculate experience significance
        analysis.experience_significance = self._calculate_experience_significance(interaction, agent)
        
        # Check for personality impact
        if self._should_trigger_personality_update(interaction, agent):
            analysis.personality_impact = True
        
        # Analyze arc progression
        arc_analysis = self._analyze_arc_progression(interaction, agent)
        if arc_analysis['should_transition']:
            analysis.arc_transition = True
            analysis.new_arc = arc_analysis['new_arc']
            analysis.arc_context = arc_analysis['context']
        
        # Analyze character development
        dev_analysis = self._analyze_character_development(interaction, agent)
        if dev_analysis['has_development']:
            analysis.character_development = dev_analysis['development']
        
        # Extract learning outcome
        analysis.learning_outcome = self._extract_learning_outcome(interaction, agent)
        
        # Generate tags
        analysis.tags = self._generate_interaction_tags(interaction, agent)
        
        # Analyze responsibility impact
        analysis.responsibility_impact = self._analyze_responsibility_impact(interaction, agent)
        
        # Identify ethical implications
        analysis.ethical_implications = self._identify_ethical_implications(interaction, agent)
        
        return analysis
    
    def _calculate_experience_significance(self, interaction: InteractionRecord, agent: AgentIdentity) -> float:
        """Calculate how significant this interaction is as an experience."""
        significance = 0.3
        
        # Impact level multiplier
        impact_multipliers = {
            ImpactLevel.LOW: 0.2,
            ImpactLevel.MEDIUM: 0.5,
            ImpactLevel.HIGH: 0.8,
            ImpactLevel.CRITICAL: 1.0
        }
        significance *= impact_multipliers[interaction.impact_level]
        
        # Multi-agent interaction bonus
        if len(interaction.participants) > 1:
            significance += 0.2
        
        # Emotional significance
        if interaction.emotional_tone in [EmotionalTone.POSITIVE, EmotionalTone.NEGATIVE]:
            significance += 0.15
        
        # Type-based significance
        significant_types = [
            InteractionType.CONFLICT, InteractionType.ACHIEVEMENT,
            InteractionType.FAILURE, InteractionType.MORAL_CHOICE
        ]
        if interaction.interaction_type in significant_types:
            significance += 0.2
        
        # Context significance
        if 'difficulty' in interaction.context and interaction.context['difficulty'] == 'high':
            significance += 0.1
        
        return min(significance, 1.0)
    
    def _should_trigger_personality_update(self, interaction: InteractionRecord, agent: AgentIdentity) -> bool:
        """Determine if this interaction should trigger personality updates."""
        # High-impact interactions
        if interaction.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            return True
        
        # Significant interaction types
        personality_types = [
            InteractionType.CONFLICT, InteractionType.MORAL_CHOICE,
            InteractionType.ACHIEVEMENT, InteractionType.FAILURE,
            InteractionType.RELATIONSHIP
        ]
        
        if interaction.interaction_type in personality_types:
            return True
        
        # Repeated behavior patterns
        recent_interactions = self._get_recent_similar_interactions(interaction, agent)
        return len(recent_interactions) >= self.narrative_rules['personality_development']['interaction_threshold']
    
    def _analyze_arc_progression(self, interaction: InteractionRecord, agent: AgentIdentity) -> Dict[str, Any]:
        """Analyze if this interaction should trigger narrative arc progression."""
        current_arc = agent.narrative.current_arc
        experience_count = len(agent.background.experiences)
        stage = agent.get_current_development_stage()
        
        # Check experience thresholds for arc transitions
        stage_thresholds = self.narrative_rules['arc_progression']['experience_thresholds']
        
        if not current_arc and experience_count >= stage_thresholds.get(DevelopmentStage.NASCENT, 5):
            return {
                'should_transition': True,
                'new_arc': 'discovery',
                'context': 'Beginning journey of self-discovery and learning'
            }
        
        if current_arc == 'discovery' and experience_count >= stage_thresholds.get(DevelopmentStage.DEVELOPING, 15):
            return {
                'should_transition': True,
                'new_arc': 'growth',
                'context': 'Transitioning from discovery phase to active growth and development'
            }
        
        # Check for trigger events
        trigger_conditions = {
            InteractionType.CONFLICT: ('challenge', 'Entering challenge phase due to significant conflict'),
            InteractionType.ACHIEVEMENT: ('mastery', 'Achieving mastery through significant accomplishment'),
            InteractionType.FAILURE: ('struggle', 'Facing struggle phase after significant failure'),
            InteractionType.MORAL_CHOICE: ('wisdom', 'Developing wisdom through ethical challenges')
        }
        
        if interaction.interaction_type in trigger_conditions:
            arc, context = trigger_conditions[interaction.interaction_type]
            return {
                'should_transition': True,
                'new_arc': arc,
                'context': context
            }
        
        return {'should_transition': False}
    
    def _analyze_character_development(self, interaction: InteractionRecord, agent: AgentIdentity) -> Dict[str, Any]:
        """Analyze if this interaction represents character development."""
        if interaction.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            return {
                'has_development': True,
                'development': {
                    'type': 'significant_growth',
                    'description': f'Major development through {interaction.interaction_type.value}',
                    'catalyst': interaction.content,
                    'before_state': agent.get_current_development_stage().value,
                    'after_state': self._predict_development_progression(agent)
                }
            }
        
        # Check for learning-based development
        if interaction.interaction_type in [InteractionType.LEARNING, InteractionType.PROBLEM_SOLVING]:
            return {
                'has_development': True,
                'development': {
                    'type': 'skill_development',
                    'description': f'Skill enhancement through {interaction.content}',
                    'catalyst': interaction.interaction_type.value,
                    'before_state': 'learning',
                    'after_state': 'improved_capability'
                }
            }
        
        return {'has_development': False}
    
    def _extract_learning_outcome(self, interaction: InteractionRecord, agent: AgentIdentity) -> str:
        """Extract potential learning outcomes from the interaction."""
        learning_patterns = {
            InteractionType.CONFLICT: 'Enhanced conflict resolution and negotiation skills',
            InteractionType.COLLABORATION: 'Improved teamwork and communication abilities',
            InteractionType.FAILURE: 'Developed resilience and adaptive problem-solving strategies',
            InteractionType.ACHIEVEMENT: 'Reinforced successful behavioral patterns and confidence',
            InteractionType.RELATIONSHIP: 'Deepened understanding of interpersonal dynamics',
            InteractionType.MORAL_CHOICE: 'Strengthened ethical reasoning and moral framework',
            InteractionType.PROBLEM_SOLVING: 'Advanced analytical and creative thinking skills',
            InteractionType.LEARNING: 'Expanded knowledge base and learning strategies'
        }
        
        base_outcome = learning_patterns.get(interaction.interaction_type, 'Gained general experience and insights')
        
        # Enhance based on context
        if 'domain' in interaction.context:
            domain = interaction.context['domain']
            base_outcome += f' in {domain}'
        
        if interaction.impact_level == ImpactLevel.CRITICAL:
            base_outcome = f'Profound {base_outcome.lower()}'
        
        return base_outcome
    
    def _generate_interaction_tags(self, interaction: InteractionRecord, agent: AgentIdentity) -> List[str]:
        """Generate tags for the interaction."""
        tags = [interaction.interaction_type.value]
        
        # Multi-agent tag
        if len(interaction.participants) > 0:
            tags.append('multi_agent')
        
        # Significance tag
        if interaction.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            tags.append('significant')
        
        # Emotional tag
        if interaction.emotional_tone != EmotionalTone.NEUTRAL:
            tags.append(f'emotional_{interaction.emotional_tone.value}')
        
        # Context-based tags
        if 'domain' in interaction.context:
            tags.append(f"domain_{interaction.context['domain']}")
        
        if 'difficulty' in interaction.context:
            tags.append(f"difficulty_{interaction.context['difficulty']}")
        
        # Stage-based tag
        tags.append(f"stage_{agent.get_current_development_stage().value}")
        
        return tags
    
    def _analyze_responsibility_impact(self, interaction: InteractionRecord, agent: AgentIdentity) -> float:
        """Analyze the responsibility implications of the interaction."""
        impact = 0.0
        
        # Action-based responsibility
        action_indicators = ['decided', 'chose', 'acted', 'initiated', 'led', 'caused']
        content_lower = interaction.content.lower()
        
        for indicator in action_indicators:
            if indicator in content_lower:
                impact += 0.2
        
        # Context-based responsibility
        if 'responsibility' in interaction.context:
            impact += interaction.context['responsibility']
        
        # Impact level influence
        impact_multipliers = {
            ImpactLevel.LOW: 0.1,
            ImpactLevel.MEDIUM: 0.3,
            ImpactLevel.HIGH: 0.6,
            ImpactLevel.CRITICAL: 1.0
        }
        impact *= impact_multipliers[interaction.impact_level]
        
        # Success/failure adjustment
        if 'success' in interaction.context:
            if interaction.context['success']:
                impact += 0.1
            else:
                impact += 0.2  # More responsibility for failures to learn from
        
        return min(impact, 1.0)
    
    def _identify_ethical_implications(self, interaction: InteractionRecord, agent: AgentIdentity) -> List[str]:
        """Identify ethical implications of the interaction."""
        implications = []
        
        # Moral choice interactions
        if interaction.interaction_type == InteractionType.MORAL_CHOICE:
            implications.append('direct_ethical_decision')
        
        # Impact on others
        if len(interaction.participants) > 0:
            implications.append('impact_on_others')
        
        # Context-based implications
        ethical_keywords = ['fair', 'unfair', 'right', 'wrong', 'ethical', 'moral', 'harm', 'help']
        content_lower = interaction.content.lower()
        
        for keyword in ethical_keywords:
            if keyword in content_lower:
                implications.append(f'ethical_concept_{keyword}')
        
        # High-impact decisions have ethical weight
        if interaction.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            implications.append('high_stakes_decision')
        
        return implications
    
    async def _process_narrative_updates(self, agent: AgentIdentity, interaction: InteractionRecord, analysis: NarrativeAnalysis) -> None:
        """Process narrative updates based on analysis results."""
        
        # Update personality if significant
        if analysis.personality_impact:
            personality_updates = self._derive_personality_updates(interaction, agent)
            for update in personality_updates:
                agent.update_personality(update['trait'], update['value'], update['context'])
        
        # Add experience if significant enough - store as memory in enhanced structure
        if analysis.experience_significance > 0.5:
            memory_data = {
                'agent_id': agent.agent_id,
                'memory_type': 'episodic',
                'content': {
                    'event_description': f"{interaction.interaction_type.value}: {interaction.content}",
                    'participants': interaction.participants,
                    'sequence_order': 1
                },
                'metadata': {
                    'importance_score': analysis.experience_significance,
                    'consolidation_strength': min(analysis.experience_significance + 0.2, 1.0),
                    'emotional_valence': 0.5 if interaction.emotional_tone == EmotionalTone.POSITIVE else (-0.5 if interaction.emotional_tone == EmotionalTone.NEGATIVE else 0.0),
                    'tags': analysis.tags,
                    'themes': [interaction.interaction_type.value],
                    'source_interactions': [f"interaction_{interaction.agent_id}_{datetime.utcnow().timestamp()}"]
                }
            }
            
            # Store memory in Firebase if available
            if self.firebase_client:
                try:
                    await self.firebase_client.store_memory(memory_data)
                except Exception as e:
                    logger.error(f"Failed to store memory: {e}")
            
            # Also add to agent's local experience
            experience_data = {
                'description': f"{interaction.interaction_type.value}: {interaction.content}",
                'impact_level': interaction.impact_level.value,
                'emotional_resonance': interaction.emotional_tone.value,
                'learning_outcome': analysis.learning_outcome,
                'participants': interaction.participants,
                'tags': analysis.tags
            }
            agent.add_experience(experience_data)
        
        # Record action if has responsibility impact - store as responsibility record
        if analysis.responsibility_impact > self.evolution_thresholds['responsibility_development']:
            responsibility_data = {
                'agent_id': agent.agent_id,
                'action_type': interaction.interaction_type.value,
                'description': interaction.content,
                'context': str(interaction.context),
                'intended_outcome': interaction.context.get('intended_outcome', 'Positive interaction outcome'),
                'actual_outcome': interaction.context.get('actual_outcome', 'Interaction completed'),
                'success_level': analysis.responsibility_impact,
                'responsibility_analysis': {
                    'causal_responsibility': analysis.responsibility_impact,
                    'moral_responsibility': len(analysis.ethical_implications) * 0.2,
                    'role_responsibility': 0.8,  # Default for autonomous agent
                    'collective_responsibility': 0.3 if len(interaction.participants) > 0 else 0.0,
                    'overall_responsibility_score': analysis.responsibility_impact,
                    'ethical_weight': len(analysis.ethical_implications) * 0.2,
                    'agent_autonomy_level': 0.9,
                    'knowledge_completeness': 0.7,
                    'external_pressures': [],
                    'alternative_actions_considered': []
                },
                'consequences': {
                    'immediate_effects': [f"Completed {interaction.interaction_type.value}"],
                    'short_term_effects': [],
                    'long_term_effects': [],
                    'user_impact': 'Interaction processed',
                    'other_agent_impact': interaction.participants,
                    'system_impact': 'Normal operation',
                    'lessons_learned': [analysis.learning_outcome] if analysis.learning_outcome else [],
                    'behavior_adjustments': [],
                    'pattern_reinforcement': True
                },
                'decision_process': {
                    'reasoning_steps': ['Analyzed interaction context', 'Applied GNF analysis'],
                    'values_considered': ['helpfulness', 'accuracy'],
                    'ethical_frameworks_applied': analysis.ethical_implications,
                    'uncertainty_factors': [],
                    'time_pressure': 'normal',
                    'knowledge_sources': ['interaction_context'],
                    'consultation_performed': False,
                    'precedent_cases': []
                },
                'performed_at': datetime.utcnow(),
                'source_interaction_id': f"conversation_{agent.agent_id}_{datetime.utcnow().timestamp()}",
                'assessment_method': 'auto'
            }
            
            # Store responsibility record in Firebase if available
            if self.firebase_client:
                try:
                    await self.firebase_client.store_responsibility_record(responsibility_data)
                except Exception as e:
                    logger.error(f"Failed to store responsibility record: {e}")
            
            # Also record action locally
            action_data = {
                'action_type': interaction.interaction_type.value,
                'description': interaction.content,
                'context': interaction.context,
                'responsibility_level': analysis.responsibility_impact,
                'ethical_weight': len(analysis.ethical_implications) * 0.2,
                'success': interaction.context.get('success', True),
                'consequences': [],
                'lessons_learned': [analysis.learning_outcome] if analysis.learning_outcome else []
            }
            agent.record_action(action_data)
        
        # Update narrative arc if needed
        if analysis.arc_transition:
            agent.update_narrative_arc(analysis.new_arc, analysis.arc_context)
        
        # Add character development if present
        if analysis.character_development:
            agent.add_character_development(analysis.character_development)
    
    def _derive_personality_updates(self, interaction: InteractionRecord, agent: AgentIdentity) -> List[Dict[str, str]]:
        """Derive personality trait updates from the interaction."""
        updates = []
        
        # Type-based trait derivation
        trait_mappings = {
            InteractionType.COLLABORATION: [
                {'trait': 'cooperation', 'value': 'collaborative', 'context': f'Reinforced through {interaction.content}'}
            ],
            InteractionType.CONFLICT: [
                {'trait': 'assertiveness', 'value': 'confident', 'context': f'Developed through conflict: {interaction.content}'}
            ],
            InteractionType.ACHIEVEMENT: [
                {'trait': 'determination', 'value': 'persistent', 'context': f'Strengthened by achievement: {interaction.content}'}
            ],
            InteractionType.FAILURE: [
                {'trait': 'resilience', 'value': 'resilient', 'context': f'Built through overcoming failure: {interaction.content}'}
            ],
            InteractionType.MORAL_CHOICE: [
                {'trait': 'integrity', 'value': 'principled', 'context': f'Developed through ethical decision: {interaction.content}'}
            ]
        }
        
        if interaction.interaction_type in trait_mappings:
            updates.extend(trait_mappings[interaction.interaction_type])
        
        # Impact-based trait enhancement
        if interaction.impact_level == ImpactLevel.CRITICAL:
            updates.append({
                'trait': 'adaptability',
                'value': 'highly_adaptable',
                'context': f'Enhanced through critical experience: {interaction.content}'
            })
        
        return updates
    
    async def _process_cross_agent_interaction(self, interaction: InteractionRecord, analysis: NarrativeAnalysis) -> None:
        """Process interactions involving multiple agents."""
        # Store cross-agent interaction in enhanced structure
        if self.firebase_client:
            try:
                cross_agent_data = {
                    'primary_agent_id': interaction.agent_id,
                    'participating_agents': [interaction.agent_id] + interaction.participants,
                    'interaction_type': 'collaboration',  # Default type
                    'description': f'Multi-agent interaction: {interaction.content}',
                    'context': str(interaction.context),
                    'narrative_impact': {
                        'shared_story_elements': [{
                            'element_type': 'collaborative_achievement',
                            'description': interaction.content,
                            'significance': analysis.experience_significance,
                            'agents_affected': [interaction.agent_id] + interaction.participants
                        }],
                        'relationship_changes': [],
                        'emergent_behaviors': []
                    },
                    'agent_impacts': [{
                        'agent_id': participant_id,
                        'impact_areas': ['relationships', 'narrative_arc'],
                        'specific_changes': [f'Interaction with {interaction.agent_id}'],
                        'experience_gained': analysis.experience_significance * 10,
                        'memory_significance': analysis.experience_significance
                    } for participant_id in ([interaction.agent_id] + interaction.participants)],
                    'outcomes': {
                        'immediate_results': [f'Completed {interaction.interaction_type.value}'],
                        'collaborative_products': [],
                        'conflict_resolutions': [],
                        'unresolved_tensions': [],
                        'future_interaction_likelihood': 0.7,
                        'network_effects': 'Strengthened agent network connections',
                        'precedent_set': False,
                        'influence_on_others': []
                    },
                    'duration_minutes': 5,  # Default duration
                    'interaction_quality': 'positive',
                    'facilitated_by_human': False,
                    'source_conversations': [f"conversation_{interaction.agent_id}_{datetime.utcnow().timestamp()}"]
                }
                
                await self.firebase_client.store_cross_agent_interaction(cross_agent_data)
            except Exception as e:
                logger.error(f"Failed to store cross-agent interaction: {e}")
        
        # Create global timeline event
        cross_agent_event = GlobalEvent(
            event_type='cross_agent_interaction',
            description=f'Multi-agent interaction: {interaction.content}',
            participants=[interaction.agent_id] + interaction.participants,
            data={
                'primary_agent': interaction.agent_id,
                'interaction_type': interaction.interaction_type.value,
                'content': interaction.content,
                'significance': analysis.experience_significance
            },
            impact_scope='multi_agent'
        )
        
        await self._store_global_event(cross_agent_event)
        
        # Update participating agents with memories
        for participant_id in interaction.participants:
            if participant_id != interaction.agent_id:
                participant = await self.get_agent(participant_id)
                if participant:
                    # Store memory for participant
                    if self.firebase_client:
                        try:
                            participant_memory_data = {
                                'agent_id': participant_id,
                                'memory_type': 'episodic',
                                'content': {
                                    'event_description': f'Interaction with {interaction.agent_id}: {interaction.content}',
                                    'participants': [interaction.agent_id],
                                    'sequence_order': 1
                                },
                                'metadata': {
                                    'importance_score': analysis.experience_significance * 0.8,
                                    'consolidation_strength': analysis.experience_significance * 0.7,
                                    'emotional_valence': 0.3,  # Neutral to positive for cross-agent
                                    'tags': ['cross_agent', interaction.interaction_type.value],
                                    'themes': ['collaboration'],
                                    'source_interactions': [f"cross_agent_interaction_{datetime.utcnow().timestamp()}"]
                                }
                            }
                            await self.firebase_client.store_memory(participant_memory_data)
                        except Exception as e:
                            logger.error(f"Failed to store participant memory: {e}")
                    
                    # Add experience locally
                    participant_experience = {
                        'description': f'Interaction with {interaction.agent_id}: {interaction.content}',
                        'impact_level': 'medium',
                        'emotional_resonance': interaction.emotional_tone.value,
                        'participants': [interaction.agent_id],
                        'tags': ['cross_agent', interaction.interaction_type.value]
                    }
                    participant.add_experience(participant_experience)
                    await self._persist_agent(participant)
    
    async def _store_global_event(self, event: GlobalEvent) -> None:
        """Store a global narrative event."""
        self.global_narrative['timeline'].append(event.dict())
        
        if self.firebase_client:
            try:
                # Create enhanced global narrative event
                enhanced_event_data = {
                    'event_type': event.event_type,
                    'title': f'{event.event_type.replace("_", " ").title()}: {event.description[:50]}...' if len(event.description) > 50 else f'{event.event_type.replace("_", " ").title()}: {event.description}',
                    'description': event.description,
                    'significance_level': 'moderate',  # Default
                    'participants': {
                        'agent_ids': event.participants,
                        'user_ids': [],
                        'system_components': ['gnf_narrative_tracker']
                    },
                    'narrative_context': {
                        'story_arc': 'agent_development',
                        'themes': [event.event_type],
                        'character_arcs_affected': event.participants,
                        'plot_developments': [event.description],
                        'emergent_patterns': [],
                        'collective_behaviors': [],
                        'system_evolution': 'Normal narrative progression'
                    },
                    'impact_analysis': {
                        'immediate_impacts': [event.description],
                        'ripple_effects': [],
                        'long_term_implications': [],
                        'system_metrics_changed': ['total_events'],
                        'narrative_coherence_impact': 0.1,
                        'network_complexity_change': 0.05 if len(event.participants) > 1 else 0.0
                    },
                    'evidence_data': {
                        'source_interactions': [],
                        'data_points': [event.data],
                        'observer_notes': f'Generated by NarrativeTracker at {datetime.utcnow()}',
                        'correlation_analysis': {}
                    },
                    'occurred_at': datetime.utcnow(),
                    'detected_at': datetime.utcnow(),
                    'duration': 0,
                    'detection_method': 'pattern_recognition',
                    'confidence_level': 0.9,
                    'validation_status': 'confirmed'
                }
                
                await self.firebase_client.store_global_narrative_event(enhanced_event_data)
            except Exception as e:
                logger.error(f"Failed to store global event: {e}")
        
        # Maintain reasonable timeline size
        if len(self.global_narrative['timeline']) > 10000:
            self.global_narrative['timeline'] = self.global_narrative['timeline'][-5000:]
    
    async def _persist_agent(self, agent: AgentIdentity) -> None:
        """Persist agent to Firebase."""
        if self.firebase_client:
            try:
                # Create enhanced agent update with GNF fields
                firebase_model = agent.to_firebase_model()
                agent_updates = {
                    AgentFields.UPDATED_AT: datetime.utcnow(),
                    AgentFields.LAST_NARRATIVE_UPDATE: datetime.utcnow(),
                    
                    # Update GNF identity structure
                    'gnf_identity': firebase_model.dict().get('core', {}),
                    
                    # Update GNF metadata
                    'gnf_metadata.last_narrative_update': datetime.utcnow(),
                    'gnf_metadata.total_interactions_tracked': getattr(agent, 'interaction_count', 0) + 1,
                    'gnf_metadata.narrative_coherence_score': min(getattr(agent, 'coherence_score', 0.5) + 0.01, 1.0)
                }
                
                await self.firebase_client.update_agent(agent.agent_id, agent_updates)
            except Exception as e:
                logger.error(f"Failed to persist agent {agent.agent_id}: {e}")
    
    def _get_recent_similar_interactions(self, interaction: InteractionRecord, agent: AgentIdentity) -> List[Any]:
        """Get recent similar interactions for pattern analysis."""
        # This would query recent interactions from Firebase in a real implementation
        # For now, return empty list as placeholder
        return []
    
    def _predict_development_progression(self, agent: AgentIdentity) -> str:
        """Predict next development stage for the agent."""
        current_stage = agent.get_current_development_stage()
        stage_progression = {
            DevelopmentStage.NASCENT: 'developing',
            DevelopmentStage.DEVELOPING: 'established', 
            DevelopmentStage.ESTABLISHED: 'mature',
            DevelopmentStage.MATURE: 'evolved'
        }
        return stage_progression.get(current_stage, current_stage.value)
    
    async def get_global_narrative_state(self) -> Dict[str, Any]:
        """Get current global narrative state."""
        stats = {}
        if self.firebase_client:
            stats = await self.firebase_client.get_agent_statistics()
        
        return {
            'total_agents': len(self.agents),
            'total_events': len(self.global_narrative['timeline']),
            'cross_agent_interactions': len(self.global_narrative['cross_agent_events']),
            'active_narrative_threads': len(self.global_narrative['threads']),
            'world_state': self.global_narrative['world_state'],
            'database_stats': stats
        }
    
    async def get_agent_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries of all agents."""
        summaries = []
        
        # Get from memory
        for agent in self.agents.values():
            summaries.append(agent.get_identity_summary())
        
        # Get additional from Firebase if available
        if self.firebase_client:
            try:
                firebase_agents = await self.firebase_client.list_agents()
                for firebase_agent in firebase_agents:
                    # Skip if already in memory
                    if firebase_agent['agent_id'] not in self.agents:
                        summaries.append({
                            'agent_id': firebase_agent['agent_id'],
                            'name': firebase_agent['name'],
                            'development_stage': firebase_agent['development_stage'],
                            'created_at': firebase_agent['created_at'],
                            'updated_at': firebase_agent['updated_at'],
                            'source': 'firebase'
                        })
            except Exception as e:
                logger.error(f"Failed to get agent summaries from Firebase: {e}")
        
        return summaries
    
    def on(self, event: str, handler: Callable) -> None:
        """Register event handler."""
        self.event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit event to registered handlers."""
        for handler in self.event_handlers[event]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event}: {e}")
    
    async def get_cross_agent_interactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent cross-agent interactions."""
        if self.firebase_client:
            try:
                # Use the enhanced cross-agent interactions method
                return await self.firebase_client.get_cross_agent_interactions(agent_id=None, limit=limit)
            except Exception as e:
                logger.error(f"Failed to get cross-agent interactions: {e}")
        
        # Fallback to in-memory data
        cross_agent_events = [
            event for event in self.global_narrative['timeline']
            if event.get('event_type') == 'cross_agent_interaction'
        ]
        return cross_agent_events[-limit:]
    
    async def backup_agent(self, agent_id: str) -> Dict[str, Any]:
        """Create a complete backup of an agent."""
        if self.firebase_client:
            return await self.firebase_client.backup_agent(agent_id)
        
        agent = await self.get_agent(agent_id)
        if agent:
            return {
                'agent': agent.to_firebase_model().dict(),
                'backup_timestamp': datetime.utcnow().isoformat()
            }
        
        return {}
    
    def close(self) -> None:
        """Clean up resources."""
        if self.firebase_client:
            self.firebase_client.close()