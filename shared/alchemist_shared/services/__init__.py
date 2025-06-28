"""
Shared Services

Common services used across Alchemist applications.
"""

from .metrics_service import MetricsService, get_metrics_service, init_metrics_service
from .api_logging_service import (
    APILoggingService,
    get_api_logging_service,
    init_api_logging_service,
    shutdown_api_logging_service
)
from .gnf_adapter import (
    GNFAdapter, 
    GNFConfig, 
    AgentIdentityData, 
    InteractionData, 
    InteractionType, 
    ImpactLevel, 
    EmotionalTone,
    create_gnf_adapter,
    track_conversation_interaction
)

# Epistemic Autonomy Services
from .story_loss_service import (
    StoryLossCalculator,
    ContradictionDetector,
    AsyncGraphProcessor,
    get_story_loss_calculator,
    init_story_loss_service
)
from .gnf_service import (
    GlobalNarrativeFrame,
    AgentGraph,
    GraphNode,
    GraphEdge,
    get_gnf_service,
    init_gnf_service
)
from .umwelt_service import (
    UmweltManager,
    SignalProcessor,
    CoreObjectiveFunction,
    get_umwelt_manager,
    init_umwelt_service
)
from .umwelt_conflict_detector import (
    UmweltConflictDetector,
    ConflictAnalyzer,
    FactExtractor,
    get_umwelt_conflict_detector,
    init_umwelt_conflict_service
)
from .minion_service import (
    MinionCoordinator,
    SelfReflectionMinion,
    BaseMinionAgent,
    get_minion_coordinator,
    init_minion_service
)
from .alert_service import (
    AlertService,
    AlertRule,
    NotificationChannel,
    get_alert_service,
    init_alert_service
)

# Spanner Graph and eA³ Services
from .spanner_graph_service import (
    SpannerGraphService,
    StoryEvent,
    StoryEventType,
    NarrativeThread,
    BeliefRevision,
    NarrativeCoherence,
    get_spanner_graph_service,
    init_spanner_graph_service
)
from .ea3_orchestrator import (
    EA3Orchestrator,
    ConversationContext,
    EA3Assessment,
    get_ea3_orchestrator,
    init_ea3_orchestrator
)

__all__ = [
    # Core Services
    "MetricsService",
    "get_metrics_service", 
    "init_metrics_service",
    "APILoggingService",
    "get_api_logging_service",
    "init_api_logging_service",
    "shutdown_api_logging_service",
    "GNFAdapter",
    "GNFConfig",
    "AgentIdentityData",
    "InteractionData",
    "InteractionType",
    "ImpactLevel",
    "EmotionalTone",
    "create_gnf_adapter",
    "track_conversation_interaction",
    
    # Epistemic Autonomy Services
    "StoryLossCalculator",
    "ContradictionDetector", 
    "AsyncGraphProcessor",
    "get_story_loss_calculator",
    "init_story_loss_service",
    "GlobalNarrativeFrame",
    "AgentGraph",
    "GraphNode",
    "GraphEdge",
    "get_gnf_service",
    "init_gnf_service",
    "UmweltManager",
    "SignalProcessor",
    "CoreObjectiveFunction",
    "get_umwelt_manager",
    "init_umwelt_service",
    "UmweltConflictDetector",
    "ConflictAnalyzer",
    "FactExtractor",
    "get_umwelt_conflict_detector",
    "init_umwelt_conflict_service",
    "MinionCoordinator",
    "SelfReflectionMinion",
    "BaseMinionAgent",
    "get_minion_coordinator",
    "init_minion_service",
    "AlertService",
    "AlertRule",
    "NotificationChannel",
    "get_alert_service",
    "init_alert_service",
    
    # Spanner Graph and eA³ Services
    "SpannerGraphService",
    "StoryEvent",
    "StoryEventType",
    "NarrativeThread",
    "BeliefRevision",
    "NarrativeCoherence",
    "get_spanner_graph_service",
    "init_spanner_graph_service",
    "EA3Orchestrator",
    "ConversationContext",
    "EA3Assessment",
    "get_ea3_orchestrator",
    "init_ea3_orchestrator"
]