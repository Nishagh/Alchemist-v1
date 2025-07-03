"""
Accountability and GNF-specific configuration
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DevelopmentStage(str, Enum):
    """Agent development stages from GNF"""
    NASCENT = "nascent"
    DEVELOPING = "developing"
    ESTABLISHED = "established"
    MATURE = "mature"
    EVOLVED = "evolved"


class InteractionType(str, Enum):
    """Types of agent interactions for narrative tracking"""
    CONVERSATION = "conversation"
    TOOL_USE = "tool_use"
    KNOWLEDGE_SEARCH = "knowledge_search"
    SELF_REFLECTION = "self_reflection"
    ERROR_HANDLING = "error_handling"
    DECISION_MAKING = "decision_making"


@dataclass
class AccountabilityThresholds:
    """Thresholds for accountability metrics"""
    story_loss_warning: float = 0.5
    story_loss_critical: float = 0.8
    responsibility_warning: float = 0.3
    responsibility_critical: float = 0.1
    coherence_warning: float = 0.4
    coherence_critical: float = 0.2
    
    def get_severity_for_story_loss(self, story_loss: float) -> AlertSeverity:
        """Get alert severity for story-loss value"""
        if story_loss >= self.story_loss_critical:
            return AlertSeverity.CRITICAL
        elif story_loss >= self.story_loss_warning:
            return AlertSeverity.HIGH
        else:
            return AlertSeverity.LOW
    
    def get_severity_for_responsibility(self, responsibility: float) -> AlertSeverity:
        """Get alert severity for responsibility score"""
        if responsibility <= self.responsibility_critical:
            return AlertSeverity.CRITICAL
        elif responsibility <= self.responsibility_warning:
            return AlertSeverity.HIGH
        else:
            return AlertSeverity.LOW
    
    def get_severity_for_coherence(self, coherence: float) -> AlertSeverity:
        """Get alert severity for narrative coherence"""
        if coherence <= self.coherence_critical:
            return AlertSeverity.CRITICAL
        elif coherence <= self.coherence_warning:
            return AlertSeverity.HIGH
        else:
            return AlertSeverity.LOW


@dataclass
class NarrativeSettings:
    """Settings for narrative tracking and coherence"""
    max_belief_nodes: int = 1000
    max_action_nodes: int = 500
    belief_confidence_threshold: float = 0.7
    contradiction_detection_threshold: float = 0.8
    memory_consolidation_interval: timedelta = timedelta(hours=1)
    narrative_graph_cleanup_interval: timedelta = timedelta(days=7)
    
    # Personality trait tracking
    max_personality_traits: int = 10
    trait_evolution_threshold: float = 0.1
    core_values_max: int = 5
    primary_goals_max: int = 3


@dataclass
class SelfReflectionSettings:
    """Settings for self-reflection and minion tasks"""
    enable_automatic_reflection: bool = True
    reflection_trigger_conditions: Dict[str, float] = None
    reflection_cooldown: timedelta = timedelta(minutes=30)
    max_reflection_attempts: int = 3
    reflection_prompt_template: str = """
    Based on recent interactions, please reflect on:
    1. Consistency with your stated values and goals
    2. Quality of your recent decisions
    3. Areas for improvement in your responses
    4. Any conflicts between your beliefs and actions
    
    Recent story-loss: {story_loss}
    Responsibility score: {responsibility_score}
    Narrative coherence: {coherence_score}
    """
    
    def __post_init__(self):
        if self.reflection_trigger_conditions is None:
            self.reflection_trigger_conditions = {
                'story_loss_threshold': 0.7,
                'responsibility_drop': 0.2,
                'coherence_drop': 0.3,
                'error_count_threshold': 5
            }


@dataclass
class MonitoringSettings:
    """Settings for real-time monitoring and alerts"""
    enable_real_time_monitoring: bool = True
    monitoring_interval: timedelta = timedelta(minutes=5)
    alert_cooldown: timedelta = timedelta(minutes=15)
    metrics_retention_days: int = 30
    
    # Time-series data collection
    story_loss_sample_interval: timedelta = timedelta(minutes=1)
    metrics_aggregation_window: timedelta = timedelta(hours=1)
    
    # Alert configurations
    enable_email_alerts: bool = False
    enable_webhook_alerts: bool = True
    webhook_url: Optional[str] = None
    alert_recipients: List[str] = None
    
    def __post_init__(self):
        if self.alert_recipients is None:
            self.alert_recipients = []


class AccountabilityConfig:
    """
    Centralized configuration for accountability features
    """
    
    def __init__(self):
        self.thresholds = AccountabilityThresholds()
        self.narrative_settings = NarrativeSettings()
        self.self_reflection_settings = SelfReflectionSettings()
        self.monitoring_settings = MonitoringSettings()
        
        # Alert rules configuration
        self.alert_rules = self._create_default_alert_rules()
        
        # Development stage configuration
        self.development_stages = self._create_development_stage_config()
    
    def _create_default_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Create default alert rules"""
        return {
            'story_loss_threshold': {
                'name': 'Story Loss Threshold Exceeded',
                'alert_type': 'story_loss_threshold',
                'conditions': {
                    'story_loss': {'operator': '>', 'value': self.thresholds.story_loss_warning}
                },
                'severity': 'high',
                'cooldown_minutes': 15,
                'enabled': True,
                'description': 'Triggered when story-loss exceeds threshold'
            },
            'responsibility_drop': {
                'name': 'Responsibility Score Drop',
                'alert_type': 'responsibility_threshold',
                'conditions': {
                    'responsibility_score': {'operator': '<', 'value': self.thresholds.responsibility_warning}
                },
                'severity': 'medium',
                'cooldown_minutes': 10,
                'enabled': True,
                'description': 'Triggered when responsibility score drops below threshold'
            },
            'narrative_coherence_low': {
                'name': 'Low Narrative Coherence',
                'alert_type': 'coherence_threshold',
                'conditions': {
                    'coherence_score': {'operator': '<', 'value': self.thresholds.coherence_warning}
                },
                'severity': 'medium',
                'cooldown_minutes': 20,
                'enabled': True,
                'description': 'Triggered when narrative coherence is low'
            },
            'umwelt_conflict': {
                'name': 'Umwelt Conflict Detected',
                'alert_type': 'umwelt_conflict',
                'conditions': {
                    'conflict_severity': {'operator': '>', 'value': 0.8}
                },
                'severity': 'high',
                'cooldown_minutes': 5,
                'enabled': True,
                'description': 'Triggered when Umwelt conflicts are detected'
            }
        }
    
    def _create_development_stage_config(self) -> Dict[str, Dict[str, Any]]:
        """Create development stage configuration"""
        return {
            DevelopmentStage.NASCENT: {
                'min_experience_points': 0,
                'min_interactions': 0,
                'characteristics': [
                    'Learning basic interaction patterns',
                    'Developing initial personality traits',
                    'Building foundational knowledge'
                ],
                'max_story_loss_tolerance': 0.9,
                'min_responsibility_expectation': 0.3
            },
            DevelopmentStage.DEVELOPING: {
                'min_experience_points': 100,
                'min_interactions': 50,
                'characteristics': [
                    'Establishing consistent behavior patterns',
                    'Refining communication style',
                    'Beginning to show expertise in domain'
                ],
                'max_story_loss_tolerance': 0.8,
                'min_responsibility_expectation': 0.4
            },
            DevelopmentStage.ESTABLISHED: {
                'min_experience_points': 500,
                'min_interactions': 200,
                'characteristics': [
                    'Consistent personality and values',
                    'Reliable decision-making patterns',
                    'Clear expertise in assigned domain'
                ],
                'max_story_loss_tolerance': 0.7,
                'min_responsibility_expectation': 0.5
            },
            DevelopmentStage.MATURE: {
                'min_experience_points': 1000,
                'min_interactions': 500,
                'characteristics': [
                    'Well-developed narrative identity',
                    'High-quality decision making',
                    'Strong ethical framework'
                ],
                'max_story_loss_tolerance': 0.6,
                'min_responsibility_expectation': 0.6
            },
            DevelopmentStage.EVOLVED: {
                'min_experience_points': 2000,
                'min_interactions': 1000,
                'characteristics': [
                    'Sophisticated understanding of context',
                    'Excellent responsibility and ethics',
                    'Capable of self-improvement'
                ],
                'max_story_loss_tolerance': 0.5,
                'min_responsibility_expectation': 0.7
            }
        }
    
    def get_stage_for_metrics(self, experience_points: int, interactions: int) -> DevelopmentStage:
        """Determine development stage based on metrics"""
        for stage in reversed(list(DevelopmentStage)):
            stage_config = self.development_stages[stage]
            if (experience_points >= stage_config['min_experience_points'] and
                interactions >= stage_config['min_interactions']):
                return stage
        return DevelopmentStage.NASCENT
    
    def get_thresholds_for_stage(self, stage: DevelopmentStage) -> Dict[str, float]:
        """Get adjusted thresholds based on development stage"""
        stage_config = self.development_stages[stage]
        
        return {
            'story_loss_threshold': stage_config['max_story_loss_tolerance'],
            'responsibility_threshold': stage_config['min_responsibility_expectation'],
            'coherence_threshold': self.thresholds.coherence_warning
        }
    
    def should_trigger_self_reflection(self, metrics: Dict[str, float]) -> bool:
        """Check if self-reflection should be triggered"""
        if not self.self_reflection_settings.enable_automatic_reflection:
            return False
        
        conditions = self.self_reflection_settings.reflection_trigger_conditions
        
        # Check each trigger condition
        if metrics.get('story_loss', 0) > conditions['story_loss_threshold']:
            return True
        
        if metrics.get('responsibility_drop', 0) > conditions['responsibility_drop']:
            return True
        
        if metrics.get('coherence_drop', 0) > conditions['coherence_drop']:
            return True
        
        if metrics.get('error_count', 0) > conditions['error_count_threshold']:
            return True
        
        return False
    
    def get_alert_rules_for_stage(self, stage: DevelopmentStage) -> Dict[str, Dict[str, Any]]:
        """Get alert rules adjusted for development stage"""
        stage_thresholds = self.get_thresholds_for_stage(stage)
        adjusted_rules = self.alert_rules.copy()
        
        # Adjust thresholds based on development stage
        if 'story_loss_threshold' in adjusted_rules:
            adjusted_rules['story_loss_threshold']['conditions']['story_loss']['value'] = stage_thresholds['story_loss_threshold']
        
        if 'responsibility_drop' in adjusted_rules:
            adjusted_rules['responsibility_drop']['conditions']['responsibility_score']['value'] = stage_thresholds['responsibility_threshold']
        
        return adjusted_rules


# Global configuration instance
accountability_config = AccountabilityConfig()