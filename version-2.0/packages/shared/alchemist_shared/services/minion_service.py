"""
Minion Service

Implements autonomous agents (minions) that perform specialized tasks like
self-reflection when triggered by story-loss thresholds or other events.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from firebase_admin import firestore

logger = logging.getLogger(__name__)


class MinionType(Enum):
    SELF_REFLECTION = "self_reflection"
    NARRATIVE_REPAIR = "narrative_repair"
    KNOWLEDGE_VALIDATION = "knowledge_validation"
    GOAL_ALIGNMENT = "goal_alignment"
    CONFLICT_RESOLUTION = "conflict_resolution"


class MinionStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    THINKING = "thinking"
    ACTING = "acting"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class MinionTask:
    """Represents a task assigned to a minion"""
    id: str
    agent_id: str
    minion_type: MinionType
    trigger_event: str
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    max_retries: int = 1
    current_retry: int = 0
    status: MinionStatus = MinionStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class MinionCapability:
    """Defines what a minion can do"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    execution_function: Callable
    timeout_seconds: int = 300  # 5 minutes default


class BaseMinionAgent:
    """Base class for minion agents"""
    
    def __init__(self, minion_type: MinionType, agent_id: str):
        self.minion_type = minion_type
        self.agent_id = agent_id
        self.capabilities: List[MinionCapability] = []
        self.db = None  # Will be initialized lazily
        self.current_task: Optional[MinionTask] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the minion agent"""
        if self._initialized:
            return
        self.db = firestore.client()
        self._initialized = True
        
    async def execute_task(self, task: MinionTask) -> Dict[str, Any]:
        """Execute a task and return results"""
        raise NotImplementedError("Subclasses must implement execute_task")
    
    async def can_handle_task(self, task: MinionTask) -> bool:
        """Check if this minion can handle the given task"""
        return task.minion_type == self.minion_type and task.agent_id == self.agent_id
    
    async def log_activity(self, activity: str, metadata: Optional[Dict[str, Any]] = None):
        """Log minion activity"""
        try:
            log_ref = self.db.collection('minion_logs').document()
            log_data = {
                'minion_type': self.minion_type.value,
                'agent_id': self.agent_id,
                'activity': activity,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None, log_ref.set, log_data
            )
            
        except Exception as e:
            logger.error(f"Failed to log minion activity: {e}")


class SelfReflectionMinion(BaseMinionAgent):
    """Specialized minion for narrative self-reflection and coherence repair"""
    
    def __init__(self, agent_id: str):
        super().__init__(MinionType.SELF_REFLECTION, agent_id)
        self.story_loss_threshold = 0.15
    
    async def execute_task(self, task: MinionTask) -> Dict[str, Any]:
        """
        Execute self-reflection task when story-loss threshold is exceeded
        
        Args:
            task: MinionTask containing trigger data and context
            
        Returns:
            Dictionary with reflection results and actions taken
        """
        try:
            self.current_task = task
            await self.log_activity("Starting self-reflection", {
                "trigger_event": task.trigger_event,
                "story_loss": task.trigger_data.get("story_loss", 0.0)
            })
            
            # Get current story-loss and context
            story_loss = task.trigger_data.get("story_loss", 0.0)
            
            if story_loss <= self.story_loss_threshold:
                return {
                    "success": True,
                    "action": "no_action_needed",
                    "reason": f"Story-loss {story_loss:.3f} is below threshold {self.story_loss_threshold}",
                    "story_loss_before": story_loss,
                    "story_loss_after": story_loss
                }
            
            # Perform narrative analysis
            analysis_result = await self._analyze_narrative_inconsistencies(task)
            
            # Attempt narrative repair
            repair_result = await self._attempt_narrative_repair(task, analysis_result)
            
            # Verify improvement
            verification_result = await self._verify_narrative_improvement(task)
            
            result = {
                "success": verification_result.get("improved", False),
                "action": "self_reflection_completed",
                "analysis": analysis_result,
                "repair": repair_result,
                "verification": verification_result,
                "story_loss_before": story_loss,
                "story_loss_after": verification_result.get("new_story_loss", story_loss),
                "improvements_made": verification_result.get("improvements", []),
                "retry_recommended": verification_result.get("new_story_loss", story_loss) > self.story_loss_threshold
            }
            
            await self.log_activity("Self-reflection completed", result)
            return result
            
        except Exception as e:
            error_msg = f"Self-reflection failed: {e}"
            logger.error(error_msg)
            await self.log_activity("Self-reflection failed", {"error": str(e)})
            
            return {
                "success": False,
                "action": "self_reflection_failed",
                "error": error_msg,
                "retry_recommended": True
            }
    
    async def _analyze_narrative_inconsistencies(self, task: MinionTask) -> Dict[str, Any]:
        """Analyze the agent's narrative for inconsistencies"""
        try:
            # Get GNF service and agent graph
            from .gnf_service import get_gnf_service
            gnf_service = await get_gnf_service()
            agent_graph = await gnf_service.get_agent_graph(task.agent_id)
            
            if not agent_graph:
                return {"error": "No agent graph available for analysis"}
            
            # Analyze contradictions in recent additions
            analysis = {
                "total_nodes": len(agent_graph.nodes),
                "total_edges": len(agent_graph.edges),
                "recent_additions": [],
                "contradiction_patterns": [],
                "temporal_inconsistencies": [],
                "logical_conflicts": []
            }
            
            # Find recent nodes and edges (last hour)
            recent_threshold = datetime.now() - timedelta(hours=1)
            
            recent_nodes = [
                node for node in agent_graph.nodes.values()
                if node.timestamp >= recent_threshold
            ]
            
            recent_edges = [
                edge for edge in agent_graph.edges
                if edge.timestamp >= recent_threshold
            ]
            
            analysis["recent_additions"] = [
                {
                    "type": "node",
                    "id": node.id,
                    "content": node.content,
                    "node_type": node.type.value,
                    "confidence": node.confidence
                }
                for node in recent_nodes
            ] + [
                {
                    "type": "edge", 
                    "id": edge.id,
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "edge_type": edge.type.value,
                    "confidence": edge.confidence
                }
                for edge in recent_edges
            ]
            
            # Identify patterns that commonly cause contradictions
            analysis["contradiction_patterns"] = await self._identify_contradiction_patterns(
                recent_nodes, recent_edges, agent_graph
            )
            
            # Look for temporal inconsistencies
            analysis["temporal_inconsistencies"] = await self._find_temporal_inconsistencies(
                recent_nodes, agent_graph
            )
            
            # Identify logical conflicts
            analysis["logical_conflicts"] = await self._find_logical_conflicts(
                recent_nodes, agent_graph
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing narrative inconsistencies: {e}")
            return {"error": str(e)}
    
    async def _identify_contradiction_patterns(
        self,
        recent_nodes: List,
        recent_edges: List,
        agent_graph
    ) -> List[Dict[str, Any]]:
        """Identify common patterns that lead to contradictions"""
        patterns = []
        
        try:
            # Pattern 1: Negation conflicts
            for node in recent_nodes:
                content = node.content.lower()
                negation_words = ["not", "never", "no", "false", "deny", "reject", "impossible"]
                
                if any(word in content for word in negation_words):
                    # Check if there are existing nodes that contradict this
                    for existing_node in agent_graph.nodes.values():
                        if existing_node.id != node.id:
                            existing_content = existing_node.content.lower()
                            
                            # Simple contradiction detection
                            shared_words = set(content.split()) & set(existing_content.split())
                            if len(shared_words) > 2:  # Significant overlap
                                has_negation = any(word in content for word in negation_words)
                                existing_has_negation = any(word in existing_content for word in negation_words)
                                
                                if has_negation != existing_has_negation:
                                    patterns.append({
                                        "type": "negation_conflict",
                                        "nodes": [node.id, existing_node.id],
                                        "description": f"Potential negation conflict between '{node.content}' and '{existing_node.content}'",
                                        "confidence": 0.7
                                    })
            
            # Pattern 2: Temporal impossibilities
            temporal_keywords = ["yesterday", "today", "tomorrow", "before", "after", "during", "while"]
            temporal_nodes = [
                node for node in recent_nodes
                if any(keyword in node.content.lower() for keyword in temporal_keywords)
            ]
            
            for i, node1 in enumerate(temporal_nodes):
                for node2 in temporal_nodes[i+1:]:
                    # Check for temporal conflicts
                    content1 = node1.content.lower()
                    content2 = node2.content.lower()
                    
                    conflicts = [
                        ("yesterday", "today"),
                        ("today", "tomorrow"),
                        ("before", "after")
                    ]
                    
                    for term1, term2 in conflicts:
                        if (term1 in content1 and term2 in content2) or (term2 in content1 and term1 in content2):
                            patterns.append({
                                "type": "temporal_conflict",
                                "nodes": [node1.id, node2.id],
                                "description": f"Temporal conflict: '{node1.content}' vs '{node2.content}'",
                                "confidence": 0.8
                            })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying contradiction patterns: {e}")
            return []
    
    async def _find_temporal_inconsistencies(self, recent_nodes: List, agent_graph) -> List[Dict[str, Any]]:
        """Find temporal inconsistencies in the narrative"""
        inconsistencies = []
        
        try:
            # Group nodes by timestamp
            nodes_by_hour = {}
            for node in agent_graph.nodes.values():
                hour_key = node.timestamp.strftime('%Y-%m-%d %H:00')
                if hour_key not in nodes_by_hour:
                    nodes_by_hour[hour_key] = []
                nodes_by_hour[hour_key].append(node)
            
            # Check for impossible temporal sequences within the same time period
            for hour_key, nodes in nodes_by_hour.items():
                if len(nodes) > 1:
                    for i, node1 in enumerate(nodes):
                        for node2 in nodes[i+1:]:
                            # Check if nodes describe conflicting temporal states
                            if self._nodes_have_temporal_conflict(node1, node2):
                                inconsistencies.append({
                                    "type": "temporal_sequence_conflict",
                                    "nodes": [node1.id, node2.id],
                                    "time_period": hour_key,
                                    "description": f"Conflicting temporal states in same period: '{node1.content}' and '{node2.content}'",
                                    "confidence": 0.6
                                })
            
            return inconsistencies
            
        except Exception as e:
            logger.error(f"Error finding temporal inconsistencies: {e}")
            return []
    
    async def _find_logical_conflicts(self, recent_nodes: List, agent_graph) -> List[Dict[str, Any]]:
        """Find logical conflicts in the narrative"""
        conflicts = []
        
        try:
            # Simple logical conflict detection
            logical_operators = ["and", "or", "if", "then", "because", "therefore", "but", "however"]
            
            for node in recent_nodes:
                content = node.content.lower()
                
                # Check for explicit contradictions
                if "but" in content or "however" in content:
                    # This node might contain internal contradiction
                    conflicts.append({
                        "type": "internal_contradiction",
                        "nodes": [node.id],
                        "description": f"Potential internal contradiction: '{node.content}'",
                        "confidence": 0.5
                    })
                
                # Check for impossible logical combinations
                if "always" in content and "never" in content:
                    conflicts.append({
                        "type": "logical_impossibility",
                        "nodes": [node.id],
                        "description": f"Logical impossibility (always + never): '{node.content}'",
                        "confidence": 0.9
                    })
                
                if "all" in content and "none" in content:
                    conflicts.append({
                        "type": "logical_impossibility",
                        "nodes": [node.id],
                        "description": f"Logical impossibility (all + none): '{node.content}'",
                        "confidence": 0.9
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error finding logical conflicts: {e}")
            return []
    
    def _nodes_have_temporal_conflict(self, node1, node2) -> bool:
        """Check if two nodes have temporal conflicts"""
        content1 = node1.content.lower()
        content2 = node2.content.lower()
        
        # Simple temporal conflict patterns
        conflicts = [
            ("started", "finished"),
            ("began", "ended"),
            ("opening", "closing"),
            ("arriving", "leaving")
        ]
        
        for start_word, end_word in conflicts:
            if (start_word in content1 and end_word in content2) or (end_word in content1 and start_word in content2):
                # Check if they're describing the same entity
                words1 = set(content1.split())
                words2 = set(content2.split())
                common_words = words1 & words2
                
                if len(common_words) > 1:  # Share significant vocabulary
                    return True
        
        return False
    
    async def _attempt_narrative_repair(self, task: MinionTask, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to repair narrative inconsistencies"""
        try:
            repair_actions = []
            
            # Get GNF service
            from .gnf_service import get_gnf_service
            gnf_service = await get_gnf_service()
            
            # Process contradiction patterns
            for pattern in analysis.get("contradiction_patterns", []):
                if pattern["confidence"] > 0.6:
                    action = await self._resolve_contradiction_pattern(pattern, gnf_service, task.agent_id)
                    if action:
                        repair_actions.append(action)
            
            # Process temporal inconsistencies
            for inconsistency in analysis.get("temporal_inconsistencies", []):
                if inconsistency["confidence"] > 0.5:
                    action = await self._resolve_temporal_inconsistency(inconsistency, gnf_service, task.agent_id)
                    if action:
                        repair_actions.append(action)
            
            # Process logical conflicts
            for conflict in analysis.get("logical_conflicts", []):
                if conflict["confidence"] > 0.7:
                    action = await self._resolve_logical_conflict(conflict, gnf_service, task.agent_id)
                    if action:
                        repair_actions.append(action)
            
            return {
                "actions_taken": repair_actions,
                "total_repairs": len(repair_actions),
                "repair_types": list(set(action["type"] for action in repair_actions))
            }
            
        except Exception as e:
            logger.error(f"Error attempting narrative repair: {e}")
            return {"error": str(e), "actions_taken": []}
    
    async def _resolve_contradiction_pattern(
        self,
        pattern: Dict[str, Any],
        gnf_service,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Resolve a contradiction pattern"""
        try:
            if pattern["type"] == "negation_conflict":
                # Add clarifying belief edge to resolve the conflict
                await gnf_service.add_belief_edge(
                    agent_id,
                    f"Clarification needed for conflicting beliefs: {pattern['description']}",
                    "Need to verify which belief is correct through evidence",
                    confidence=0.8,
                    metadata={"repair_action": "contradiction_clarification", "pattern_id": pattern.get("nodes", [])}
                )
                
                return {
                    "type": "contradiction_clarification",
                    "description": "Added clarifying belief edge for negation conflict",
                    "nodes_involved": pattern.get("nodes", [])
                }
        
        except Exception as e:
            logger.error(f"Error resolving contradiction pattern: {e}")
        
        return None
    
    async def _resolve_temporal_inconsistency(
        self,
        inconsistency: Dict[str, Any],
        gnf_service,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Resolve a temporal inconsistency"""
        try:
            # Add temporal ordering belief
            await gnf_service.add_belief_edge(
                agent_id,
                "Temporal sequence requires clarification",
                f"Events need proper temporal ordering: {inconsistency['description']}",
                confidence=0.7,
                metadata={"repair_action": "temporal_clarification", "inconsistency_id": inconsistency.get("nodes", [])}
            )
            
            return {
                "type": "temporal_clarification",
                "description": "Added temporal ordering clarification",
                "nodes_involved": inconsistency.get("nodes", [])
            }
        
        except Exception as e:
            logger.error(f"Error resolving temporal inconsistency: {e}")
        
        return None
    
    async def _resolve_logical_conflict(
        self,
        conflict: Dict[str, Any],
        gnf_service,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Resolve a logical conflict"""
        try:
            # Add logical clarification belief
            await gnf_service.add_belief_edge(
                agent_id,
                "Logical consistency check needed",
                f"Statement requires logical review: {conflict['description']}",
                confidence=0.8,
                metadata={"repair_action": "logical_clarification", "conflict_id": conflict.get("nodes", [])}
            )
            
            return {
                "type": "logical_clarification", 
                "description": "Added logical consistency check",
                "nodes_involved": conflict.get("nodes", [])
            }
        
        except Exception as e:
            logger.error(f"Error resolving logical conflict: {e}")
        
        return None
    
    async def _verify_narrative_improvement(self, task: MinionTask) -> Dict[str, Any]:
        """Verify if narrative coherence has improved"""
        try:
            # Get current story-loss after repairs
            from .story_loss_service import get_story_loss_calculator
            calculator = await get_story_loss_calculator()
            
            # Get updated agent graph
            from .gnf_service import get_gnf_service
            gnf_service = await get_gnf_service()
            agent_graph = await gnf_service.get_agent_graph(task.agent_id)
            
            if not agent_graph:
                return {"error": "No agent graph available for verification"}
            
            # Calculate current story-loss
            # For verification, we simulate adding a neutral edge to check overall coherence
            from .story_loss_service import GraphEdge, EdgeType, GraphNode, NodeType
            
            test_node = GraphNode(
                id="verification_test",
                type=NodeType.BELIEF,
                content="Verification test",
                timestamp=datetime.now()
            )
            
            test_edge = GraphEdge(
                id="verification_edge",
                source_id=list(agent_graph.nodes.keys())[0] if agent_graph.nodes else "test",
                target_id="verification_test",
                type=EdgeType.BELIEF
            )
            
            new_story_loss = await calculator.calculate_story_loss(
                task.agent_id,
                [test_edge],
                agent_graph.nodes,
                agent_graph.edges
            )
            
            original_story_loss = task.trigger_data.get("story_loss", 0.0)
            improvement = original_story_loss - new_story_loss
            
            verification_result = {
                "new_story_loss": new_story_loss,
                "original_story_loss": original_story_loss,
                "improvement": improvement,
                "improved": improvement > 0.01,  # At least 1% improvement
                "still_above_threshold": new_story_loss > self.story_loss_threshold,
                "improvements": []
            }
            
            if improvement > 0.01:
                verification_result["improvements"].append("Narrative coherence improved")
            
            if new_story_loss <= self.story_loss_threshold:
                verification_result["improvements"].append("Story-loss below threshold")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying narrative improvement: {e}")
            return {"error": str(e), "improved": False}


class MinionCoordinator:
    """Coordinates and manages minion agents"""
    
    def __init__(self):
        self.active_minions: Dict[str, BaseMinionAgent] = {}
        self.task_queue: List[MinionTask] = []
        self.db = None  # Will be initialized lazily
        self._processing = False
        self._background_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the minion coordinator"""
        if self._initialized:
            return
        self.db = firestore.client()
        self._processing = True
        self._initialized = True
        self._background_task = asyncio.create_task(self._process_tasks())
        logger.info("MinionCoordinator initialized")
    
    async def shutdown(self):
        """Shutdown the minion coordinator"""
        self._processing = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        logger.info("MinionCoordinator shutdown")
    
    async def trigger_self_reflection(
        self,
        agent_id: str,
        story_loss: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Trigger self-reflection minion for story-loss threshold exceedance
        
        Args:
            agent_id: ID of the agent
            story_loss: Current story-loss value
            metadata: Additional context data
            
        Returns:
            Task ID of the created self-reflection task
        """
        try:
            task = MinionTask(
                id="",  # Will be auto-generated
                agent_id=agent_id,
                minion_type=MinionType.SELF_REFLECTION,
                trigger_event="story_loss_threshold_exceeded",
                trigger_data={
                    "story_loss": story_loss,
                    "threshold": 0.15,
                    "metadata": metadata or {}
                },
                priority=2 if story_loss > 0.3 else 1  # Higher priority for very high story-loss
            )
            
            self.task_queue.append(task)
            
            # Store task in Firebase
            await self._persist_task(task)
            
            logger.info(f"Self-reflection task created for agent {agent_id}: {task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to trigger self-reflection for agent {agent_id}: {e}")
            return ""
    
    async def _persist_task(self, task: MinionTask):
        """Persist task to Firebase"""
        try:
            doc_ref = self.db.collection('minion_tasks').document(task.id)
            task_data = {
                'id': task.id,
                'agent_id': task.agent_id,
                'minion_type': task.minion_type.value,
                'trigger_event': task.trigger_event,
                'trigger_data': task.trigger_data,
                'priority': task.priority,
                'max_retries': task.max_retries,
                'current_retry': task.current_retry,
                'status': task.status.value,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'result': task.result,
                'error_message': task.error_message
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.set, task_data
            )
            
        except Exception as e:
            logger.error(f"Failed to persist task {task.id}: {e}")
    
    async def _process_tasks(self):
        """Background task processor"""
        while self._processing:
            try:
                if self.task_queue:
                    # Sort by priority (higher priority first)
                    self.task_queue.sort(key=lambda t: t.priority, reverse=True)
                    
                    # Process highest priority task
                    task = self.task_queue.pop(0)
                    await self._execute_task(task)
                
                # Wait before checking for more tasks
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(5)
    
    async def _execute_task(self, task: MinionTask):
        """Execute a minion task"""
        try:
            task.status = MinionStatus.ACTIVE
            task.started_at = datetime.now()
            await self._persist_task(task)
            
            # Create appropriate minion for the task
            minion = await self._create_minion(task)
            if not minion:
                task.status = MinionStatus.FAILED
                task.error_message = "Failed to create appropriate minion"
                await self._persist_task(task)
                return
            
            # Execute the task
            result = await minion.execute_task(task)
            
            # Update task with results
            task.result = result
            task.completed_at = datetime.now()
            
            if result.get("success", False):
                task.status = MinionStatus.COMPLETED
            else:
                if task.current_retry < task.max_retries and result.get("retry_recommended", False):
                    task.current_retry += 1
                    task.status = MinionStatus.RETRYING
                    # Re-queue for retry
                    self.task_queue.append(task)
                else:
                    task.status = MinionStatus.FAILED
                    task.error_message = result.get("error", "Task failed")
            
            await self._persist_task(task)
            
            logger.info(f"Task {task.id} completed with status: {task.status.value}")
            
        except Exception as e:
            task.status = MinionStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            await self._persist_task(task)
            logger.error(f"Error executing task {task.id}: {e}")
    
    async def _create_minion(self, task: MinionTask) -> Optional[BaseMinionAgent]:
        """Create appropriate minion for the task"""
        try:
            if task.minion_type == MinionType.SELF_REFLECTION:
                return SelfReflectionMinion(task.agent_id)
            
            # Add other minion types here as needed
            
            logger.warning(f"No minion implementation for type: {task.minion_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error creating minion for task {task.id}: {e}")
            return None


# Global instance
_minion_coordinator: Optional[MinionCoordinator] = None


async def get_minion_coordinator() -> MinionCoordinator:
    """Get the global minion coordinator instance"""
    global _minion_coordinator
    if _minion_coordinator is None:
        _minion_coordinator = MinionCoordinator()
    if not _minion_coordinator._initialized:
        await _minion_coordinator.initialize()
    return _minion_coordinator


async def init_minion_service() -> MinionCoordinator:
    """Initialize and return the global minion coordinator instance"""
    return await get_minion_coordinator()