"""
Umwelt Conflict Detection Service

Detects conflicts between incoming Umwelt deltas and established GNF facts.
Raises umwelt_conflict events for self-reflection or human review when
contradictions are detected.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

from firebase_admin import firestore
from .gnf_service import get_gnf_service, AgentGraph, GraphNode, GraphEdge, NodeType, EdgeType
from .umwelt_service import UmweltEntry, UpdatePriority

logger = logging.getLogger(__name__)


class ConflictSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictType(Enum):
    FACTUAL_CONTRADICTION = "factual_contradiction"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    LOGICAL_IMPOSSIBILITY = "logical_impossibility"
    VALUE_MISMATCH = "value_mismatch"
    CONTEXT_VIOLATION = "context_violation"


@dataclass
class ConflictResult:
    """Result of conflict detection analysis"""
    has_conflict: bool
    conflict_type: Optional[ConflictType] = None
    severity: ConflictSeverity = ConflictSeverity.LOW
    description: str = ""
    gnf_nodes_involved: List[str] = None
    umwelt_keys_involved: List[str] = None
    confidence: float = 0.0
    suggested_resolution: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.gnf_nodes_involved is None:
            self.gnf_nodes_involved = []
        if self.umwelt_keys_involved is None:
            self.umwelt_keys_involved = []
        if self.metadata is None:
            self.metadata = {}


class FactExtractor:
    """Extracts and normalizes facts from GNF nodes and Umwelt entries"""
    
    def __init__(self):
        self.numerical_patterns = [
            r'(\d+(?:\.\d+)?)\s*(seconds?|minutes?|hours?|days?|weeks?|months?|years?)',
            r'(\d+(?:\.\d+)?)\s*(kg|pounds?|lbs?|grams?|g)',
            r'(\d+(?:\.\d+)?)\s*(meters?|feet|ft|inches?|in|cm|mm)',
            r'(\d+(?:\.\d+)?)\s*(?:degrees?|°)\s*([CF])?',
            r'\$(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)%'
        ]
        
        self.temporal_patterns = [
            r'(yesterday|today|tomorrow)',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'(before|after|during|while)\s+(.+)',
            r'(\d{1,2}):(\d{2})\s*(am|pm)?'
        ]
        
        self.boolean_patterns = [
            r'(is|are|was|were)\s+(not\s+)?(true|false|correct|wrong|active|inactive|enabled|disabled)',
            r'(can|cannot|could|couldn\'t|will|won\'t|shall|shall not)\s+(.+)',
            r'(has|have|had)\s+(not\s+)?(.+)',
            r'(does|doesn\'t|did|didn\'t)\s+(.+)'
        ]
    
    def extract_facts_from_node(self, node: GraphNode) -> List[Dict[str, Any]]:
        """Extract structured facts from a GNF node"""
        facts = []
        content = node.content.lower().strip()
        
        # Extract numerical facts
        for pattern in self.numerical_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                facts.append({
                    'type': 'numerical',
                    'value': match.group(1),
                    'unit': match.group(2) if match.lastindex > 1 else None,
                    'context': match.group(0),
                    'node_id': node.id,
                    'confidence': node.confidence
                })
        
        # Extract temporal facts
        for pattern in self.temporal_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                facts.append({
                    'type': 'temporal',
                    'value': match.group(0),
                    'context': content,
                    'node_id': node.id,
                    'confidence': node.confidence
                })
        
        # Extract boolean facts
        for pattern in self.boolean_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                negated = 'not' in match.group(0).lower() or 'n\'t' in match.group(0).lower()
                facts.append({
                    'type': 'boolean',
                    'value': not negated,
                    'subject': match.group(0),
                    'context': content,
                    'node_id': node.id,
                    'confidence': node.confidence
                })
        
        # Extract general factual statements
        if node.type in [NodeType.FACT, NodeType.BELIEF]:
            facts.append({
                'type': 'statement',
                'value': content,
                'context': content,
                'node_id': node.id,
                'confidence': node.confidence
            })
        
        return facts
    
    def extract_facts_from_umwelt_entry(self, key: str, entry: UmweltEntry) -> List[Dict[str, Any]]:
        """Extract structured facts from an Umwelt entry"""
        facts = []
        
        # Handle different value types
        if isinstance(entry.value, (int, float)):
            facts.append({
                'type': 'numerical',
                'value': entry.value,
                'key': key,
                'context': f"{key}: {entry.value}",
                'confidence': entry.confidence,
                'timestamp': entry.timestamp
            })
        
        elif isinstance(entry.value, bool):
            facts.append({
                'type': 'boolean',
                'value': entry.value,
                'key': key,
                'context': f"{key}: {entry.value}",
                'confidence': entry.confidence,
                'timestamp': entry.timestamp
            })
        
        elif isinstance(entry.value, str):
            content = entry.value.lower().strip()
            
            # Extract patterns from string values
            for pattern in self.numerical_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    facts.append({
                        'type': 'numerical',
                        'value': match.group(1),
                        'unit': match.group(2) if match.lastindex > 1 else None,
                        'key': key,
                        'context': f"{key}: {entry.value}",
                        'confidence': entry.confidence,
                        'timestamp': entry.timestamp
                    })
            
            # String as statement
            facts.append({
                'type': 'statement',
                'value': content,
                'key': key,
                'context': f"{key}: {entry.value}",
                'confidence': entry.confidence,
                'timestamp': entry.timestamp
            })
        
        elif isinstance(entry.value, dict):
            # Handle nested dictionary values
            for nested_key, nested_value in entry.value.items():
                nested_entry = UmweltEntry(
                    key=f"{key}.{nested_key}",
                    value=nested_value,
                    timestamp=entry.timestamp,
                    confidence=entry.confidence
                )
                facts.extend(self.extract_facts_from_umwelt_entry(f"{key}.{nested_key}", nested_entry))
        
        return facts


class ConflictAnalyzer:
    """Analyzes conflicts between GNF facts and Umwelt data"""
    
    def __init__(self):
        self.fact_extractor = FactExtractor()
    
    async def detect_conflicts(
        self,
        agent_id: str,
        umwelt_delta: Dict[str, Any],
        gnf_graph: AgentGraph
    ) -> List[ConflictResult]:
        """
        Detect conflicts between Umwelt delta and GNF facts
        
        Args:
            agent_id: ID of the agent
            umwelt_delta: New Umwelt observations
            gnf_graph: Current GNF graph
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            # Extract facts from GNF graph
            gnf_facts = []
            for node in gnf_graph.nodes.values():
                node_facts = self.fact_extractor.extract_facts_from_node(node)
                gnf_facts.extend(node_facts)
            
            # Extract facts from Umwelt delta
            umwelt_facts = []
            for key, value in umwelt_delta.items():
                entry = UmweltEntry(
                    key=key,
                    value=value,
                    timestamp=datetime.now(),
                    confidence=1.0
                )
                entry_facts = self.fact_extractor.extract_facts_from_umwelt_entry(key, entry)
                umwelt_facts.extend(entry_facts)
            
            # Compare facts for conflicts
            for umwelt_fact in umwelt_facts:
                for gnf_fact in gnf_facts:
                    conflict = await self._compare_facts(umwelt_fact, gnf_fact)
                    if conflict.has_conflict:
                        conflicts.append(conflict)
            
            logger.info(f"Detected {len(conflicts)} conflicts for agent {agent_id}")
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting conflicts for agent {agent_id}: {e}")
            return []
    
    async def _compare_facts(
        self,
        umwelt_fact: Dict[str, Any],
        gnf_fact: Dict[str, Any]
    ) -> ConflictResult:
        """Compare two facts for conflicts"""
        
        # No conflict by default
        no_conflict = ConflictResult(has_conflict=False)
        
        # Skip if facts are not comparable
        if umwelt_fact['type'] != gnf_fact['type']:
            return no_conflict
        
        fact_type = umwelt_fact['type']
        
        if fact_type == 'numerical':
            return await self._compare_numerical_facts(umwelt_fact, gnf_fact)
        elif fact_type == 'boolean':
            return await self._compare_boolean_facts(umwelt_fact, gnf_fact)
        elif fact_type == 'temporal':
            return await self._compare_temporal_facts(umwelt_fact, gnf_fact)
        elif fact_type == 'statement':
            return await self._compare_statement_facts(umwelt_fact, gnf_fact)
        
        return no_conflict
    
    async def _compare_numerical_facts(
        self,
        umwelt_fact: Dict[str, Any],
        gnf_fact: Dict[str, Any]
    ) -> ConflictResult:
        """Compare numerical facts"""
        try:
            umwelt_value = float(umwelt_fact['value'])
            gnf_value = float(gnf_fact['value'])
            
            # Check for significant differences
            diff_percent = abs(umwelt_value - gnf_value) / max(abs(gnf_value), 1) * 100
            
            if diff_percent > 20:  # 20% difference threshold
                return ConflictResult(
                    has_conflict=True,
                    conflict_type=ConflictType.VALUE_MISMATCH,
                    severity=ConflictSeverity.MEDIUM if diff_percent > 50 else ConflictSeverity.LOW,
                    description=f"Numerical values differ significantly: {umwelt_value} vs {gnf_value} ({diff_percent:.1f}% difference)",
                    gnf_nodes_involved=[gnf_fact['node_id']],
                    umwelt_keys_involved=[umwelt_fact.get('key', 'unknown')],
                    confidence=min(umwelt_fact.get('confidence', 1.0), gnf_fact.get('confidence', 1.0)),
                    suggested_resolution="Verify source of newer measurement and update belief if confirmed"
                )
        
        except (ValueError, KeyError):
            pass
        
        return ConflictResult(has_conflict=False)
    
    async def _compare_boolean_facts(
        self,
        umwelt_fact: Dict[str, Any],
        gnf_fact: Dict[str, Any]
    ) -> ConflictResult:
        """Compare boolean facts"""
        try:
            umwelt_value = umwelt_fact['value']
            gnf_value = gnf_fact['value']
            
            if umwelt_value != gnf_value:
                return ConflictResult(
                    has_conflict=True,
                    conflict_type=ConflictType.FACTUAL_CONTRADICTION,
                    severity=ConflictSeverity.HIGH,
                    description=f"Boolean values contradict: {umwelt_value} vs {gnf_value}",
                    gnf_nodes_involved=[gnf_fact['node_id']],
                    umwelt_keys_involved=[umwelt_fact.get('key', 'unknown')],
                    confidence=min(umwelt_fact.get('confidence', 1.0), gnf_fact.get('confidence', 1.0)),
                    suggested_resolution="Determine which source is more reliable and update accordingly"
                )
        
        except KeyError:
            pass
        
        return ConflictResult(has_conflict=False)
    
    async def _compare_temporal_facts(
        self,
        umwelt_fact: Dict[str, Any],
        gnf_fact: Dict[str, Any]
    ) -> ConflictResult:
        """Compare temporal facts"""
        # Simple temporal conflict detection
        umwelt_temporal = str(umwelt_fact['value']).lower()
        gnf_temporal = str(gnf_fact['value']).lower()
        
        # Check for obvious contradictions
        contradictions = [
            ('yesterday', 'today'),
            ('today', 'tomorrow'),
            ('before', 'after'),
            ('morning', 'evening'),
            ('am', 'pm')
        ]
        
        for term1, term2 in contradictions:
            if (term1 in umwelt_temporal and term2 in gnf_temporal) or \
               (term2 in umwelt_temporal and term1 in gnf_temporal):
                return ConflictResult(
                    has_conflict=True,
                    conflict_type=ConflictType.TEMPORAL_INCONSISTENCY,
                    severity=ConflictSeverity.MEDIUM,
                    description=f"Temporal contradiction: {umwelt_temporal} vs {gnf_temporal}",
                    gnf_nodes_involved=[gnf_fact['node_id']],
                    umwelt_keys_involved=[umwelt_fact.get('key', 'unknown')],
                    confidence=0.7,
                    suggested_resolution="Verify temporal context and update timeline"
                )
        
        return ConflictResult(has_conflict=False)
    
    async def _compare_statement_facts(
        self,
        umwelt_fact: Dict[str, Any],
        gnf_fact: Dict[str, Any]
    ) -> ConflictResult:
        """Compare statement facts"""
        umwelt_statement = str(umwelt_fact['value']).lower()
        gnf_statement = str(gnf_fact['value']).lower()
        
        # Check for direct negations
        negation_patterns = [
            (r'is (.+)', r'is not \1'),
            (r'can (.+)', r'cannot \1'),
            (r'will (.+)', r'will not \1'),
            (r'has (.+)', r'has no \1'),
            (r'(.+) exists', r'\1 does not exist'),
            (r'(.+) is true', r'\1 is false'),
            (r'(.+) is possible', r'\1 is impossible')
        ]
        
        for positive_pattern, negative_pattern in negation_patterns:
            if (re.search(positive_pattern, umwelt_statement) and re.search(negative_pattern, gnf_statement)) or \
               (re.search(negative_pattern, umwelt_statement) and re.search(positive_pattern, gnf_statement)):
                return ConflictResult(
                    has_conflict=True,
                    conflict_type=ConflictType.LOGICAL_IMPOSSIBILITY,
                    severity=ConflictSeverity.HIGH,
                    description=f"Logical contradiction in statements: '{umwelt_statement}' vs '{gnf_statement}'",
                    gnf_nodes_involved=[gnf_fact['node_id']],
                    umwelt_keys_involved=[umwelt_fact.get('key', 'unknown')],
                    confidence=0.8,
                    suggested_resolution="Resolve logical contradiction through evidence verification"
                )
        
        # Check for semantic similarity that might indicate conflict
        # (This is a simplified version - in practice, you'd use NLP similarity)
        common_words = set(umwelt_statement.split()) & set(gnf_statement.split())
        if len(common_words) > 2:  # Statements share significant vocabulary
            # Look for negation indicators
            umwelt_negated = any(neg in umwelt_statement for neg in ['not', 'no', 'never', 'none', 'false'])
            gnf_negated = any(neg in gnf_statement for neg in ['not', 'no', 'never', 'none', 'false'])
            
            if umwelt_negated != gnf_negated:
                return ConflictResult(
                    has_conflict=True,
                    conflict_type=ConflictType.FACTUAL_CONTRADICTION,
                    severity=ConflictSeverity.MEDIUM,
                    description=f"Potential statement contradiction: '{umwelt_statement}' vs '{gnf_statement}'",
                    gnf_nodes_involved=[gnf_fact['node_id']],
                    umwelt_keys_involved=[umwelt_fact.get('key', 'unknown')],
                    confidence=0.6,
                    suggested_resolution="Review context and determine which statement is more accurate"
                )
        
        return ConflictResult(has_conflict=False)


class UmweltConflictDetector:
    """Main service for detecting Umwelt-GNF conflicts"""
    
    def __init__(self):
        self.conflict_analyzer = ConflictAnalyzer()
        self.db = None  # Will be initialized lazily
        self._initialized = False
    
    async def initialize(self):
        """Initialize the conflict detector"""
        self.db = firestore.client()
        self._initialized = True
        logger.info("UmweltConflictDetector initialized")
    
    async def check_umwelt_conflicts(
        self,
        agent_id: str,
        umwelt_delta: Dict[str, Any],
        priority: Optional[UpdatePriority] = None
    ) -> List[ConflictResult]:
        """
        Check for conflicts between Umwelt delta and GNF
        
        Args:
            agent_id: ID of the agent
            umwelt_delta: New Umwelt observations
            priority: Priority of the update
            
        Returns:
            List of detected conflicts
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Get GNF service and agent graph
            gnf_service = await get_gnf_service()
            agent_graph = await gnf_service.get_agent_graph(agent_id)
            
            if not agent_graph:
                logger.warning(f"No GNF graph found for agent {agent_id}")
                return []
            
            # Detect conflicts
            conflicts = await self.conflict_analyzer.detect_conflicts(
                agent_id, umwelt_delta, agent_graph
            )
            
            # Raise events for significant conflicts
            for conflict in conflicts:
                if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                    await self._raise_conflict_event(agent_id, conflict)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking Umwelt conflicts for agent {agent_id}: {e}")
            return []
    
    async def _raise_conflict_event(self, agent_id: str, conflict: ConflictResult):
        """Raise a umwelt_conflict event"""
        try:
            event_ref = self.db.collection('agent_events').document()
            
            event_data = {
                'agent_id': agent_id,
                'event_type': 'umwelt_conflict',
                'conflict_type': conflict.conflict_type.value,
                'severity': conflict.severity.value,
                'description': conflict.description,
                'gnf_nodes_involved': conflict.gnf_nodes_involved,
                'umwelt_keys_involved': conflict.umwelt_keys_involved,
                'confidence': conflict.confidence,
                'suggested_resolution': conflict.suggested_resolution,
                'metadata': conflict.metadata,
                'timestamp': datetime.now(),
                'requires_attention': conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL],
                'auto_resolvable': conflict.severity == ConflictSeverity.LOW
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None, event_ref.set, event_data
            )
            
            logger.warning(
                f"Umwelt conflict event raised for agent {agent_id}: "
                f"{conflict.conflict_type.value} ({conflict.severity.value})"
            )
            
            # Also trigger alert system
            await self._trigger_conflict_alert(agent_id, conflict)
            
        except Exception as e:
            logger.error(f"Failed to raise conflict event for agent {agent_id}: {e}")
    
    async def _trigger_conflict_alert(self, agent_id: str, conflict: ConflictResult):
        """Trigger alert for Umwelt conflicts"""
        try:
            from .alert_service import get_alert_service
            
            # Get alert service
            alert_service = await get_alert_service()
            
            # Create event data
            event_data = {
                "event_type": "umwelt_conflict",
                "agent_id": agent_id,
                "conflict_type": conflict.conflict_type.value,
                "severity": conflict.severity.value,
                "confidence": conflict.confidence,
                "description": conflict.description,
                "gnf_nodes_involved": conflict.gnf_nodes_involved,
                "umwelt_keys_involved": conflict.umwelt_keys_involved,
                "suggested_resolution": conflict.suggested_resolution,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process event through alert system
            alert_ids = await alert_service.process_event(event_data)
            
            if alert_ids:
                logger.info(f"Umwelt conflict alerts created for agent {agent_id}: {alert_ids}")
            else:
                logger.debug(f"No new alerts created for agent {agent_id} Umwelt conflict")
                
        except ImportError:
            logger.warning("Alert service not available for Umwelt conflict alerts")
        except Exception as e:
            logger.error(f"Error triggering Umwelt conflict alert for agent {agent_id}: {e}")


# Global instance
_umwelt_conflict_detector: Optional[UmweltConflictDetector] = None


async def get_umwelt_conflict_detector() -> UmweltConflictDetector:
    """Get the global Umwelt conflict detector instance"""
    global _umwelt_conflict_detector
    if _umwelt_conflict_detector is None:
        _umwelt_conflict_detector = UmweltConflictDetector()
    if not _umwelt_conflict_detector._initialized:
        await _umwelt_conflict_detector.initialize()
    return _umwelt_conflict_detector


async def init_umwelt_conflict_service() -> UmweltConflictDetector:
    """Initialize and return the global Umwelt conflict detector instance"""
    return await get_umwelt_conflict_detector()