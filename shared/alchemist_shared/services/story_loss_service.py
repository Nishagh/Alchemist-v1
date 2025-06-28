"""
Story-Loss Metric Service

Implements story-loss calculation for Global Narrative Frame (GNF) coherence monitoring.
Measures L_story = contradictory_edges / total_edges_added when agents append new nodes.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EdgeType(Enum):
    BELIEF = "belief"
    ACTION = "action"
    CAUSAL = "causal"
    TEMPORAL = "temporal"
    CONTRADICTION = "contradiction"


class NodeType(Enum):
    FACT = "fact"
    GOAL = "goal"
    ACTION = "action"
    BELIEF = "belief"
    EVENT = "event"


@dataclass
class GraphNode:
    """Represents a node in the agent's narrative graph"""
    id: str
    type: NodeType
    content: str
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID based on content and timestamp"""
        content_hash = hashlib.md5(
            f"{self.content}_{self.timestamp.isoformat()}".encode()
        ).hexdigest()[:8]
        return f"{self.type.value}_{content_hash}"


@dataclass
class GraphEdge:
    """Represents an edge in the agent's narrative graph"""
    id: str
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID for edge"""
        edge_hash = hashlib.md5(
            f"{self.source_id}_{self.target_id}_{self.type.value}".encode()
        ).hexdigest()[:8]
        return f"edge_{edge_hash}"


@dataclass
class ContradictionResult:
    """Result of contradiction detection analysis"""
    contradictory_edges: List[GraphEdge]
    total_edges_checked: int
    contradiction_details: List[Dict[str, Any]]
    confidence_score: float


class ContradictionDetector:
    """Detects contradictions and broken causal links in narrative graphs"""
    
    def __init__(self):
        self.contradiction_patterns = self._load_contradiction_patterns()
        self.causal_validators = self._load_causal_validators()
    
    def _load_contradiction_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns that indicate contradictions"""
        return [
            {
                "pattern": "negation",
                "description": "Direct negation of previous belief",
                "weight": 1.0
            },
            {
                "pattern": "temporal_impossibility", 
                "description": "Events that cannot coexist temporally",
                "weight": 0.9
            },
            {
                "pattern": "logical_inconsistency",
                "description": "Logically inconsistent statements",
                "weight": 0.8
            },
            {
                "pattern": "causal_violation",
                "description": "Effect preceding cause",
                "weight": 0.7
            }
        ]
    
    def _load_causal_validators(self) -> List[Dict[str, Any]]:
        """Load validators for causal link coherence"""
        return [
            {
                "validator": "temporal_order",
                "description": "Cause must precede effect",
                "weight": 1.0
            },
            {
                "validator": "causal_proximity",
                "description": "Reasonable temporal distance between cause and effect",
                "weight": 0.6
            },
            {
                "validator": "causal_plausibility",
                "description": "Plausible causal relationship",
                "weight": 0.8
            }
        ]
    
    async def detect_contradictions(
        self,
        new_edges: List[GraphEdge],
        existing_graph: Dict[str, GraphNode],
        existing_edges: List[GraphEdge]
    ) -> ContradictionResult:
        """
        Detect contradictions between new edges and existing graph
        
        Args:
            new_edges: List of edges being added
            existing_graph: Dictionary of existing nodes (id -> node)
            existing_edges: List of existing edges
            
        Returns:
            ContradictionResult with detected contradictions
        """
        contradictory_edges = []
        contradiction_details = []
        
        # Run contradiction detection in parallel for performance
        tasks = []
        
        for new_edge in new_edges:
            task = self._check_edge_contradictions(
                new_edge, existing_graph, existing_edges
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error checking edge {new_edges[i].id}: {result}")
                continue
                
            is_contradictory, details = result
            if is_contradictory:
                contradictory_edges.append(new_edges[i])
                contradiction_details.extend(details)
        
        confidence_score = self._calculate_confidence(contradiction_details)
        
        return ContradictionResult(
            contradictory_edges=contradictory_edges,
            total_edges_checked=len(new_edges),
            contradiction_details=contradiction_details,
            confidence_score=confidence_score
        )
    
    async def _check_edge_contradictions(
        self,
        edge: GraphEdge,
        existing_graph: Dict[str, GraphNode],
        existing_edges: List[GraphEdge]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check if a single edge contradicts existing graph"""
        details = []
        is_contradictory = False
        
        # Check for direct contradictions
        contradictions = await self._find_direct_contradictions(
            edge, existing_graph, existing_edges
        )
        if contradictions:
            is_contradictory = True
            details.extend(contradictions)
        
        # Check for causal violations
        causal_violations = await self._find_causal_violations(
            edge, existing_graph, existing_edges
        )
        if causal_violations:
            is_contradictory = True
            details.extend(causal_violations)
        
        return is_contradictory, details
    
    async def _find_direct_contradictions(
        self,
        edge: GraphEdge,
        existing_graph: Dict[str, GraphNode],
        existing_edges: List[GraphEdge]
    ) -> List[Dict[str, Any]]:
        """Find direct contradictions with existing beliefs/facts"""
        contradictions = []
        
        source_node = existing_graph.get(edge.source_id)
        target_node = existing_graph.get(edge.target_id)
        
        if not source_node or not target_node:
            return contradictions
        
        # Check for negation patterns
        if edge.type == EdgeType.BELIEF:
            negation_conflicts = await self._check_negation_patterns(
                source_node, target_node, existing_edges
            )
            contradictions.extend(negation_conflicts)
        
        # Check for temporal impossibilities
        if edge.type == EdgeType.TEMPORAL:
            temporal_conflicts = await self._check_temporal_consistency(
                source_node, target_node, existing_edges
            )
            contradictions.extend(temporal_conflicts)
        
        return contradictions
    
    async def _find_causal_violations(
        self,
        edge: GraphEdge,
        existing_graph: Dict[str, GraphNode],
        existing_edges: List[GraphEdge]
    ) -> List[Dict[str, Any]]:
        """Find violations of causal coherence"""
        violations = []
        
        if edge.type != EdgeType.CAUSAL:
            return violations
        
        source_node = existing_graph.get(edge.source_id)
        target_node = existing_graph.get(edge.target_id)
        
        if not source_node or not target_node:
            return violations
        
        # Check temporal order (cause before effect)
        if source_node.timestamp > target_node.timestamp:
            violations.append({
                "type": "temporal_order_violation",
                "description": f"Effect {target_node.id} precedes cause {source_node.id}",
                "severity": 1.0,
                "edge_id": edge.id
            })
        
        return violations
    
    async def _check_negation_patterns(
        self,
        source_node: GraphNode,
        target_node: GraphNode,
        existing_edges: List[GraphEdge]
    ) -> List[Dict[str, Any]]:
        """Check for negation contradictions"""
        patterns = []
        
        # Simple negation detection (can be enhanced with NLP)
        negation_words = ["not", "never", "no", "false", "deny", "reject"]
        
        source_content = source_node.content.lower()
        target_content = target_node.content.lower()
        
        # Check if one statement negates the other
        for word in negation_words:
            if word in source_content and any(
                term in target_content for term in source_content.split()
                if term != word and len(term) > 3
            ):
                patterns.append({
                    "type": "negation_contradiction",
                    "description": f"Statement negation between {source_node.id} and {target_node.id}",
                    "severity": 0.8,
                    "source_content": source_node.content,
                    "target_content": target_node.content
                })
        
        return patterns
    
    async def _check_temporal_consistency(
        self,
        source_node: GraphNode,
        target_node: GraphNode,
        existing_edges: List[GraphEdge]
    ) -> List[Dict[str, Any]]:
        """Check for temporal consistency violations"""
        violations = []
        
        # Check for temporal paradoxes
        time_diff = abs((source_node.timestamp - target_node.timestamp).total_seconds())
        
        # If events are claimed to be simultaneous but have significant time gap
        if time_diff > 3600:  # 1 hour threshold
            violations.append({
                "type": "temporal_inconsistency",
                "description": f"Large temporal gap in simultaneous events",
                "severity": 0.6,
                "time_difference_seconds": time_diff
            })
        
        return violations
    
    def _calculate_confidence(self, contradiction_details: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in contradiction detection"""
        if not contradiction_details:
            return 1.0
        
        total_severity = sum(detail.get("severity", 0.5) for detail in contradiction_details)
        max_possible = len(contradiction_details) * 1.0
        
        return min(total_severity / max_possible, 1.0) if max_possible > 0 else 0.5


class AsyncGraphProcessor:
    """Handles async processing to minimize latency impact"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue = asyncio.Queue()
        self.is_running = False
    
    async def start(self):
        """Start the background processor"""
        self.is_running = True
        asyncio.create_task(self._process_queue())
    
    async def stop(self):
        """Stop the background processor"""
        self.is_running = False
    
    async def _process_queue(self):
        """Background queue processor"""
        while self.is_running:
            try:
                task = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )
                await task
                self.processing_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in graph processor: {e}")
    
    async def submit_analysis(self, analysis_coro):
        """Submit analysis for background processing"""
        await self.processing_queue.put(analysis_coro)


class StoryLossCalculator:
    """Main service for calculating story-loss metrics"""
    
    def __init__(self):
        self.contradiction_detector = ContradictionDetector()
        self.graph_processor = AsyncGraphProcessor()
        self.metrics_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def initialize(self):
        """Initialize the service"""
        await self.graph_processor.start()
        logger.info("StoryLossCalculator initialized")
    
    async def shutdown(self):
        """Shutdown the service"""
        await self.graph_processor.stop()
        logger.info("StoryLossCalculator shutdown")
    
    async def calculate_story_loss(
        self,
        agent_id: str,
        new_edges: List[GraphEdge],
        existing_graph: Dict[str, GraphNode],
        existing_edges: List[GraphEdge]
    ) -> float:
        """
        Calculate L_story = contradictory_edges / total_edges_added
        
        Args:
            agent_id: ID of the agent
            new_edges: List of edges being added
            existing_graph: Current graph state
            existing_edges: Existing edges in graph
            
        Returns:
            Normalized story-loss score between 0 and 1
        """
        if not new_edges:
            return 0.0
        
        try:
            # Perform contradiction detection
            contradiction_result = await self.contradiction_detector.detect_contradictions(
                new_edges, existing_graph, existing_edges
            )
            
            # Calculate normalized score
            contradictory_count = len(contradiction_result.contradictory_edges)
            total_edges = len(new_edges)
            
            story_loss = contradictory_count / total_edges if total_edges > 0 else 0.0
            
            # Apply confidence weighting
            weighted_story_loss = story_loss * contradiction_result.confidence_score
            
            # Cache result
            self._cache_result(agent_id, weighted_story_loss, contradiction_result)
            
            logger.info(
                f"Story-loss calculated for agent {agent_id}: {weighted_story_loss:.3f} "
                f"({contradictory_count}/{total_edges} edges)"
            )
            
            return min(weighted_story_loss, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating story-loss for agent {agent_id}: {e}")
            return 0.0
    
    def _cache_result(
        self,
        agent_id: str,
        story_loss: float,
        contradiction_result: ContradictionResult
    ):
        """Cache calculation result"""
        self.metrics_cache[agent_id] = {
            "story_loss": story_loss,
            "timestamp": datetime.now(),
            "contradiction_details": contradiction_result.contradiction_details,
            "confidence": contradiction_result.confidence_score
        }
    
    def get_cached_result(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get cached story-loss result if still valid"""
        if agent_id not in self.metrics_cache:
            return None
        
        cached = self.metrics_cache[agent_id]
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        
        if age > self.cache_ttl:
            del self.metrics_cache[agent_id]
            return None
        
        return cached
    
    def normalize_score(self, contradictory_edges: int, total_edges: int) -> float:
        """Normalize story-loss score to [0,1] range"""
        if total_edges == 0:
            return 0.0
        return min(contradictory_edges / total_edges, 1.0)


# Global instance
story_loss_calculator = StoryLossCalculator()


async def get_story_loss_calculator() -> StoryLossCalculator:
    """Get the global story-loss calculator instance"""
    return story_loss_calculator


async def init_story_loss_service() -> StoryLossCalculator:
    """Initialize and return the global story-loss calculator instance"""
    await story_loss_calculator.initialize()
    return story_loss_calculator