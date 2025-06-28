"""
Global Narrative Frame (GNF) Service

Manages agent belief graphs and integrates with story-loss calculation.
Provides the main interface for adding belief/action edges and triggering
narrative coherence analysis.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import json
from collections import defaultdict

from firebase_admin import firestore
from .story_loss_service import (
    StoryLossCalculator, GraphNode, GraphEdge, EdgeType, NodeType,
    get_story_loss_calculator
)

logger = logging.getLogger(__name__)


@dataclass
class AgentGraph:
    """Represents an agent's complete narrative graph"""
    agent_id: str
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def add_node(self, node: GraphNode) -> bool:
        """Add a node to the graph"""
        if node.id in self.nodes:
            logger.warning(f"Node {node.id} already exists in graph")
            return False
        
        self.nodes[node.id] = node
        self.last_updated = datetime.now()
        self.version += 1
        return True
    
    def add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge to the graph"""
        # Validate that source and target nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            logger.error(f"Cannot add edge {edge.id}: missing nodes")
            return False
        
        # Check for duplicate edges
        for existing_edge in self.edges:
            if (existing_edge.source_id == edge.source_id and 
                existing_edge.target_id == edge.target_id and
                existing_edge.type == edge.type):
                logger.warning(f"Duplicate edge detected: {edge.id}")
                return False
        
        self.edges.append(edge)
        self.last_updated = datetime.now()
        self.version += 1
        return True
    
    def get_node_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges connected to a specific node"""
        return [
            edge for edge in self.edges
            if edge.source_id == node_id or edge.target_id == node_id
        ]
    
    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all outgoing edges from a node"""
        return [edge for edge in self.edges if edge.source_id == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all incoming edges to a node"""
        return [edge for edge in self.edges if edge.target_id == node_id]


class MetricsCallback:
    """Callback interface for metrics reporting"""
    
    async def on_story_loss_calculated(
        self,
        agent_id: str,
        story_loss: float,
        metadata: Dict[str, Any]
    ):
        """Called when story-loss is calculated"""
        pass
    
    async def on_threshold_exceeded(
        self,
        agent_id: str,
        story_loss: float,
        threshold: float
    ):
        """Called when story-loss exceeds threshold"""
        pass


class FirebaseMetricsCallback(MetricsCallback):
    """Firebase implementation of metrics callback"""
    
    def __init__(self):
        self.db = None  # Will be initialized when used
    
    async def on_story_loss_calculated(
        self,
        agent_id: str,
        story_loss: float,
        metadata: Dict[str, Any]
    ):
        """Store story-loss metrics in Firebase"""
        try:
            if self.db is None:
                self.db = firestore.client()
            
            doc_ref = self.db.collection('agent_metrics').document(agent_id)
            
            metrics_data = {
                'story_loss': story_loss,
                'timestamp': datetime.now(),
                'metadata': metadata,
                'version': 1
            }
            
            # Update the agent's latest metrics
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.set, metrics_data, True
            )
            
            # Also store in time-series collection for 24h tracking
            time_series_ref = (
                self.db.collection('agent_metrics')
                .document(agent_id)
                .collection('time_series')
                .document(datetime.now().strftime('%Y%m%d_%H%M%S'))
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None, time_series_ref.set, metrics_data
            )
            
            logger.info(f"Story-loss metrics stored for agent {agent_id}: {story_loss:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to store metrics for agent {agent_id}: {e}")
    
    async def on_threshold_exceeded(
        self,
        agent_id: str,
        story_loss: float,
        threshold: float
    ):
        """Store threshold exceedance event"""
        try:
            event_ref = self.db.collection('agent_events').document()
            
            event_data = {
                'agent_id': agent_id,
                'event_type': 'story_loss_threshold_exceeded',
                'story_loss': story_loss,
                'threshold': threshold,
                'timestamp': datetime.now(),
                'requires_attention': True
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None, event_ref.set, event_data
            )
            
            logger.warning(
                f"Story-loss threshold exceeded for agent {agent_id}: "
                f"{story_loss:.3f} > {threshold}"
            )
            
        except Exception as e:
            logger.error(f"Failed to store threshold event for agent {agent_id}: {e}")


class GlobalNarrativeFrame:
    """Main GNF service managing agent narrative graphs"""
    
    def __init__(self):
        self.agent_graphs: Dict[str, AgentGraph] = {}
        self.story_loss_calculator: Optional[StoryLossCalculator] = None
        self.metrics_callbacks: List[MetricsCallback] = []
        self.story_loss_threshold = 0.15
        self.db = None  # Will be initialized lazily
        self._initialized = False
    
    async def initialize(self):
        """Initialize the GNF service"""
        if self._initialized:
            return
        
        # Initialize Firestore client
        self.db = firestore.client()
        
        self.story_loss_calculator = await get_story_loss_calculator()
        await self.story_loss_calculator.initialize()
        
        # Add default Firebase metrics callback
        self.add_metrics_callback(FirebaseMetricsCallback())
        
        self._initialized = True
        logger.info("GlobalNarrativeFrame initialized")
    
    async def shutdown(self):
        """Shutdown the GNF service"""
        if self.story_loss_calculator:
            await self.story_loss_calculator.shutdown()
        
        self._initialized = False
        logger.info("GlobalNarrativeFrame shutdown")
    
    def add_metrics_callback(self, callback: MetricsCallback):
        """Add a metrics callback"""
        self.metrics_callbacks.append(callback)
    
    async def get_or_create_agent_graph(self, agent_id: str) -> AgentGraph:
        """Get existing agent graph or create a new one"""
        if agent_id not in self.agent_graphs:
            # Try to load from Firebase first
            graph = await self._load_agent_graph(agent_id)
            if graph is None:
                graph = AgentGraph(agent_id=agent_id)
                logger.info(f"Created new graph for agent {agent_id}")
            else:
                logger.info(f"Loaded existing graph for agent {agent_id}")
            
            self.agent_graphs[agent_id] = graph
        
        return self.agent_graphs[agent_id]
    
    async def _load_agent_graph(self, agent_id: str) -> Optional[AgentGraph]:
        """Load agent graph from Firebase"""
        try:
            doc_ref = self.db.collection('agent_graphs').document(agent_id)
            doc = await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.get
            )
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Reconstruct nodes
            nodes = {}
            for node_data in data.get('nodes', []):
                node = GraphNode(
                    id=node_data['id'],
                    type=NodeType(node_data['type']),
                    content=node_data['content'],
                    timestamp=node_data['timestamp'],
                    confidence=node_data.get('confidence', 1.0),
                    metadata=node_data.get('metadata', {})
                )
                nodes[node.id] = node
            
            # Reconstruct edges
            edges = []
            for edge_data in data.get('edges', []):
                edge = GraphEdge(
                    id=edge_data['id'],
                    source_id=edge_data['source_id'],
                    target_id=edge_data['target_id'],
                    type=EdgeType(edge_data['type']),
                    weight=edge_data.get('weight', 1.0),
                    confidence=edge_data.get('confidence', 1.0),
                    timestamp=edge_data['timestamp'],
                    metadata=edge_data.get('metadata', {})
                )
                edges.append(edge)
            
            graph = AgentGraph(
                agent_id=agent_id,
                nodes=nodes,
                edges=edges,
                last_updated=data.get('last_updated', datetime.now()),
                version=data.get('version', 1)
            )
            
            return graph
            
        except Exception as e:
            logger.error(f"Failed to load graph for agent {agent_id}: {e}")
            return None
    
    async def _save_agent_graph(self, graph: AgentGraph):
        """Save agent graph to Firebase"""
        try:
            doc_ref = self.db.collection('agent_graphs').document(graph.agent_id)
            
            # Serialize nodes
            nodes_data = []
            for node in graph.nodes.values():
                nodes_data.append({
                    'id': node.id,
                    'type': node.type.value,
                    'content': node.content,
                    'timestamp': node.timestamp,
                    'confidence': node.confidence,
                    'metadata': node.metadata
                })
            
            # Serialize edges
            edges_data = []
            for edge in graph.edges:
                edges_data.append({
                    'id': edge.id,
                    'source_id': edge.source_id,
                    'target_id': edge.target_id,
                    'type': edge.type.value,
                    'weight': edge.weight,
                    'confidence': edge.confidence,
                    'timestamp': edge.timestamp,
                    'metadata': edge.metadata
                })
            
            graph_data = {
                'agent_id': graph.agent_id,
                'nodes': nodes_data,
                'edges': edges_data,
                'last_updated': graph.last_updated,
                'version': graph.version
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.set, graph_data
            )
            
            logger.debug(f"Saved graph for agent {graph.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to save graph for agent {graph.agent_id}: {e}")
    
    async def add_belief_edge(
        self,
        agent_id: str,
        source_content: str,
        target_content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a belief edge to the agent's graph and calculate story-loss
        
        Args:
            agent_id: ID of the agent
            source_content: Content of the source belief
            target_content: Content of the target belief
            confidence: Confidence in the belief connection
            metadata: Additional metadata for the edge
            
        Returns:
            True if edge was added successfully
        """
        return await self._add_edge(
            agent_id, source_content, target_content,
            EdgeType.BELIEF, confidence, metadata
        )
    
    async def add_action_edge(
        self,
        agent_id: str,
        source_content: str,
        target_content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an action edge to the agent's graph and calculate story-loss
        
        Args:
            agent_id: ID of the agent
            source_content: Content of the source action/goal
            target_content: Content of the target action/result
            confidence: Confidence in the action connection
            metadata: Additional metadata for the edge
            
        Returns:
            True if edge was added successfully
        """
        return await self._add_edge(
            agent_id, source_content, target_content,
            EdgeType.ACTION, confidence, metadata
        )
    
    async def _add_edge(
        self,
        agent_id: str,
        source_content: str,
        target_content: str,
        edge_type: EdgeType,
        confidence: float,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Internal method to add an edge and trigger story-loss calculation"""
        try:
            if not self._initialized:
                await self.initialize()
            
            graph = await self.get_or_create_agent_graph(agent_id)
            
            # Create or get source node
            source_node = await self._get_or_create_node(
                graph, source_content, 
                NodeType.BELIEF if edge_type == EdgeType.BELIEF else NodeType.ACTION
            )
            
            # Create or get target node
            target_node = await self._get_or_create_node(
                graph, target_content,
                NodeType.BELIEF if edge_type == EdgeType.BELIEF else NodeType.ACTION
            )
            
            # Create the edge
            edge = GraphEdge(
                id="",  # Will be auto-generated
                source_id=source_node.id,
                target_id=target_node.id,
                type=edge_type,
                confidence=confidence,
                metadata=metadata or {}
            )
            
            # Calculate story-loss before adding the edge
            story_loss = await self.story_loss_calculator.calculate_story_loss(
                agent_id, [edge], graph.nodes, graph.edges
            )
            
            # Add the edge to the graph
            if not graph.add_edge(edge):
                return False
            
            # Save the updated graph
            await self._save_agent_graph(graph)
            
            # Notify metrics callbacks
            await self._notify_metrics_callbacks(agent_id, story_loss, {
                'edge_id': edge.id,
                'edge_type': edge_type.value,
                'confidence': confidence,
                'graph_version': graph.version
            })
            
            # Check if threshold is exceeded
            if story_loss > self.story_loss_threshold:
                await self._handle_threshold_exceeded(agent_id, story_loss)
            
            logger.info(
                f"Added {edge_type.value} edge for agent {agent_id}, "
                f"story-loss: {story_loss:.3f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add {edge_type.value} edge for agent {agent_id}: {e}")
            return False
    
    async def _get_or_create_node(
        self,
        graph: AgentGraph,
        content: str,
        node_type: NodeType
    ) -> GraphNode:
        """Get existing node or create a new one"""
        # Check if a node with similar content already exists
        for node in graph.nodes.values():
            if node.content == content and node.type == node_type:
                return node
        
        # Create new node
        node = GraphNode(
            id="",  # Will be auto-generated
            type=node_type,
            content=content,
            timestamp=datetime.now()
        )
        
        graph.add_node(node)
        return node
    
    async def _notify_metrics_callbacks(
        self,
        agent_id: str,
        story_loss: float,
        metadata: Dict[str, Any]
    ):
        """Notify all registered metrics callbacks"""
        for callback in self.metrics_callbacks:
            try:
                await callback.on_story_loss_calculated(agent_id, story_loss, metadata)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")
    
    async def _handle_threshold_exceeded(self, agent_id: str, story_loss: float):
        """Handle story-loss threshold exceedance"""
        logger.warning(
            f"Story-loss threshold exceeded for agent {agent_id}: "
            f"{story_loss:.3f} > {self.story_loss_threshold}"
        )
        
        # Notify callbacks about threshold exceedance
        for callback in self.metrics_callbacks:
            try:
                await callback.on_threshold_exceeded(
                    agent_id, story_loss, self.story_loss_threshold
                )
            except Exception as e:
                logger.error(f"Error in threshold callback: {e}")
        
        # Trigger alert system
        await self._trigger_story_loss_alert(agent_id, story_loss)
        
        # Trigger self-reflection minion
        await self._trigger_self_reflection(agent_id, story_loss)
    
    async def _trigger_self_reflection(self, agent_id: str, story_loss: float):
        """Trigger self-reflection minion"""
        try:
            from .minion_service import get_minion_coordinator
            
            # Get minion coordinator
            coordinator = await get_minion_coordinator()
            
            # Trigger self-reflection task
            task_id = await coordinator.trigger_self_reflection(
                agent_id=agent_id,
                story_loss=story_loss,
                metadata={
                    "trigger_source": "gnf_service",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            if task_id:
                logger.info(f"Self-reflection task {task_id} triggered for agent {agent_id}")
            else:
                logger.warning(f"Failed to trigger self-reflection for agent {agent_id}")
                
        except ImportError:
            logger.warning("Minion service not available for self-reflection")
        except Exception as e:
            logger.error(f"Error triggering self-reflection for agent {agent_id}: {e}")
    
    async def _trigger_story_loss_alert(self, agent_id: str, story_loss: float):
        """Trigger story-loss alert"""
        try:
            from .alert_service import get_alert_service
            
            # Get alert service
            alert_service = await get_alert_service()
            
            # Create event data
            event_data = {
                "event_type": "story_loss_threshold",
                "agent_id": agent_id,
                "story_loss": story_loss,
                "threshold": self.story_loss_threshold,
                "threshold_exceeded": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process event through alert system
            alert_ids = await alert_service.process_event(event_data)
            
            if alert_ids:
                logger.info(f"Story-loss alerts created for agent {agent_id}: {alert_ids}")
            else:
                logger.debug(f"No new alerts created for agent {agent_id} story-loss event")
                
        except ImportError:
            logger.warning("Alert service not available for story-loss alerts")
        except Exception as e:
            logger.error(f"Error triggering story-loss alert for agent {agent_id}: {e}")
    
    async def get_agent_graph(self, agent_id: str) -> Optional[AgentGraph]:
        """Get the current graph for an agent"""
        return await self.get_or_create_agent_graph(agent_id)
    
    async def get_story_loss_history(
        self,
        agent_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get story-loss history for the past N hours"""
        try:
            end_time = datetime.now()
            start_time = end_time.replace(
                hour=end_time.hour - hours if end_time.hour >= hours else 0
            )
            
            query = (
                self.db.collection('agent_metrics')
                .document(agent_id)
                .collection('time_series')
                .where('timestamp', '>=', start_time)
                .where('timestamp', '<=', end_time)
                .order_by('timestamp')
            )
            
            docs = await asyncio.get_event_loop().run_in_executor(
                None, query.get
            )
            
            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append({
                    'timestamp': data['timestamp'],
                    'story_loss': data['story_loss'],
                    'metadata': data.get('metadata', {})
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get story-loss history for agent {agent_id}: {e}")
            return []


# Global instance
_gnf_service: Optional[GlobalNarrativeFrame] = None


async def get_gnf_service() -> GlobalNarrativeFrame:
    """Get the global GNF service instance"""
    global _gnf_service
    if _gnf_service is None:
        _gnf_service = GlobalNarrativeFrame()
    if not _gnf_service._initialized:
        await _gnf_service.initialize()
    return _gnf_service


async def init_gnf_service() -> GlobalNarrativeFrame:
    """Initialize and return the global GNF service instance"""
    return await get_gnf_service()