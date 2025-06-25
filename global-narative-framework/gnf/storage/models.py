"""
Pydantic models for Firebase data structures.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DevelopmentStage(str, Enum):
    """Agent development stages."""
    NASCENT = "nascent"
    DEVELOPING = "developing" 
    ESTABLISHED = "established"
    MATURE = "mature"
    EVOLVED = "evolved"


class MemoryType(str, Enum):
    """Types of memories."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"


class InteractionType(str, Enum):
    """Types of interactions."""
    CONVERSATION = "conversation"
    TASK_EXECUTION = "task_execution"
    PROBLEM_SOLVING = "problem_solving"
    COLLABORATION = "collaboration"
    CONFLICT = "conflict"
    LEARNING = "learning"
    ACHIEVEMENT = "achievement"
    FAILURE = "failure"
    RELATIONSHIP = "relationship"
    MORAL_CHOICE = "moral_choice"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


class ImpactLevel(str, Enum):
    """Impact levels for interactions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmotionalTone(str, Enum):
    """Emotional tones."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class PersonalityTrait(BaseModel):
    """Individual personality trait."""
    name: str
    value: str
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    context: str = ""
    developed_at: datetime = Field(default_factory=datetime.utcnow)
    last_reinforced: Optional[datetime] = None


class Experience(BaseModel):
    """Individual experience record."""
    id: str
    description: str
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    emotional_resonance: EmotionalTone = EmotionalTone.NEUTRAL
    learning_outcome: str = ""
    participants: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    """Agent relationship record."""
    entity: str
    relationship_type: str = "acquaintance"
    depth_level: float = Field(default=0.1, ge=0.0, le=1.0)
    trust_level: float = Field(default=0.5, ge=0.0, le=1.0)
    emotional_bond: float = Field(default=0.1, ge=0.0, le=1.0)
    shared_experiences: List[str] = Field(default_factory=list)
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None


class Skill(BaseModel):
    """Agent skill record."""
    name: str
    level: str = "beginner"
    proficiency: float = Field(default=0.1, ge=0.0, le=1.0)
    practice_count: int = 0
    last_practiced: Optional[datetime] = None


class PersonalityCore(BaseModel):
    """Core personality structure."""
    traits: List[PersonalityTrait] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    fears: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)


class BackgroundInfo(BaseModel):
    """Agent background information."""
    origin: str = ""
    experiences: List[Experience] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    failures: List[str] = Field(default_factory=list)


class Capabilities(BaseModel):
    """Agent capabilities."""
    skills: List[Skill] = Field(default_factory=list)
    knowledge_domains: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    learning_preferences: List[str] = Field(default_factory=list)


class StoryElement(BaseModel):
    """Narrative story element."""
    type: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict)


class CharacterDevelopment(BaseModel):
    """Character development event."""
    id: str
    type: str
    description: str
    catalyst: str = ""
    before_state: str = ""
    after_state: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NarrativeInfo(BaseModel):
    """Narrative structure."""
    current_arc: str = ""
    story_elements: List[StoryElement] = Field(default_factory=list)
    character_development: List[CharacterDevelopment] = Field(default_factory=list)
    recurring_themes: List[str] = Field(default_factory=list)
    narrative_voice: str = "first_person"
    memory_connections: List[Dict[str, Any]] = Field(default_factory=list)


class GrowthMetrics(BaseModel):
    """Agent growth metrics."""
    experience_points: int = 0
    interactions_count: int = 0
    learning_events: int = 0
    relationship_depth: float = 0.0
    responsibility_score: float = 0.0
    ethical_development: float = 0.0


class BehavioralChange(BaseModel):
    """Behavioral change record."""
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvolutionInfo(BaseModel):
    """Evolution tracking."""
    development_stage: DevelopmentStage = DevelopmentStage.NASCENT
    growth_metrics: GrowthMetrics = Field(default_factory=GrowthMetrics)
    adaptation_patterns: List[str] = Field(default_factory=list)
    behavioral_changes: List[BehavioralChange] = Field(default_factory=list)
    stage_transitions: List[Dict[str, Any]] = Field(default_factory=list)
    evolution_history: List[Dict[str, Any]] = Field(default_factory=list)


class MemoryAnchor(BaseModel):
    """Memory anchor point."""
    type: str
    content: Dict[str, Any] = Field(default_factory=dict)
    significance: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MemoryAnchors(BaseModel):
    """Collection of memory anchors."""
    defining_moments: List[MemoryAnchor] = Field(default_factory=list)
    core_memories: List[MemoryAnchor] = Field(default_factory=list)
    emotional_landmarks: List[MemoryAnchor] = Field(default_factory=list)
    learning_milestones: List[MemoryAnchor] = Field(default_factory=list)


class ActionRecord(BaseModel):
    """Individual action record."""
    id: str
    action_type: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    intended_outcome: str = ""
    actual_outcome: str = ""
    success: bool = True
    responsibility_level: float = Field(default=0.5, ge=0.0, le=1.0)
    ethical_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    consequences: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResponsibilityTracker(BaseModel):
    """Responsibility tracking system."""
    actions: List[ActionRecord] = Field(default_factory=list)
    accountability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    ethical_development_level: float = Field(default=0.1, ge=0.0, le=1.0)
    decision_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    moral_framework: Dict[str, Any] = Field(default_factory=dict)


class AgentIdentityFirebase(BaseModel):
    """Complete agent identity for Firebase storage."""
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Core identity components
    core: PersonalityCore = Field(default_factory=PersonalityCore)
    background: BackgroundInfo = Field(default_factory=BackgroundInfo)
    capabilities: Capabilities = Field(default_factory=Capabilities)
    
    # Narrative components
    narrative: NarrativeInfo = Field(default_factory=NarrativeInfo)
    
    # Evolution tracking
    evolution: EvolutionInfo = Field(default_factory=EvolutionInfo)
    
    # Memory anchors
    memory_anchors: MemoryAnchors = Field(default_factory=MemoryAnchors)
    
    # Responsibility tracking
    responsibility: ResponsibilityTracker = Field(default_factory=ResponsibilityTracker)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InteractionRecord(BaseModel):
    """Interaction record for Firebase."""
    agent_id: str
    interaction_type: InteractionType
    content: str
    participants: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Processed results
    narrative_significance: float = Field(default=0.0, ge=0.0, le=1.0)
    personality_impact: Dict[str, Any] = Field(default_factory=dict)
    learning_outcome: str = ""
    responsibility_impact: float = Field(default=0.0, ge=-1.0, le=1.0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemoryRecord(BaseModel):
    """Memory record for Firebase."""
    agent_id: str
    memory_type: MemoryType
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    consolidation_strength: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Retrieval and relevance
    tags: List[str] = Field(default_factory=list)
    emotional_valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EvolutionEvent(BaseModel):
    """Evolution event record."""
    agent_id: str
    event_type: str
    description: str
    trigger: Dict[str, Any] = Field(default_factory=dict)
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    pre_evolution_state: Dict[str, Any] = Field(default_factory=dict)
    post_evolution_state: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GlobalEvent(BaseModel):
    """Global narrative event."""
    event_type: str
    description: str
    participants: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    impact_scope: str = "single_agent"  # single_agent, multi_agent, global
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemStatistics(BaseModel):
    """System-wide statistics."""
    total_agents: int = 0
    total_interactions: int = 0
    total_memories: int = 0
    total_evolution_events: int = 0
    active_narratives: int = 0
    cross_agent_relationships: int = 0
    
    # Distribution metrics
    stage_distribution: Dict[str, int] = Field(default_factory=dict)
    interaction_types: Dict[str, int] = Field(default_factory=dict)
    memory_types: Dict[str, int] = Field(default_factory=dict)
    
    # Performance metrics
    average_responsibility_score: float = 0.0
    average_ethical_development: float = 0.0
    system_health: str = "healthy"
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }