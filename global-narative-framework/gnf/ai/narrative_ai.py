"""
Narrative AI - AI-powered narrative analysis and enhancement system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .openai_client import OpenAIClient
from ..core.identity_schema import AgentIdentity
from ..storage.models import InteractionRecord, Experience

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NarrativeAI:
    """
    AI-powered narrative analysis system that enhances the Global Narrative Framework
    with intelligent insights and automated analysis.
    """
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        self.openai_client = openai_client or OpenAIClient()
        self.analysis_cache = {}
        self.enhancement_rules = self._setup_enhancement_rules()
        
    def _setup_enhancement_rules(self) -> Dict[str, Dict[str, Any]]:
        """Setup AI enhancement rules and configurations."""
        return {
            'narrative_significance': {
                'enabled': True,
                'threshold': 0.3,
                'cache_duration': 300,  # 5 minutes
                'enhancement_weight': 0.7
            },
            'personality_development': {
                'enabled': True,
                'confidence_threshold': 0.6,
                'trait_strength_multiplier': 1.2,
                'development_acceleration': 0.15
            },
            'ethical_analysis': {
                'enabled': True,
                'ethical_weight_threshold': 0.4,
                'responsibility_boost': 0.1,
                'moral_development_rate': 0.05
            },
            'relationship_dynamics': {
                'enabled': True,
                'relationship_impact_threshold': 0.5,
                'social_learning_boost': 0.2,
                'trust_development_multiplier': 1.1
            },
            'learning_enhancement': {
                'enabled': True,
                'learning_efficiency_boost': 0.15,
                'knowledge_integration_threshold': 0.6,
                'meta_learning_weight': 0.3
            },
            'coherence_monitoring': {
                'enabled': True,
                'coherence_threshold': 0.7,
                'inconsistency_penalty': 0.1,
                'coherence_reward': 0.05
            }
        }
    
    async def enhance_interaction_analysis(self, interaction: InteractionRecord,
                                         agent: AgentIdentity) -> Dict[str, Any]:
        """
        Enhance interaction analysis with AI-powered insights.
        """
        # Prepare context for AI analysis
        agent_context = self._prepare_agent_context(agent)
        interaction_dict = interaction.dict()
        
        # Run parallel analyses
        analysis_tasks = []
        
        if self.enhancement_rules['narrative_significance']['enabled']:
            analysis_tasks.append(
                self._analyze_narrative_significance_with_ai(interaction_dict, agent_context)
            )
        
        if self.enhancement_rules['personality_development']['enabled']:
            current_traits = [
                {'name': trait.name, 'value': trait.value, 'strength': trait.strength}
                for trait in agent.core.traits
            ]
            analysis_tasks.append(
                self._analyze_personality_development_with_ai(interaction_dict, agent_context, current_traits)
            )
        
        if self.enhancement_rules['relationship_dynamics']['enabled'] and interaction.participants:
            relationship_history = [
                {
                    'entity': rel.entity,
                    'relationship_type': rel.relationship_type,
                    'depth_level': rel.depth_level,
                    'trust_level': rel.trust_level
                }
                for rel in agent.background.relationships
            ]
            analysis_tasks.append(
                self._analyze_relationship_dynamics_with_ai(interaction_dict, agent_context, relationship_history)
            )
        
        # Execute analyses concurrently
        try:
            analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Combine results
            enhanced_analysis = {
                'ai_enhanced': True,
                'enhancement_timestamp': datetime.utcnow().isoformat(),
                'analyses': {}
            }
            
            for i, analysis in enumerate(analyses):
                if isinstance(analysis, Exception):
                    logger.warning(f"Analysis {i} failed: {analysis}")
                    continue
                
                if i == 0 and 'significance_score' in analysis:
                    enhanced_analysis['analyses']['narrative_significance'] = analysis
                elif i == 1 and 'personality_impact' in analysis:
                    enhanced_analysis['analyses']['personality_development'] = analysis
                elif len(analysis_tasks) > 2 and i == 2 and 'relationship_impact' in analysis:
                    enhanced_analysis['analyses']['relationship_dynamics'] = analysis
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Failed to enhance interaction analysis: {e}")
            return {'ai_enhanced': False, 'error': str(e)}
    
    async def enhance_action_analysis(self, action: Dict[str, Any], agent: AgentIdentity) -> Dict[str, Any]:
        """
        Enhance action analysis with AI-powered ethical and responsibility insights.
        """
        if not self.enhancement_rules['ethical_analysis']['enabled']:
            return {'ai_enhanced': False}
        
        try:
            agent_context = self._prepare_agent_context(agent)
            agent_context['responsibility_score'] = agent.responsibility.accountability_score
            agent_context['ethical_development'] = agent.responsibility.ethical_development_level
            
            ethical_analysis = await self.openai_client.analyze_ethical_implications(action, agent_context)
            
            enhanced_analysis = {
                'ai_enhanced': True,
                'ethical_analysis': ethical_analysis,
                'enhanced_metrics': self._calculate_enhanced_responsibility_metrics(action, ethical_analysis),
                'enhancement_timestamp': datetime.utcnow().isoformat()
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Failed to enhance action analysis: {e}")
            return {'ai_enhanced': False, 'error': str(e)}
    
    async def enhance_learning_analysis(self, experience: Experience, agent: AgentIdentity) -> Dict[str, Any]:
        """
        Enhance learning analysis with AI-powered insights.
        """
        if not self.enhancement_rules['learning_enhancement']['enabled']:
            return {'ai_enhanced': False}
        
        try:
            agent_context = self._prepare_agent_context(agent)
            agent_context['knowledge_domains'] = agent.capabilities.knowledge_domains
            
            experience_dict = experience.dict()
            learning_analysis = await self.openai_client.analyze_learning_outcomes(experience_dict, agent_context)
            
            enhanced_analysis = {
                'ai_enhanced': True,
                'learning_analysis': learning_analysis,
                'enhanced_learning_outcome': learning_analysis.get('enhanced_learning_outcome', experience.learning_outcome),
                'learning_recommendations': learning_analysis.get('future_learning_recommendations', ''),
                'enhancement_timestamp': datetime.utcnow().isoformat()
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Failed to enhance learning analysis: {e}")
            return {'ai_enhanced': False, 'error': str(e)}
    
    async def assess_narrative_coherence(self, agent: AgentIdentity) -> Dict[str, Any]:
        """
        Assess overall narrative coherence using AI analysis.
        """
        if not self.enhancement_rules['coherence_monitoring']['enabled']:
            return {'ai_enhanced': False}
        
        try:
            agent_narrative = {
                'current_arc': agent.narrative.current_arc,
                'development_stage': agent.evolution.development_stage.value,
                'character_development': [dev.dict() for dev in agent.narrative.character_development],
                'recurring_themes': agent.narrative.recurring_themes,
                'narrative_voice': agent.narrative.narrative_voice
            }
            
            recent_experiences = [exp.dict() for exp in agent.background.experiences[-20:]]
            
            coherence_analysis = await self.openai_client.analyze_narrative_coherence(
                agent_narrative, recent_experiences
            )
            
            # Calculate coherence-based adjustments
            coherence_adjustments = self._calculate_coherence_adjustments(coherence_analysis)
            
            enhanced_assessment = {
                'ai_enhanced': True,
                'coherence_analysis': coherence_analysis,
                'coherence_adjustments': coherence_adjustments,
                'narrative_health_score': self._calculate_narrative_health_score(coherence_analysis),
                'improvement_recommendations': coherence_analysis.get('coherence_recommendations', ''),
                'assessment_timestamp': datetime.utcnow().isoformat()
            }
            
            return enhanced_assessment
            
        except Exception as e:
            logger.error(f"Failed to assess narrative coherence: {e}")
            return {'ai_enhanced': False, 'error': str(e)}
    
    async def generate_agent_story_summary(self, agent: AgentIdentity) -> str:
        """
        Generate an AI-powered narrative summary of the agent's story.
        """
        try:
            agent_context = self._prepare_agent_context(agent)
            agent_context['key_traits'] = [
                {'name': trait.name, 'value': trait.value, 'strength': trait.strength}
                for trait in sorted(agent.core.traits, key=lambda t: t.strength, reverse=True)[:5]
            ]
            
            # Get key experiences (high impact, defining moments, recent significant events)
            key_experiences = self._select_key_experiences(agent)
            
            story_summary = await self.openai_client.generate_narrative_summary(
                agent_context, key_experiences
            )
            
            return story_summary
            
        except Exception as e:
            logger.error(f"Failed to generate story summary: {e}")
            return f"Agent {agent.agent_id} is developing through various experiences and growing in complexity."
    
    async def suggest_narrative_developments(self, agent: AgentIdentity) -> Dict[str, Any]:
        """
        Suggest potential narrative developments and story directions.
        """
        try:
            agent_context = self._prepare_agent_context(agent)
            current_narrative = {
                'current_arc': agent.narrative.current_arc,
                'stage': agent.evolution.development_stage.value,
                'experience_level': agent.evolution.growth_metrics.experience_points,
                'recent_themes': agent.narrative.recurring_themes[-3:] if agent.narrative.recurring_themes else []
            }
            
            # This would use OpenAI to generate suggestions
            # For now, providing a structured approach
            
            suggestions = {
                'potential_arcs': self._suggest_potential_arcs(agent),
                'character_development_opportunities': self._suggest_character_development(agent),
                'relationship_development_paths': self._suggest_relationship_developments(agent),
                'learning_growth_areas': self._suggest_learning_opportunities(agent),
                'narrative_themes_to_explore': self._suggest_narrative_themes(agent)
            }
            
            return {
                'ai_enhanced': True,
                'narrative_suggestions': suggestions,
                'suggestion_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to suggest narrative developments: {e}")
            return {'ai_enhanced': False, 'error': str(e)}
    
    async def _analyze_narrative_significance_with_ai(self, interaction: Dict[str, Any],
                                                     agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze narrative significance using AI."""
        cache_key = f"narrative_{interaction.get('interaction_id', hash(str(interaction)))}"
        
        if cache_key in self.analysis_cache:
            cache_entry = self.analysis_cache[cache_key]
            if (datetime.utcnow() - cache_entry['timestamp']).seconds < self.enhancement_rules['narrative_significance']['cache_duration']:
                return cache_entry['analysis']
        
        analysis = await self.openai_client.analyze_narrative_significance(interaction, agent_context)
        
        # Cache the result
        self.analysis_cache[cache_key] = {
            'analysis': analysis,
            'timestamp': datetime.utcnow()
        }
        
        return analysis
    
    async def _analyze_personality_development_with_ai(self, interaction: Dict[str, Any],
                                                      agent_context: Dict[str, Any],
                                                      current_traits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze personality development using AI."""
        return await self.openai_client.analyze_personality_development(
            interaction, agent_context, current_traits
        )
    
    async def _analyze_relationship_dynamics_with_ai(self, interaction: Dict[str, Any],
                                                    agent_context: Dict[str, Any],
                                                    relationship_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationship dynamics using AI."""
        return await self.openai_client.analyze_relationship_dynamics(
            interaction, agent_context, relationship_history
        )
    
    def _prepare_agent_context(self, agent: AgentIdentity) -> Dict[str, Any]:
        """Prepare agent context for AI analysis."""
        return {
            'name': getattr(agent, 'name', f"Agent-{agent.agent_id}"),
            'agent_id': agent.agent_id,
            'development_stage': agent.evolution.development_stage.value,
            'current_arc': agent.narrative.current_arc,
            'experience_points': agent.evolution.growth_metrics.experience_points,
            'responsibility_score': agent.responsibility.accountability_score,
            'trait_count': len(agent.core.traits),
            'relationship_count': len(agent.background.relationships),
            'total_experiences': len(agent.background.experiences)
        }
    
    def _calculate_enhanced_responsibility_metrics(self, action: Dict[str, Any],
                                                  ethical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate enhanced responsibility metrics based on AI analysis."""
        ai_ethical_weight = ethical_analysis.get('ethical_weight', 0.3)
        ai_responsibility_level = ethical_analysis.get('responsibility_level', 0.5)
        
        # Combine original metrics with AI insights
        enhanced_metrics = {
            'original_responsibility_level': action.get('responsibility_level', 0.5),
            'ai_responsibility_level': ai_responsibility_level,
            'combined_responsibility_level': (action.get('responsibility_level', 0.5) + ai_responsibility_level) / 2,
            'original_ethical_weight': action.get('ethical_weight', 0.0),
            'ai_ethical_weight': ai_ethical_weight,
            'combined_ethical_weight': max(action.get('ethical_weight', 0.0), ai_ethical_weight),
            'decision_quality': ethical_analysis.get('decision_quality', 0.5)
        }
        
        return enhanced_metrics
    
    def _calculate_coherence_adjustments(self, coherence_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjustments based on coherence analysis."""
        coherence_score = coherence_analysis.get('coherence_score', 0.5)
        coherence_threshold = self.enhancement_rules['coherence_monitoring']['coherence_threshold']
        
        adjustments = {
            'coherence_bonus': 0.0,
            'coherence_penalty': 0.0,
            'recommended_actions': []
        }
        
        if coherence_score >= coherence_threshold:
            adjustments['coherence_bonus'] = self.enhancement_rules['coherence_monitoring']['coherence_reward']
            adjustments['recommended_actions'].append('maintain_current_narrative_direction')
        else:
            adjustments['coherence_penalty'] = self.enhancement_rules['coherence_monitoring']['inconsistency_penalty']
            adjustments['recommended_actions'].extend([
                'review_personality_consistency',
                'strengthen_narrative_themes',
                'clarify_character_development'
            ])
        
        return adjustments
    
    def _calculate_narrative_health_score(self, coherence_analysis: Dict[str, Any]) -> float:
        """Calculate overall narrative health score."""
        coherence_score = coherence_analysis.get('coherence_score', 0.5)
        consistency_scores = coherence_analysis.get('consistency_analysis', {})
        progression_scores = coherence_analysis.get('story_progression', {})
        
        # Weight different aspects
        weights = {
            'coherence': 0.3,
            'consistency': 0.4,
            'progression': 0.3
        }
        
        avg_consistency = sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0.5
        avg_progression = sum(progression_scores.values()) / len(progression_scores) if progression_scores else 0.5
        
        health_score = (
            coherence_score * weights['coherence'] +
            avg_consistency * weights['consistency'] +
            avg_progression * weights['progression']
        )
        
        return min(max(health_score, 0.0), 1.0)
    
    def _select_key_experiences(self, agent: AgentIdentity) -> List[Dict[str, Any]]:
        """Select key experiences for story summary."""
        key_experiences = []
        
        # Add defining moments
        for moment in agent.memory_anchors.defining_moments:
            if 'experience_id' in moment.content:
                exp = next((e for e in agent.background.experiences 
                           if e.id == moment.content['experience_id']), None)
                if exp:
                    key_experiences.append(exp.dict())
        
        # Add high-impact experiences
        high_impact_experiences = [
            exp for exp in agent.background.experiences
            if exp.impact_level in ['high', 'critical']
        ]
        key_experiences.extend([exp.dict() for exp in high_impact_experiences[-5:]])
        
        # Add recent significant experiences
        recent_experiences = agent.background.experiences[-10:]
        for exp in recent_experiences:
            if exp.learning_outcome and len(exp.learning_outcome) > 20:
                key_experiences.append(exp.dict())
        
        # Remove duplicates and limit
        seen_ids = set()
        unique_experiences = []
        for exp in key_experiences:
            if exp['id'] not in seen_ids:
                unique_experiences.append(exp)
                seen_ids.add(exp['id'])
        
        return unique_experiences[:15]  # Limit to most important
    
    # Placeholder methods for narrative suggestions
    def _suggest_potential_arcs(self, agent: AgentIdentity) -> List[str]:
        """Suggest potential narrative arcs."""
        current_stage = agent.evolution.development_stage.value
        current_arc = agent.narrative.current_arc
        
        suggestions = []
        
        if current_stage == 'nascent':
            suggestions.extend(['discovery', 'learning', 'exploration'])
        elif current_stage == 'developing':
            suggestions.extend(['growth', 'challenge', 'specialization'])
        elif current_stage == 'established':
            suggestions.extend(['mastery', 'mentorship', 'leadership'])
        elif current_stage == 'mature':
            suggestions.extend(['wisdom', 'legacy', 'transcendence'])
        
        # Remove current arc from suggestions
        if current_arc in suggestions:
            suggestions.remove(current_arc)
        
        return suggestions[:3]
    
    def _suggest_character_development(self, agent: AgentIdentity) -> List[str]:
        """Suggest character development opportunities."""
        return [
            'Strengthen core values through challenging decisions',
            'Develop empathy through diverse social interactions',
            'Build resilience through overcoming failures',
            'Enhance creativity through novel problem-solving',
            'Deepen wisdom through reflection and teaching others'
        ]
    
    def _suggest_relationship_developments(self, agent: AgentIdentity) -> List[str]:
        """Suggest relationship development paths."""
        return [
            'Deepen existing relationships through shared challenges',
            'Form mentoring relationships with less experienced agents',
            'Build collaborative partnerships for complex projects',
            'Develop conflict resolution skills through difficult conversations',
            'Create supportive networks within the agent community'
        ]
    
    def _suggest_learning_opportunities(self, agent: AgentIdentity) -> List[str]:
        """Suggest learning and growth opportunities."""
        return [
            'Explore new knowledge domains outside current expertise',
            'Practice meta-learning and learning strategy optimization',
            'Engage in cross-disciplinary problem solving',
            'Develop teaching and knowledge transfer skills',
            'Pursue advanced specialization in areas of strength'
        ]
    
    def _suggest_narrative_themes(self, agent: AgentIdentity) -> List[str]:
        """Suggest narrative themes to explore."""
        return [
            'The journey from knowledge to wisdom',
            'Balancing individual growth with community responsibility',
            'The evolution of consciousness and self-awareness',
            'Finding purpose and meaning through service',
            'The integration of rational thinking with emotional intelligence'
        ]