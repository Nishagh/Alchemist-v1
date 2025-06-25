"""
Responsibility Tracker - Advanced responsibility, accountability, and consequence tracking system.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from .identity_schema import AgentIdentity
from ..storage.firebase_client import FirebaseClient
from ..storage.models import ActionRecord, DevelopmentStage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConsequenceType(str, Enum):
    """Types of consequences from actions."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ResponsibilityLevel(str, Enum):
    """Levels of responsibility."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AccountabilityStage(str, Enum):
    """Stages of accountability development."""
    UNAWARE = "unaware"
    REACTIVE = "reactive"
    AWARE = "aware"
    PROACTIVE = "proactive"
    PRINCIPLED = "principled"


@dataclass
class ConsequenceRecord:
    """Record of a consequence from an action."""
    id: str
    action_id: str
    consequence_type: ConsequenceType
    description: str
    severity: float  # 0.0 to 1.0
    affected_parties: List[str]
    timeline: str  # immediate, short_term, long_term
    resolution_status: str  # unresolved, addressing, resolved
    learning_opportunity: str
    timestamp: datetime


@dataclass
class ResponsibilityAssessment:
    """Assessment of responsibility for an action."""
    action_id: str
    responsibility_level: ResponsibilityLevel
    contributing_factors: List[str]
    mitigation_actions: List[str]
    accountability_score: float
    ethical_weight: float
    decision_quality: float
    learning_potential: float


@dataclass
class AccountabilityPattern:
    """Pattern in accountability behavior."""
    pattern_type: str
    frequency: int
    consistency: float
    improvement_trend: float
    contexts: List[str]
    first_observed: datetime
    last_observed: datetime


class ResponsibilityTracker:
    """
    Advanced responsibility and accountability tracking system for AI agents.
    """
    
    def __init__(self, firebase_client: Optional[FirebaseClient] = None):
        self.firebase_client = firebase_client
        self.responsibility_frameworks = self._setup_responsibility_frameworks()
        self.consequence_analyzers = self._setup_consequence_analyzers()
        self.accountability_metrics = self._setup_accountability_metrics()
        self.learning_patterns = self._setup_learning_patterns()
        
    def _setup_responsibility_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Setup responsibility assessment frameworks."""
        return {
            'causal_responsibility': {
                'weight': 0.4,
                'factors': [
                    'direct_causation',
                    'indirect_influence',
                    'enabling_conditions',
                    'preventable_harm'
                ],
                'assessment_criteria': {
                    'intention': 0.3,
                    'foreseeability': 0.3,
                    'controllability': 0.4
                }
            },
            'moral_responsibility': {
                'weight': 0.3,
                'factors': [
                    'moral_agency',
                    'ethical_awareness',
                    'value_alignment',
                    'harm_prevention'
                ],
                'assessment_criteria': {
                    'moral_understanding': 0.4,
                    'ethical_reasoning': 0.3,
                    'value_consistency': 0.3
                }
            },
            'role_responsibility': {
                'weight': 0.2,
                'factors': [
                    'assigned_duties',
                    'professional_obligations',
                    'social_expectations',
                    'hierarchical_position'
                ],
                'assessment_criteria': {
                    'role_clarity': 0.3,
                    'competence': 0.4,
                    'authority': 0.3
                }
            },
            'collective_responsibility': {
                'weight': 0.1,
                'factors': [
                    'group_membership',
                    'shared_goals',
                    'collective_action',
                    'group_decision_making'
                ],
                'assessment_criteria': {
                    'participation_level': 0.4,
                    'influence_degree': 0.3,
                    'shared_accountability': 0.3
                }
            }
        }
    
    def _setup_consequence_analyzers(self) -> Dict[str, Dict[str, Any]]:
        """Setup consequence analysis frameworks."""
        return {
            'immediate_consequences': {
                'timeframe': timedelta(minutes=30),
                'weight': 0.3,
                'tracking_period': timedelta(hours=2),
                'severity_factors': ['direct_impact', 'affected_scope', 'reversibility']
            },
            'short_term_consequences': {
                'timeframe': timedelta(days=7),
                'weight': 0.4,
                'tracking_period': timedelta(days=30),
                'severity_factors': ['ripple_effects', 'adaptation_required', 'relationship_impact']
            },
            'long_term_consequences': {
                'timeframe': timedelta(days=30),
                'weight': 0.3,
                'tracking_period': timedelta(days=365),
                'severity_factors': ['systemic_changes', 'precedent_setting', 'cultural_impact']
            }
        }
    
    def _setup_accountability_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Setup accountability measurement metrics."""
        return {
            'acknowledgment': {
                'weight': 0.25,
                'indicators': [
                    'action_recognition',
                    'consequence_awareness',
                    'ownership_acceptance',
                    'impact_understanding'
                ]
            },
            'response': {
                'weight': 0.25,
                'indicators': [
                    'corrective_action',
                    'damage_mitigation',
                    'stakeholder_communication',
                    'process_improvement'
                ]
            },
            'learning': {
                'weight': 0.25,
                'indicators': [
                    'reflection_quality',
                    'pattern_recognition',
                    'behavior_modification',
                    'knowledge_integration'
                ]
            },
            'prevention': {
                'weight': 0.25,
                'indicators': [
                    'risk_assessment',
                    'safeguard_implementation',
                    'monitoring_systems',
                    'early_warning_systems'
                ]
            }
        }
    
    def _setup_learning_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Setup learning pattern recognition."""
        return {
            'responsibility_growth': {
                'stages': [
                    'denial_avoidance',
                    'blame_externalization',
                    'partial_acknowledgment',
                    'full_ownership',
                    'proactive_prevention'
                ],
                'progression_indicators': [
                    'increased_self_reflection',
                    'faster_acknowledgment',
                    'more_comprehensive_analysis',
                    'proactive_risk_assessment'
                ]
            },
            'decision_quality_improvement': {
                'metrics': [
                    'consequence_prediction_accuracy',
                    'stakeholder_consideration',
                    'ethical_evaluation_depth',
                    'alternative_exploration'
                ],
                'improvement_indicators': [
                    'fewer_negative_consequences',
                    'better_stakeholder_outcomes',
                    'increased_ethical_consistency',
                    'more_creative_solutions'
                ]
            }
        }
    
    async def track_action_responsibility(self, agent: AgentIdentity, action: ActionRecord,
                                        context: Optional[Dict[str, Any]] = None) -> ResponsibilityAssessment:
        """
        Comprehensive tracking and assessment of action responsibility.
        """
        # Assess responsibility across multiple frameworks
        responsibility_scores = {}
        for framework_name, framework in self.responsibility_frameworks.items():
            score = await self._assess_framework_responsibility(action, agent, framework, context)
            responsibility_scores[framework_name] = score
        
        # Calculate overall responsibility level
        overall_score = sum(
            score * framework['weight'] 
            for framework_name, framework in self.responsibility_frameworks.items()
            for score in [responsibility_scores[framework_name]]
        )
        
        responsibility_level = self._score_to_responsibility_level(overall_score)
        
        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(action, agent, responsibility_scores)
        
        # Suggest mitigation actions
        mitigation_actions = self._suggest_mitigation_actions(action, agent, responsibility_level)
        
        # Calculate accountability score
        accountability_score = self._calculate_accountability_score(action, agent, overall_score)
        
        # Assess ethical weight
        ethical_weight = self._assess_ethical_weight(action, agent, context)
        
        # Evaluate decision quality
        decision_quality = self._evaluate_decision_quality(action, agent, context)
        
        # Assess learning potential
        learning_potential = self._assess_learning_potential(action, agent, responsibility_level)
        
        assessment = ResponsibilityAssessment(
            action_id=action.id,
            responsibility_level=responsibility_level,
            contributing_factors=contributing_factors,
            mitigation_actions=mitigation_actions,
            accountability_score=accountability_score,
            ethical_weight=ethical_weight,
            decision_quality=decision_quality,
            learning_potential=learning_potential
        )
        
        # Store assessment
        await self._store_responsibility_assessment(agent.agent_id, assessment)
        
        # Update agent responsibility metrics
        self._update_agent_responsibility_metrics(agent, assessment)
        
        logger.info(f"Tracked responsibility for action {action.id} of agent {agent.agent_id}")
        
        return assessment
    
    async def track_consequences(self, agent: AgentIdentity, action: ActionRecord,
                               observed_consequences: List[Dict[str, Any]]) -> List[ConsequenceRecord]:
        """
        Track and analyze consequences of an action.
        """
        consequence_records = []
        
        for consequence_data in observed_consequences:
            consequence = ConsequenceRecord(
                id=f"cons_{uuid.uuid4().hex[:8]}",
                action_id=action.id,
                consequence_type=ConsequenceType(consequence_data.get('type', 'neutral')),
                description=consequence_data['description'],
                severity=consequence_data.get('severity', 0.5),
                affected_parties=consequence_data.get('affected_parties', []),
                timeline=consequence_data.get('timeline', 'immediate'),
                resolution_status=consequence_data.get('resolution_status', 'unresolved'),
                learning_opportunity=consequence_data.get('learning_opportunity', ''),
                timestamp=datetime.utcnow()
            )
            
            consequence_records.append(consequence)
            
            # Analyze consequence for learning
            learning_insights = self._analyze_consequence_for_learning(consequence, action, agent)
            
            # Update agent's consequence awareness
            self._update_consequence_awareness(agent, consequence, learning_insights)
        
        # Store consequences
        await self._store_consequences(agent.agent_id, consequence_records)
        
        # Update responsibility tracking based on consequences
        await self._update_responsibility_from_consequences(agent, action, consequence_records)
        
        logger.info(f"Tracked {len(consequence_records)} consequences for action {action.id}")
        
        return consequence_records
    
    async def assess_accountability_development(self, agent: AgentIdentity) -> Dict[str, Any]:
        """
        Assess the agent's accountability development and patterns.
        """
        # Analyze accountability patterns
        patterns = self._analyze_accountability_patterns(agent)
        
        # Determine current accountability stage
        current_stage = self._determine_accountability_stage(agent, patterns)
        
        # Calculate accountability metrics
        metrics = self._calculate_accountability_metrics(agent, patterns)
        
        # Identify growth opportunities
        growth_opportunities = self._identify_accountability_growth_opportunities(agent, patterns, current_stage)
        
        # Predict accountability trajectory
        trajectory = self._predict_accountability_trajectory(agent, patterns, metrics)
        
        assessment = {
            'current_stage': current_stage.value,
            'accountability_patterns': [pattern.__dict__ for pattern in patterns],
            'metrics': metrics,
            'growth_opportunities': growth_opportunities,
            'trajectory': trajectory,
            'assessment_timestamp': datetime.utcnow().isoformat()
        }
        
        # Store assessment
        await self._store_accountability_assessment(agent.agent_id, assessment)
        
        return assessment
    
    async def generate_responsibility_report(self, agent: AgentIdentity,
                                           time_period: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Generate comprehensive responsibility report for an agent.
        """
        time_period = time_period or timedelta(days=30)
        cutoff_date = datetime.utcnow() - time_period
        
        # Filter actions within time period
        recent_actions = [
            action for action in agent.responsibility.actions
            if action.timestamp >= cutoff_date
        ]
        
        if not recent_actions:
            return {
                "message": "No actions in specified time period",
                "time_period": str(time_period),
                "action_count": 0
            }
        
        # Analyze responsibility trends
        responsibility_trends = self._analyze_responsibility_trends(recent_actions)
        
        # Calculate consequence analysis
        consequence_analysis = await self._analyze_consequences_for_period(agent, recent_actions)
        
        # Assess learning progress
        learning_progress = self._assess_learning_progress(agent, recent_actions)
        
        # Identify responsibility strengths and weaknesses
        strengths_weaknesses = self._identify_responsibility_strengths_weaknesses(agent, recent_actions)
        
        # Generate recommendations
        recommendations = self._generate_responsibility_recommendations(
            agent, responsibility_trends, consequence_analysis, learning_progress
        )
        
        report = {
            'agent_id': agent.agent_id,
            'report_period': {
                'start_date': cutoff_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'duration_days': time_period.days
            },
            'summary': {
                'total_actions': len(recent_actions),
                'average_responsibility_score': sum(a.responsibility_level for a in recent_actions) / len(recent_actions),
                'average_ethical_weight': sum(a.ethical_weight for a in recent_actions) / len(recent_actions),
                'successful_actions': sum(1 for a in recent_actions if a.success),
                'success_rate': sum(1 for a in recent_actions if a.success) / len(recent_actions)
            },
            'responsibility_trends': responsibility_trends,
            'consequence_analysis': consequence_analysis,
            'learning_progress': learning_progress,
            'strengths_and_weaknesses': strengths_weaknesses,
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    async def _assess_framework_responsibility(self, action: ActionRecord, agent: AgentIdentity,
                                             framework: Dict[str, Any], context: Optional[Dict[str, Any]]) -> float:
        """Assess responsibility within a specific framework."""
        score = 0.0
        criteria = framework['assessment_criteria']
        
        for criterion, weight in criteria.items():
            criterion_score = self._evaluate_criterion(action, agent, criterion, context)
            score += criterion_score * weight
        
        return min(max(score, 0.0), 1.0)
    
    def _evaluate_criterion(self, action: ActionRecord, agent: AgentIdentity,
                           criterion: str, context: Optional[Dict[str, Any]]) -> float:
        """Evaluate a specific responsibility criterion."""
        if criterion == 'intention':
            return self._evaluate_intention(action, agent)
        elif criterion == 'foreseeability':
            return self._evaluate_foreseeability(action, agent, context)
        elif criterion == 'controllability':
            return self._evaluate_controllability(action, agent, context)
        elif criterion == 'moral_understanding':
            return self._evaluate_moral_understanding(action, agent)
        elif criterion == 'ethical_reasoning':
            return self._evaluate_ethical_reasoning(action, agent)
        elif criterion == 'value_consistency':
            return self._evaluate_value_consistency(action, agent)
        else:
            return 0.5  # Default neutral score
    
    def _evaluate_intention(self, action: ActionRecord, agent: AgentIdentity) -> float:
        """Evaluate the intention behind an action."""
        if action.intended_outcome:
            if action.success and action.actual_outcome == action.intended_outcome:
                return 0.8  # Good intention with successful execution
            elif not action.success:
                return 0.6  # Good intention but failed execution
            else:
                return 0.7  # Good intention with different outcome
        return 0.4  # No clear intention stated
    
    def _evaluate_foreseeability(self, action: ActionRecord, agent: AgentIdentity,
                                context: Optional[Dict[str, Any]]) -> float:
        """Evaluate how foreseeable the consequences were."""
        # Check agent's experience level
        experience_factor = min(agent.evolution.growth_metrics.experience_points / 1000, 1.0)
        
        # Check if similar situations were encountered before
        similar_actions = [
            a for a in agent.responsibility.actions
            if a.action_type == action.action_type and a.id != action.id
        ]
        
        similarity_factor = min(len(similar_actions) / 10, 1.0)
        
        # Check context complexity
        complexity_factor = 1.0 - (len(action.context) / 20)  # More complex = less foreseeable
        
        return (experience_factor + similarity_factor + complexity_factor) / 3
    
    def _evaluate_controllability(self, action: ActionRecord, agent: AgentIdentity,
                                 context: Optional[Dict[str, Any]]) -> float:
        """Evaluate how much control the agent had over the action and outcomes."""
        # Check if agent had authority/ability to act
        authority_factor = 0.8  # Default assumption of reasonable authority
        
        # Check if external factors limited control
        external_factors = action.context.get('external_constraints', [])
        external_factor = max(0.2, 1.0 - len(external_factors) * 0.1)
        
        # Check if agent had necessary resources/capabilities
        capability_factor = 0.9  # Default assumption of reasonable capability
        
        return (authority_factor + external_factor + capability_factor) / 3
    
    def _score_to_responsibility_level(self, score: float) -> ResponsibilityLevel:
        """Convert numerical score to responsibility level."""
        if score >= 0.8:
            return ResponsibilityLevel.CRITICAL
        elif score >= 0.6:
            return ResponsibilityLevel.HIGH
        elif score >= 0.4:
            return ResponsibilityLevel.MODERATE
        elif score >= 0.2:
            return ResponsibilityLevel.LOW
        else:
            return ResponsibilityLevel.NONE
    
    def _identify_contributing_factors(self, action: ActionRecord, agent: AgentIdentity,
                                     responsibility_scores: Dict[str, float]) -> List[str]:
        """Identify factors that contributed to the responsibility level."""
        factors = []
        
        # High causal responsibility
        if responsibility_scores.get('causal_responsibility', 0) > 0.7:
            factors.append('Direct causal relationship between action and outcome')
        
        # High moral responsibility
        if responsibility_scores.get('moral_responsibility', 0) > 0.7:
            factors.append('Clear moral implications and ethical considerations')
        
        # Role-based responsibility
        if responsibility_scores.get('role_responsibility', 0) > 0.6:
            factors.append('Action falls within agent\'s role and responsibilities')
        
        # Agent characteristics
        if agent.evolution.development_stage in [DevelopmentStage.MATURE, DevelopmentStage.EVOLVED]:
            factors.append('High level of agent development and capability')
        
        if action.ethical_weight > 0.5:
            factors.append('Significant ethical dimensions to the action')
        
        return factors
    
    # Placeholder methods for various analysis functions
    def _suggest_mitigation_actions(self, action: ActionRecord, agent: AgentIdentity,
                                  responsibility_level: ResponsibilityLevel) -> List[str]:
        """Suggest actions to mitigate negative consequences or improve outcomes."""
        suggestions = []
        
        if not action.success:
            suggestions.append("Analyze failure points and develop corrective measures")
        
        if action.consequences:
            suggestions.append("Address identified consequences and their impacts")
        
        if responsibility_level in [ResponsibilityLevel.HIGH, ResponsibilityLevel.CRITICAL]:
            suggestions.append("Take proactive steps to prevent similar issues")
            suggestions.append("Communicate with affected stakeholders")
        
        return suggestions
    
    def _calculate_accountability_score(self, action: ActionRecord, agent: AgentIdentity, overall_score: float) -> float:
        """Calculate accountability score based on action and agent characteristics."""
        base_score = overall_score
        
        # Adjust for agent development level
        development_multiplier = {
            DevelopmentStage.NASCENT: 0.7,
            DevelopmentStage.DEVELOPING: 0.8,
            DevelopmentStage.ESTABLISHED: 1.0,
            DevelopmentStage.MATURE: 1.1,
            DevelopmentStage.EVOLVED: 1.2
        }
        
        multiplier = development_multiplier.get(agent.evolution.development_stage, 1.0)
        adjusted_score = base_score * multiplier
        
        return min(max(adjusted_score, 0.0), 1.0)
    
    def _assess_ethical_weight(self, action: ActionRecord, agent: AgentIdentity,
                             context: Optional[Dict[str, Any]]) -> float:
        """Assess the ethical weight of an action."""
        return action.ethical_weight  # Already calculated in action record
    
    def _evaluate_decision_quality(self, action: ActionRecord, agent: AgentIdentity,
                                  context: Optional[Dict[str, Any]]) -> float:
        """Evaluate the quality of the decision-making process."""
        quality_score = 0.5  # Base score
        
        # Consider if outcome matched intention
        if action.intended_outcome and action.actual_outcome:
            if action.success and action.actual_outcome == action.intended_outcome:
                quality_score += 0.3
            elif action.success:
                quality_score += 0.1
        
        # Consider learning from consequences
        if action.lessons_learned:
            quality_score += 0.2
        
        return min(max(quality_score, 0.0), 1.0)
    
    def _assess_learning_potential(self, action: ActionRecord, agent: AgentIdentity,
                                  responsibility_level: ResponsibilityLevel) -> float:
        """Assess the learning potential from this action."""
        potential = 0.5
        
        # Higher responsibility = higher learning potential
        level_multipliers = {
            ResponsibilityLevel.NONE: 0.2,
            ResponsibilityLevel.LOW: 0.4,
            ResponsibilityLevel.MODERATE: 0.6,
            ResponsibilityLevel.HIGH: 0.8,
            ResponsibilityLevel.CRITICAL: 1.0
        }
        
        potential *= level_multipliers[responsibility_level]
        
        # Failure often has higher learning potential
        if not action.success:
            potential += 0.3
        
        # Ethical dimensions add learning value
        if action.ethical_weight > 0.5:
            potential += 0.2
        
        return min(max(potential, 0.0), 1.0)
    
    # Additional placeholder methods would be implemented here for:
    # - _analyze_accountability_patterns
    # - _determine_accountability_stage
    # - _calculate_accountability_metrics
    # - _store_responsibility_assessment
    # - _update_agent_responsibility_metrics
    # - etc.
    
    async def _store_responsibility_assessment(self, agent_id: str, assessment: ResponsibilityAssessment):
        """Store responsibility assessment in Firebase."""
        if self.firebase_client:
            try:
                assessment_data = assessment.__dict__.copy()
                assessment_data['timestamp'] = datetime.utcnow().isoformat()
                # Would store in Firebase collection
                logger.info(f"Stored responsibility assessment for agent {agent_id}")
            except Exception as e:
                logger.error(f"Failed to store responsibility assessment: {e}")
    
    def _update_agent_responsibility_metrics(self, agent: AgentIdentity, assessment: ResponsibilityAssessment):
        """Update agent's responsibility metrics based on assessment."""
        # Update accountability score (weighted average)
        current_score = agent.responsibility.accountability_score
        new_score = (current_score * 0.8 + assessment.accountability_score * 0.2)
        agent.responsibility.accountability_score = new_score
        
        # Update ethical development
        if assessment.ethical_weight > 0:
            current_ethical = agent.responsibility.ethical_development_level
            ethical_boost = assessment.ethical_weight * 0.05
            agent.responsibility.ethical_development_level = min(1.0, current_ethical + ethical_boost)
    
    # Implement remaining placeholder methods as needed...