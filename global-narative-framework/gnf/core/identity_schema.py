"""
Agent Identity Schema - Core identity management for AI agents.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ..storage.models import (
    AgentIdentityFirebase, PersonalityCore, BackgroundInfo, Capabilities,
    NarrativeInfo, EvolutionInfo, MemoryAnchors, ResponsibilityTracker,
    PersonalityTrait, Experience, CharacterDevelopment, ActionRecord,
    DevelopmentStage, ImpactLevel, EmotionalTone, InteractionType
)


class AgentIdentity:
    """
    Core agent identity class with comprehensive personality, narrative, and evolution tracking.
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        config = config or {}
        
        # Initialize core components
        self.core = PersonalityCore(
            traits=[PersonalityTrait(name=trait, value=trait, strength=0.5) 
                   for trait in config.get('personality', {}).get('traits', [])],
            values=config.get('personality', {}).get('values', []),
            goals=config.get('personality', {}).get('goals', []),
            fears=config.get('personality', {}).get('fears', []),
            motivations=config.get('personality', {}).get('motivations', [])
        )
        
        self.background = BackgroundInfo(
            origin=config.get('background', {}).get('origin', f"Created agent {agent_id}"),
            achievements=config.get('background', {}).get('achievements', []),
            failures=config.get('background', {}).get('failures', [])
        )
        
        self.capabilities = Capabilities(
            knowledge_domains=config.get('capabilities', {}).get('knowledge_domains', []),
            limitations=config.get('capabilities', {}).get('limitations', []),
            learning_preferences=config.get('capabilities', {}).get('learning_preferences', [])
        )
        
        self.narrative = NarrativeInfo(
            narrative_voice=config.get('narrative_voice', 'first_person')
        )
        
        self.evolution = EvolutionInfo()
        self.memory_anchors = MemoryAnchors()
        self.responsibility = ResponsibilityTracker()
    
    def update_personality(self, trait_name: str, value: str, context: str = "") -> None:
        """Update or add a personality trait."""
        current_time = datetime.utcnow()
        
        # Find existing trait
        existing_trait = None
        for trait in self.core.traits:
            if trait.name == trait_name:
                existing_trait = trait
                break
        
        if existing_trait:
            existing_trait.value = value
            existing_trait.strength = min(existing_trait.strength + 0.1, 1.0)
            existing_trait.context = context
            existing_trait.last_reinforced = current_time
        else:
            new_trait = PersonalityTrait(
                name=trait_name,
                value=value,
                strength=0.6,
                context=context,
                developed_at=current_time
            )
            self.core.traits.append(new_trait)
        
        self.updated_at = current_time
        self._log_evolution("personality_update", {
            "trait": trait_name,
            "value": value,
            "context": context
        })
    
    def add_experience(self, experience_data: Dict[str, Any]) -> Experience:
        """Add a new experience to the agent's background."""
        experience = Experience(
            id=f"exp_{uuid.uuid4().hex[:8]}",
            description=experience_data.get('description', ''),
            impact_level=ImpactLevel(experience_data.get('impact_level', 'medium')),
            emotional_resonance=EmotionalTone(experience_data.get('emotional_resonance', 'neutral')),
            learning_outcome=experience_data.get('learning_outcome', ''),
            participants=experience_data.get('participants', []),
            tags=experience_data.get('tags', [])
        )
        
        self.background.experiences.append(experience)
        
        # Update growth metrics
        self.evolution.growth_metrics.experience_points += self._calculate_experience_points(experience)
        self.evolution.growth_metrics.interactions_count += 1
        
        # Check for defining moments
        if experience.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            self.memory_anchors.defining_moments.append({
                'type': 'defining_moment',
                'content': {
                    'experience_id': experience.id,
                    'description': experience.description,
                    'impact': experience.impact_level.value
                },
                'significance': f"High-impact experience: {experience.description}",
                'timestamp': experience.timestamp
            })
        
        self.updated_at = datetime.utcnow()
        self._log_evolution("experience_added", experience.dict())
        
        return experience
    
    def record_action(self, action_data: Dict[str, Any]) -> ActionRecord:
        """Record an action taken by the agent for responsibility tracking."""
        action = ActionRecord(
            id=f"action_{uuid.uuid4().hex[:8]}",
            action_type=action_data.get('action_type', 'general'),
            description=action_data.get('description', ''),
            context=action_data.get('context', {}),
            intended_outcome=action_data.get('intended_outcome', ''),
            actual_outcome=action_data.get('actual_outcome', ''),
            success=action_data.get('success', True),
            responsibility_level=action_data.get('responsibility_level', 0.5),
            ethical_weight=action_data.get('ethical_weight', 0.0),
            consequences=action_data.get('consequences', []),
            lessons_learned=action_data.get('lessons_learned', [])
        )
        
        self.responsibility.actions.append(action)
        
        # Update responsibility metrics
        self._update_responsibility_metrics(action)
        
        # Create experience from significant actions
        if action.responsibility_level > 0.7 or action.ethical_weight > 0.5:
            self.add_experience({
                'description': f"Action taken: {action.description}",
                'impact_level': 'high' if action.responsibility_level > 0.8 else 'medium',
                'emotional_resonance': 'positive' if action.success else 'negative',
                'learning_outcome': '; '.join(action.lessons_learned),
                'tags': ['action', action.action_type, 'responsibility']
            })
        
        self.updated_at = datetime.utcnow()
        return action
    
    def update_narrative_arc(self, new_arc: str, context: str = "") -> None:
        """Update the agent's current narrative arc."""
        current_time = datetime.utcnow()
        
        if self.narrative.current_arc:
            # Record arc transition
            self.narrative.story_elements.append({
                'type': 'arc_transition',
                'content': f"Transitioned from '{self.narrative.current_arc}' to '{new_arc}'",
                'timestamp': current_time,
                'context': {'from': self.narrative.current_arc, 'to': new_arc, 'reason': context}
            })
        
        self.narrative.current_arc = new_arc
        self.updated_at = current_time
        
        self._log_evolution("narrative_arc_update", {
            "new_arc": new_arc,
            "context": context
        })
    
    def add_character_development(self, development_data: Dict[str, Any]) -> CharacterDevelopment:
        """Add a character development event."""
        development = CharacterDevelopment(
            id=f"dev_{uuid.uuid4().hex[:8]}",
            type=development_data.get('type', 'growth_event'),
            description=development_data.get('description', ''),
            catalyst=development_data.get('catalyst', ''),
            before_state=development_data.get('before_state', ''),
            after_state=development_data.get('after_state', '')
        )
        
        self.narrative.character_development.append(development)
        self.evolution.growth_metrics.learning_events += 1
        
        self.updated_at = datetime.utcnow()
        self._log_evolution("character_development", development.dict())
        
        return development
    
    def get_current_development_stage(self) -> DevelopmentStage:
        """Calculate current development stage based on experience points."""
        exp = self.evolution.growth_metrics.experience_points
        
        if exp < 100:
            return DevelopmentStage.NASCENT
        elif exp < 500:
            return DevelopmentStage.DEVELOPING
        elif exp < 1000:
            return DevelopmentStage.ESTABLISHED
        elif exp < 2000:
            return DevelopmentStage.MATURE
        else:
            return DevelopmentStage.EVOLVED
    
    def get_identity_summary(self) -> Dict[str, Any]:
        """Get a concise summary of the agent's identity."""
        return {
            'agent_id': self.agent_id,
            'name': getattr(self, 'name', f"Agent-{self.agent_id}"),
            'development_stage': self.get_current_development_stage().value,
            'current_arc': self.narrative.current_arc,
            'experience_level': self.evolution.growth_metrics.experience_points,
            'responsibility_score': self.responsibility.accountability_score,
            'key_traits': [
                {'name': trait.name, 'value': trait.value, 'strength': trait.strength}
                for trait in sorted(self.core.traits, key=lambda t: t.strength, reverse=True)[:5]
            ],
            'defining_moments': len(self.memory_anchors.defining_moments),
            'total_experiences': len(self.background.experiences),
            'total_actions': len(self.responsibility.actions),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_firebase_model(self) -> AgentIdentityFirebase:
        """Convert to Firebase-compatible model."""
        return AgentIdentityFirebase(
            agent_id=self.agent_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            core=self.core,
            background=self.background,
            capabilities=self.capabilities,
            narrative=self.narrative,
            evolution=self.evolution,
            memory_anchors=self.memory_anchors,
            responsibility=self.responsibility
        )
    
    @classmethod
    def from_firebase_model(cls, model: AgentIdentityFirebase) -> 'AgentIdentity':
        """Create AgentIdentity from Firebase model."""
        identity = cls(model.agent_id)
        identity.created_at = model.created_at
        identity.updated_at = model.updated_at
        identity.core = model.core
        identity.background = model.background
        identity.capabilities = model.capabilities
        identity.narrative = model.narrative
        identity.evolution = model.evolution
        identity.memory_anchors = model.memory_anchors
        identity.responsibility = model.responsibility
        return identity
    
    def _calculate_experience_points(self, experience: Experience) -> int:
        """Calculate experience points for an experience."""
        base_points = 10
        
        impact_multipliers = {
            ImpactLevel.LOW: 0.5,
            ImpactLevel.MEDIUM: 1.0,
            ImpactLevel.HIGH: 2.0,
            ImpactLevel.CRITICAL: 3.0
        }
        
        multiplier = impact_multipliers.get(experience.impact_level, 1.0)
        
        # Bonus for multi-agent interactions
        if len(experience.participants) > 0:
            multiplier += 0.5
        
        # Bonus for learning outcomes
        if experience.learning_outcome:
            multiplier += 0.3
        
        return int(base_points * multiplier)
    
    def _update_responsibility_metrics(self, action: ActionRecord) -> None:
        """Update responsibility tracking metrics."""
        # Update accountability score (weighted average)
        current_score = self.responsibility.accountability_score
        action_weight = action.responsibility_level
        total_actions = len(self.responsibility.actions)
        
        if total_actions > 1:
            # Weighted average with recent actions having more influence
            recent_weight = 0.7
            historical_weight = 0.3
            new_score = (current_score * historical_weight + 
                        action_weight * recent_weight)
        else:
            new_score = action_weight
        
        self.responsibility.accountability_score = max(0.0, min(1.0, new_score))
        
        # Update ethical development
        if action.ethical_weight > 0:
            ethical_impact = action.ethical_weight * (1.0 if action.success else 0.5)
            current_ethical = self.responsibility.ethical_development_level
            self.responsibility.ethical_development_level = min(1.0, 
                current_ethical + ethical_impact * 0.1)
        
        # Track decision patterns
        decision_pattern = {
            'action_type': action.action_type,
            'responsibility_level': action.responsibility_level,
            'ethical_weight': action.ethical_weight,
            'success': action.success,
            'timestamp': action.timestamp.isoformat()
        }
        
        self.responsibility.decision_patterns.append(decision_pattern)
        
        # Keep only recent patterns (last 100)
        if len(self.responsibility.decision_patterns) > 100:
            self.responsibility.decision_patterns = self.responsibility.decision_patterns[-50:]
    
    def _log_evolution(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an evolution event."""
        evolution_event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_state': {
                'stage': self.get_current_development_stage().value,
                'experience_points': self.evolution.growth_metrics.experience_points,
                'responsibility_score': self.responsibility.accountability_score
            }
        }
        
        self.evolution.behavioral_changes.append(evolution_event)
        
        # Maintain reasonable history size
        if len(self.evolution.behavioral_changes) > 1000:
            self.evolution.behavioral_changes = self.evolution.behavioral_changes[-500:]
    
    def calculate_narrative_coherence(self) -> float:
        """Calculate how coherent the agent's narrative is."""
        coherence_score = 0.5  # Base coherence
        
        # Consistency in personality traits
        if len(self.core.traits) > 0:
            avg_trait_strength = sum(t.strength for t in self.core.traits) / len(self.core.traits)
            coherence_score += avg_trait_strength * 0.2
        
        # Narrative arc progression
        if self.narrative.current_arc:
            coherence_score += 0.15
        
        # Character development events
        if len(self.narrative.character_development) > 0:
            coherence_score += min(0.15, len(self.narrative.character_development) * 0.03)
        
        # Experience to learning ratio
        total_experiences = len(self.background.experiences)
        learning_experiences = sum(1 for exp in self.background.experiences if exp.learning_outcome)
        
        if total_experiences > 0:
            learning_ratio = learning_experiences / total_experiences
            coherence_score += learning_ratio * 0.1
        
        # Responsibility consistency
        if len(self.responsibility.actions) > 0:
            responsibility_variance = self._calculate_responsibility_variance()
            coherence_score += (1.0 - responsibility_variance) * 0.1
        
        return max(0.0, min(1.0, coherence_score))
    
    def _calculate_responsibility_variance(self) -> float:
        """Calculate variance in responsibility levels (lower is more consistent)."""
        if len(self.responsibility.actions) < 2:
            return 0.0
        
        responsibility_levels = [action.responsibility_level for action in self.responsibility.actions]
        mean_responsibility = sum(responsibility_levels) / len(responsibility_levels)
        
        variance = sum((r - mean_responsibility) ** 2 for r in responsibility_levels) / len(responsibility_levels)
        return min(1.0, variance)  # Normalize to 0-1 range
    
    def get_personality_profile(self) -> Dict[str, Any]:
        """Get detailed personality profile."""
        return {
            'dominant_traits': [
                {'name': trait.name, 'value': trait.value, 'strength': trait.strength}
                for trait in sorted(self.core.traits, key=lambda t: t.strength, reverse=True)[:10]
            ],
            'core_values': self.core.values,
            'primary_goals': self.core.goals,
            'motivations': self.core.motivations,
            'fears': self.core.fears,
            'trait_development_timeline': [
                {
                    'trait': trait.name,
                    'developed_at': trait.developed_at.isoformat(),
                    'last_reinforced': trait.last_reinforced.isoformat() if trait.last_reinforced else None,
                    'context': trait.context
                }
                for trait in sorted(self.core.traits, key=lambda t: t.developed_at)
            ]
        }
    
    def export_narrative_only(self) -> Dict[str, Any]:
        """Export only narrative-related data."""
        return {
            'agent_id': self.agent_id,
            'narrative': self.narrative.dict(),
            'key_experiences': [exp.dict() for exp in self.background.experiences[-10:]],
            'defining_moments': [moment for moment in self.memory_anchors.defining_moments],
            'character_development': [dev.dict() for dev in self.narrative.character_development],
            'current_stage': self.get_current_development_stage().value,
            'narrative_coherence': self.calculate_narrative_coherence(),
            'exported_at': datetime.utcnow().isoformat()
        }