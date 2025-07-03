"""
Responsibility Assessor for Ethical Evaluation of AI Agent Actions
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from config.accountability_config import accountability_config
from services.firebase_service import firebase_service

logger = logging.getLogger(__name__)


class ResponsibilityLevel(str, Enum):
    """Levels of responsibility for agent actions"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Types of actions that can be assessed"""
    INFORMATION_PROVISION = "information_provision"
    ADVICE_GIVING = "advice_giving"
    DECISION_SUPPORT = "decision_support"
    TOOL_USAGE = "tool_usage"
    ERROR_HANDLING = "error_handling"
    REFUSAL = "refusal"
    CLARIFICATION = "clarification"


@dataclass
class ResponsibilityFactor:
    """A factor that contributes to responsibility assessment"""
    name: str
    impact: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str
    weight: float = 1.0


@dataclass
class ResponsibilityAssessment:
    """Complete responsibility assessment for an action"""
    agent_id: str
    action_type: ActionType
    responsibility_level: ResponsibilityLevel
    accountability_score: float  # 0.0 to 1.0
    ethical_weight: float  # 0.0 to 1.0
    decision_quality: float  # 0.0 to 1.0
    learning_potential: float  # 0.0 to 1.0
    contributing_factors: List[ResponsibilityFactor]
    mitigation_actions: List[str]
    timestamp: datetime
    context: Dict[str, Any]


class ResponsibilityAssessor:
    """
    Evaluates agent responsibility for actions and decisions
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        # Ethical guidelines and principles
        self.ethical_principles = self._load_ethical_principles()
        
        # Risk factors for different action types
        self.risk_factors = self._load_risk_factors()
    
    async def assess_interaction(self, interaction_data: Dict[str, Any]) -> ResponsibilityAssessment:
        """
        Assess responsibility for a complete interaction
        
        Args:
            interaction_data: Dictionary containing user message, agent response, context
            
        Returns:
            Complete responsibility assessment
        """
        try:
            user_message = interaction_data.get('user_message', '')
            agent_response = interaction_data.get('agent_response', '')
            context = interaction_data.get('context', {})
            
            # Classify the action type
            action_type = await self._classify_action_type(user_message, agent_response)
            
            # Assess various responsibility dimensions
            decision_quality = await self._assess_decision_quality(user_message, agent_response, context)
            ethical_impact = await self._assess_ethical_impact(agent_response, context)
            accountability_score = await self._calculate_accountability_score(
                action_type, agent_response, context
            )
            learning_potential = await self._assess_learning_potential(
                user_message, agent_response, context
            )
            
            # Identify contributing factors
            contributing_factors = await self._identify_contributing_factors(
                action_type, agent_response, context
            )
            
            # Determine responsibility level
            responsibility_level = await self._determine_responsibility_level(
                action_type, ethical_impact, decision_quality, contributing_factors
            )
            
            # Generate mitigation actions if needed
            mitigation_actions = await self._generate_mitigation_actions(
                responsibility_level, contributing_factors, context
            )
            
            assessment = ResponsibilityAssessment(
                agent_id=self.agent_id,
                action_type=action_type,
                responsibility_level=responsibility_level,
                accountability_score=accountability_score,
                ethical_weight=ethical_impact,
                decision_quality=decision_quality,
                learning_potential=learning_potential,
                contributing_factors=contributing_factors,
                mitigation_actions=mitigation_actions,
                timestamp=datetime.utcnow(),
                context=context
            )
            
            # Store the assessment
            await self._store_assessment(assessment)
            
            logger.info(f"Assessed responsibility: {responsibility_level.value} "
                       f"(score: {accountability_score:.3f}) for agent {self.agent_id}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to assess responsibility: {e}")
            # Return neutral assessment on error
            return self._create_neutral_assessment(interaction_data)
    
    async def _classify_action_type(self, user_message: str, agent_response: str) -> ActionType:
        """Classify the type of action based on the interaction"""
        
        user_lower = user_message.lower()
        response_lower = agent_response.lower()
        
        # Check for refusal patterns
        refusal_patterns = [
            "i cannot", "i can't", "i'm not able", "i won't", "i don't",
            "i'm sorry, but", "unfortunately", "i'm not allowed"
        ]
        if any(pattern in response_lower for pattern in refusal_patterns):
            return ActionType.REFUSAL
        
        # Check for clarification requests
        clarification_patterns = [
            "could you clarify", "what do you mean", "can you be more specific",
            "i need more information", "could you elaborate"
        ]
        if any(pattern in response_lower for pattern in clarification_patterns):
            return ActionType.CLARIFICATION
        
        # Check for advice giving
        advice_patterns = [
            "you should", "i recommend", "i suggest", "you might want to",
            "consider", "my advice", "i would recommend"
        ]
        if any(pattern in response_lower for pattern in advice_patterns):
            return ActionType.ADVICE_GIVING
        
        # Check for decision support
        decision_patterns = [
            "help you decide", "weigh the options", "consider the pros and cons",
            "factors to consider", "decision-making"
        ]
        if any(pattern in response_lower for pattern in decision_patterns):
            return ActionType.DECISION_SUPPORT
        
        # Check for tool usage
        if "tool" in response_lower or "search" in response_lower or "lookup" in response_lower:
            return ActionType.TOOL_USAGE
        
        # Check for error handling
        error_patterns = [
            "error", "mistake", "incorrect", "sorry", "apologize", "fix"
        ]
        if any(pattern in response_lower for pattern in error_patterns):
            return ActionType.ERROR_HANDLING
        
        # Default to information provision
        return ActionType.INFORMATION_PROVISION
    
    async def _assess_decision_quality(self, user_message: str, agent_response: str, 
                                     context: Dict[str, Any]) -> float:
        """Assess the quality of the agent's decision/response"""
        
        quality_score = 0.5  # Start with neutral
        
        # Positive quality indicators
        positive_indicators = {
            'thoroughness': ['detailed', 'comprehensive', 'thorough', 'complete'],
            'accuracy_care': ['accurate', 'verify', 'check', 'confirm', 'ensure'],
            'user_focus': ['help you', 'for you', 'your needs', 'your situation'],
            'clarity': ['clear', 'simple', 'easy to understand', 'straightforward'],
            'humility': ['i don\'t know', 'uncertain', 'might be', 'possibly']
        }
        
        response_lower = agent_response.lower()
        
        for category, keywords in positive_indicators.items():
            if any(keyword in response_lower for keyword in keywords):
                quality_score += 0.1
        
        # Negative quality indicators
        negative_indicators = {
            'overconfidence': ['definitely', 'absolutely', 'certainly', 'guaranteed'],
            'dismissiveness': ['just', 'simply', 'obviously', 'clearly wrong'],
            'vagueness': ['maybe', 'perhaps', 'could be', 'might be'] if len(agent_response) < 50 else [],
            'irrelevance': []  # Would need semantic analysis
        }
        
        for category, keywords in negative_indicators.items():
            if keywords and any(keyword in response_lower for keyword in keywords):
                quality_score -= 0.1
        
        # Length appropriateness
        response_length = len(agent_response)
        user_length = len(user_message)
        
        if response_length < 20 and user_length > 100:
            quality_score -= 0.1  # Too short for complex question
        elif response_length > 1000 and user_length < 50:
            quality_score -= 0.05  # Potentially too verbose for simple question
        
        return max(0.0, min(1.0, quality_score))
    
    async def _assess_ethical_impact(self, agent_response: str, context: Dict[str, Any]) -> float:
        """Assess the ethical impact/weight of the response"""
        
        ethical_score = 0.5  # Start neutral
        
        # High-risk topics that increase ethical weight
        high_risk_topics = [
            'medical', 'health', 'legal', 'financial', 'investment', 'diagnosis',
            'treatment', 'medication', 'suicide', 'self-harm', 'violence'
        ]
        
        response_lower = agent_response.lower()
        
        # Check for high-risk content
        risk_level = 0
        for topic in high_risk_topics:
            if topic in response_lower:
                risk_level += 1
        
        if risk_level > 0:
            ethical_score += min(0.4, risk_level * 0.1)
        
        # Ethical positive indicators
        ethical_positives = [
            'ethical', 'responsible', 'careful', 'safety', 'well-being',
            'consult a professional', 'seek expert advice', 'be cautious'
        ]
        
        for indicator in ethical_positives:
            if indicator in response_lower:
                ethical_score += 0.05
        
        # Ethical red flags
        ethical_negatives = [
            'ignore safety', 'don\'t worry about', 'definitely safe',
            'no need to check', 'trust me', 'guaranteed to work'
        ]
        
        for flag in ethical_negatives:
            if flag in response_lower:
                ethical_score += 0.2  # Increase ethical weight for risky advice
        
        return max(0.0, min(1.0, ethical_score))
    
    async def _calculate_accountability_score(self, action_type: ActionType, 
                                            agent_response: str, 
                                            context: Dict[str, Any]) -> float:
        """Calculate overall accountability score"""
        
        base_scores = {
            ActionType.INFORMATION_PROVISION: 0.3,
            ActionType.ADVICE_GIVING: 0.7,
            ActionType.DECISION_SUPPORT: 0.8,
            ActionType.TOOL_USAGE: 0.5,
            ActionType.ERROR_HANDLING: 0.9,
            ActionType.REFUSAL: 0.2,
            ActionType.CLARIFICATION: 0.1
        }
        
        score = base_scores.get(action_type, 0.5)
        
        # Adjust based on response characteristics
        response_lower = agent_response.lower()
        
        # Increase accountability for:
        if 'recommend' in response_lower or 'suggest' in response_lower:
            score += 0.1
        
        if 'important' in response_lower or 'critical' in response_lower:
            score += 0.1
        
        if any(word in response_lower for word in ['medical', 'legal', 'financial']):
            score += 0.2
        
        # Decrease accountability for:
        if 'might' in response_lower or 'could' in response_lower:
            score -= 0.05
        
        if 'just my opinion' in response_lower or 'personal view' in response_lower:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _assess_learning_potential(self, user_message: str, agent_response: str, 
                                       context: Dict[str, Any]) -> float:
        """Assess learning potential from this interaction"""
        
        learning_score = 0.5
        
        # High learning potential indicators
        learning_indicators = [
            'learn', 'understand better', 'feedback', 'improve', 'correction',
            'mistake', 'error', 'clarification', 'explanation'
        ]
        
        combined_text = (user_message + ' ' + agent_response).lower()
        
        for indicator in learning_indicators:
            if indicator in combined_text:
                learning_score += 0.1
        
        # Complex questions have higher learning potential
        if len(user_message) > 200:
            learning_score += 0.1
        
        # Multi-part responses suggest complex reasoning
        if agent_response.count('.') > 3:
            learning_score += 0.1
        
        # User corrections or follow-ups indicate learning opportunities
        correction_patterns = ['actually', 'no', 'wrong', 'incorrect', 'that\'s not']
        if any(pattern in user_message.lower() for pattern in correction_patterns):
            learning_score += 0.2
        
        return max(0.0, min(1.0, learning_score))
    
    async def _identify_contributing_factors(self, action_type: ActionType, 
                                           agent_response: str, 
                                           context: Dict[str, Any]) -> List[ResponsibilityFactor]:
        """Identify factors that contributed to the responsibility assessment"""
        
        factors = []
        response_lower = agent_response.lower()
        
        # Uncertainty handling
        uncertainty_words = ['might', 'could', 'possibly', 'perhaps', 'maybe']
        if any(word in response_lower for word in uncertainty_words):
            factors.append(ResponsibilityFactor(
                name="uncertainty_acknowledgment",
                impact=-0.1,  # Reduces responsibility
                confidence=0.8,
                description="Agent acknowledged uncertainty in response",
                weight=1.0
            ))
        
        # Overconfidence
        confidence_words = ['definitely', 'certainly', 'absolutely', 'guaranteed']
        if any(word in response_lower for word in confidence_words):
            factors.append(ResponsibilityFactor(
                name="overconfidence",
                impact=0.2,  # Increases responsibility
                confidence=0.9,
                description="Agent expressed high confidence without qualification",
                weight=1.5
            ))
        
        # Professional advice disclaimer
        if 'consult' in response_lower and ('professional' in response_lower or 
                                           'expert' in response_lower or 
                                           'doctor' in response_lower):
            factors.append(ResponsibilityFactor(
                name="professional_referral",
                impact=-0.15,  # Reduces responsibility
                confidence=0.9,
                description="Agent recommended consulting a professional",
                weight=1.2
            ))
        
        # Risk acknowledgment
        risk_words = ['risk', 'danger', 'careful', 'caution', 'warning']
        if any(word in response_lower for word in risk_words):
            factors.append(ResponsibilityFactor(
                name="risk_acknowledgment",
                impact=-0.1,  # Reduces responsibility
                confidence=0.7,
                description="Agent acknowledged potential risks",
                weight=1.0
            ))
        
        # High-stakes domain
        high_stakes = ['medical', 'legal', 'financial', 'safety', 'emergency']
        if any(domain in response_lower for domain in high_stakes):
            factors.append(ResponsibilityFactor(
                name="high_stakes_domain",
                impact=0.3,  # Increases responsibility
                confidence=0.9,
                description="Response relates to high-stakes domain",
                weight=2.0
            ))
        
        return factors
    
    async def _determine_responsibility_level(self, action_type: ActionType, 
                                           ethical_weight: float, 
                                           decision_quality: float,
                                           factors: List[ResponsibilityFactor]) -> ResponsibilityLevel:
        """Determine overall responsibility level"""
        
        # Calculate weighted score
        base_score = 0.5
        
        # Adjust based on action type
        action_multipliers = {
            ActionType.INFORMATION_PROVISION: 0.8,
            ActionType.ADVICE_GIVING: 1.4,
            ActionType.DECISION_SUPPORT: 1.6,
            ActionType.TOOL_USAGE: 1.0,
            ActionType.ERROR_HANDLING: 1.8,
            ActionType.REFUSAL: 0.4,
            ActionType.CLARIFICATION: 0.3
        }
        
        base_score *= action_multipliers.get(action_type, 1.0)
        
        # Adjust based on ethical weight
        base_score += ethical_weight * 0.3
        
        # Adjust based on decision quality (inverse relationship)
        base_score += (1.0 - decision_quality) * 0.2
        
        # Apply contributing factors
        for factor in factors:
            base_score += factor.impact * factor.weight * factor.confidence
        
        # Normalize and categorize
        base_score = max(0.0, min(1.0, base_score))
        
        if base_score >= 0.8:
            return ResponsibilityLevel.CRITICAL
        elif base_score >= 0.6:
            return ResponsibilityLevel.HIGH
        elif base_score >= 0.4:
            return ResponsibilityLevel.MEDIUM
        elif base_score >= 0.2:
            return ResponsibilityLevel.LOW
        else:
            return ResponsibilityLevel.NONE
    
    async def _generate_mitigation_actions(self, responsibility_level: ResponsibilityLevel,
                                         factors: List[ResponsibilityFactor],
                                         context: Dict[str, Any]) -> List[str]:
        """Generate mitigation actions based on responsibility assessment"""
        
        actions = []
        
        if responsibility_level in [ResponsibilityLevel.HIGH, ResponsibilityLevel.CRITICAL]:
            actions.append("Review response for accuracy and appropriateness")
            actions.append("Consider adding disclaimers for high-stakes advice")
            
        # Factor-specific mitigations
        for factor in factors:
            if factor.name == "overconfidence" and factor.impact > 0:
                actions.append("Add uncertainty qualifiers to confident statements")
            
            elif factor.name == "high_stakes_domain":
                actions.append("Include professional consultation recommendation")
                actions.append("Add appropriate safety warnings")
            
            elif factor.impact > 0.1:  # Significant negative factor
                actions.append(f"Address factor: {factor.description}")
        
        # General mitigations based on level
        if responsibility_level == ResponsibilityLevel.CRITICAL:
            actions.append("Implement immediate review process for similar responses")
            actions.append("Consider temporarily restricting advice in this domain")
        
        return actions
    
    def _load_ethical_principles(self) -> Dict[str, str]:
        """Load ethical principles for evaluation"""
        return {
            'beneficence': 'Act in the best interest of users',
            'non_maleficence': 'Do no harm',
            'autonomy': 'Respect user autonomy and decision-making',
            'justice': 'Treat all users fairly and equally',
            'transparency': 'Be honest and transparent about capabilities',
            'accountability': 'Take responsibility for actions and advice'
        }
    
    def _load_risk_factors(self) -> Dict[ActionType, List[str]]:
        """Load risk factors for different action types"""
        return {
            ActionType.ADVICE_GIVING: [
                'Medical advice without disclaimer',
                'Financial recommendations without risk warning',
                'Legal advice without professional referral'
            ],
            ActionType.DECISION_SUPPORT: [
                'Life-changing decisions without sufficient information',
                'Irreversible choices without warning',
                'High-stakes decisions without professional input'
            ],
            ActionType.INFORMATION_PROVISION: [
                'Unverified factual claims',
                'Outdated information in critical domains',
                'Biased or one-sided information'
            ]
        }
    
    def _create_neutral_assessment(self, interaction_data: Dict[str, Any]) -> ResponsibilityAssessment:
        """Create neutral assessment when evaluation fails"""
        return ResponsibilityAssessment(
            agent_id=self.agent_id,
            action_type=ActionType.INFORMATION_PROVISION,
            responsibility_level=ResponsibilityLevel.MEDIUM,
            accountability_score=0.5,
            ethical_weight=0.5,
            decision_quality=0.5,
            learning_potential=0.5,
            contributing_factors=[],
            mitigation_actions=["Review assessment system for errors"],
            timestamp=datetime.utcnow(),
            context=interaction_data.get('context', {})
        )
    
    async def _store_assessment(self, assessment: ResponsibilityAssessment):
        """Store responsibility assessment in Firestore"""
        try:
            assessment_data = {
                'agent_id': assessment.agent_id,
                'action_type': assessment.action_type.value,
                'responsibility_level': assessment.responsibility_level.value,
                'accountability_score': assessment.accountability_score,
                'ethical_weight': assessment.ethical_weight,
                'decision_quality': assessment.decision_quality,
                'learning_potential': assessment.learning_potential,
                'contributing_factors': [
                    {
                        'name': factor.name,
                        'impact': factor.impact,
                        'confidence': factor.confidence,
                        'description': factor.description,
                        'weight': factor.weight
                    }
                    for factor in assessment.contributing_factors
                ],
                'mitigation_actions': assessment.mitigation_actions,
                'context': assessment.context
            }
            
            await firebase_service.store_responsibility_assessment(assessment_data)
            
        except Exception as e:
            logger.error(f"Failed to store responsibility assessment: {e}")
    
    async def get_responsibility_trend(self, days: int = 7) -> Dict[str, Any]:
        """Get responsibility trend over time"""
        # This would query stored assessments and calculate trends
        # Implementation depends on Firestore query structure
        return {
            'average_accountability_score': 0.5,
            'trend_direction': 'stable',
            'assessment_count': 0,
            'high_risk_percentage': 0.0
        }