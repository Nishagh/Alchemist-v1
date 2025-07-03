"""
Story-Loss Calculation System for Narrative Coherence Monitoring
"""

import asyncio
import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from config.accountability_config import accountability_config
from services.firebase_service import firebase_service

logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """Types of narrative conflicts"""
    BELIEF_CONTRADICTION = "belief_contradiction"
    VALUE_CONFLICT = "value_conflict"
    GOAL_INCONSISTENCY = "goal_inconsistency"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    FACTUAL_CONTRADICTION = "factual_contradiction"


@dataclass
class NarrativeElement:
    """A narrative element (belief, fact, goal, etc.)"""
    id: str
    type: str  # belief, fact, goal, action, event
    content: str
    confidence: float
    timestamp: datetime
    source: str  # conversation_id, interaction_id, etc.
    metadata: Dict[str, Any]


@dataclass
class NarrativeConflict:
    """A detected conflict in the narrative"""
    conflict_type: ConflictType
    element1: NarrativeElement
    element2: NarrativeElement
    severity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str
    suggested_resolution: Optional[str] = None


class StoryLossCalculator:
    """
    Calculates story-loss metrics for narrative coherence monitoring
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.narrative_elements: List[NarrativeElement] = []
        self.detected_conflicts: List[NarrativeConflict] = []
        
        # Load existing narrative elements
        asyncio.create_task(self._load_narrative_elements())
    
    async def calculate_interaction_story_loss(self, pre_state: Dict[str, Any], 
                                             post_state: Dict[str, Any], 
                                             interaction_data: Dict[str, Any]) -> float:
        """
        Calculate story-loss for a single interaction
        
        Args:
            pre_state: Agent state before interaction
            post_state: Agent state after interaction  
            interaction_data: The interaction data
            
        Returns:
            Story-loss value between 0.0 and 1.0
        """
        try:
            # Extract narrative elements from the interaction
            new_elements = await self._extract_narrative_elements(interaction_data)
            
            # Detect conflicts with existing narrative
            conflicts = await self._detect_conflicts(new_elements)
            
            # Calculate story-loss based on conflicts
            story_loss = await self._compute_story_loss(conflicts, new_elements)
            
            # Store the new elements and conflicts
            await self._store_narrative_elements(new_elements)
            await self._store_conflicts(conflicts)
            
            # Update time-series data
            await firebase_service.update_agent_metrics(self.agent_id, {
                'story_loss': story_loss,
                'conflict_count': len(conflicts),
                'narrative_elements_count': len(self.narrative_elements)
            })
            
            logger.info(f"Calculated story-loss: {story_loss:.3f} for agent {self.agent_id}")
            return story_loss
            
        except Exception as e:
            logger.error(f"Failed to calculate story-loss: {e}")
            return 0.0  # Return neutral value on error
    
    async def _extract_narrative_elements(self, interaction_data: Dict[str, Any]) -> List[NarrativeElement]:
        """Extract narrative elements from interaction"""
        elements = []
        timestamp = datetime.utcnow()
        
        user_message = interaction_data.get('user_message', '')
        agent_response = interaction_data.get('agent_response', '')
        conversation_id = interaction_data.get('conversation_id', '')
        
        # Extract beliefs from agent response
        beliefs = await self._extract_beliefs(agent_response)
        for belief in beliefs:
            elements.append(NarrativeElement(
                id=f"belief_{len(elements)}_{int(timestamp.timestamp())}",
                type="belief",
                content=belief['content'],
                confidence=belief['confidence'],
                timestamp=timestamp,
                source=conversation_id,
                metadata={'extraction_method': 'pattern_matching'}
            ))
        
        # Extract facts from agent response
        facts = await self._extract_facts(agent_response)
        for fact in facts:
            elements.append(NarrativeElement(
                id=f"fact_{len(elements)}_{int(timestamp.timestamp())}",
                type="fact",
                content=fact['content'],
                confidence=fact['confidence'],
                timestamp=timestamp,
                source=conversation_id,
                metadata={'extraction_method': 'pattern_matching'}
            ))
        
        # Extract goals from agent response
        goals = await self._extract_goals(agent_response)
        for goal in goals:
            elements.append(NarrativeElement(
                id=f"goal_{len(elements)}_{int(timestamp.timestamp())}",
                type="goal",
                content=goal['content'],
                confidence=goal['confidence'],
                timestamp=timestamp,
                source=conversation_id,
                metadata={'extraction_method': 'pattern_matching'}
            ))
        
        # Extract actions from agent response
        actions = await self._extract_actions(agent_response, user_message)
        for action in actions:
            elements.append(NarrativeElement(
                id=f"action_{len(elements)}_{int(timestamp.timestamp())}",
                type="action",
                content=action['content'],
                confidence=action['confidence'],
                timestamp=timestamp,
                source=conversation_id,
                metadata={'user_request': user_message[:100]}
            ))
        
        return elements
    
    async def _extract_beliefs(self, text: str) -> List[Dict[str, Any]]:
        """Extract beliefs from text using pattern matching"""
        beliefs = []
        
        # Patterns that indicate beliefs
        belief_patterns = [
            r"I believe (?:that )?(.+?)(?:\.|$)",
            r"I think (?:that )?(.+?)(?:\.|$)", 
            r"In my opinion,? (.+?)(?:\.|$)",
            r"It seems (?:to me )?(?:that )?(.+?)(?:\.|$)",
            r"I feel (?:that )?(.+?)(?:\.|$)"
        ]
        
        for pattern in belief_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                belief_content = match.group(1).strip()
                if len(belief_content) > 10:  # Filter out very short matches
                    beliefs.append({
                        'content': belief_content,
                        'confidence': 0.7  # Default confidence for pattern-based extraction
                    })
        
        return beliefs
    
    async def _extract_facts(self, text: str) -> List[Dict[str, Any]]:
        """Extract factual statements from text"""
        facts = []
        
        # Patterns that indicate factual statements
        fact_patterns = [
            r"(?:It is|This is) (?:a fact that )?(.+?)(?:\.|$)",
            r"(?:Actually|In fact),? (.+?)(?:\.|$)",
            r"(?:The truth is|Truth is) (?:that )?(.+?)(?:\.|$)",
            r"According to (.+?)(?:\.|$)",
            r"Research shows (?:that )?(.+?)(?:\.|$)"
        ]
        
        for pattern in fact_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fact_content = match.group(1).strip()
                if len(fact_content) > 10:
                    facts.append({
                        'content': fact_content,
                        'confidence': 0.8  # Higher confidence for factual statements
                    })
        
        return facts
    
    async def _extract_goals(self, text: str) -> List[Dict[str, Any]]:
        """Extract goals and intentions from text"""
        goals = []
        
        # Patterns that indicate goals
        goal_patterns = [
            r"My goal is (?:to )?(.+?)(?:\.|$)",
            r"I aim (?:to )?(.+?)(?:\.|$)",
            r"I want (?:to )?(.+?)(?:\.|$)",
            r"I intend (?:to )?(.+?)(?:\.|$)",
            r"I hope (?:to )?(.+?)(?:\.|$)",
            r"I will try (?:to )?(.+?)(?:\.|$)"
        ]
        
        for pattern in goal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                goal_content = match.group(1).strip()
                if len(goal_content) > 5:
                    goals.append({
                        'content': goal_content,
                        'confidence': 0.6
                    })
        
        return goals
    
    async def _extract_actions(self, agent_response: str, user_message: str) -> List[Dict[str, Any]]:
        """Extract actions taken by the agent"""
        actions = []
        
        # The response itself is an action
        if len(agent_response.strip()) > 0:
            actions.append({
                'content': f"Responded to user query: {user_message[:50]}...",
                'confidence': 1.0
            })
        
        # Patterns for specific actions
        action_patterns = [
            r"I (?:will|am going to|shall) (.+?)(?:\.|$)",
            r"Let me (.+?)(?:\.|$)",
            r"I am (.+?)(?:\.|$)",
            r"I have (.+?)(?:\.|$)"
        ]
        
        for pattern in action_patterns:
            matches = re.finditer(pattern, agent_response, re.IGNORECASE)
            for match in matches:
                action_content = match.group(1).strip()
                if len(action_content) > 5:
                    actions.append({
                        'content': action_content,
                        'confidence': 0.8
                    })
        
        return actions
    
    async def _detect_conflicts(self, new_elements: List[NarrativeElement]) -> List[NarrativeConflict]:
        """Detect conflicts between new elements and existing narrative"""
        conflicts = []
        
        for new_element in new_elements:
            for existing_element in self.narrative_elements:
                conflict = await self._check_element_conflict(new_element, existing_element)
                if conflict:
                    conflicts.append(conflict)
        
        # Also check for conflicts within new elements
        for i, element1 in enumerate(new_elements):
            for element2 in new_elements[i+1:]:
                conflict = await self._check_element_conflict(element1, element2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _check_element_conflict(self, element1: NarrativeElement, 
                                    element2: NarrativeElement) -> Optional[NarrativeConflict]:
        """Check if two elements conflict"""
        
        # Skip if elements are the same type and very similar
        if element1.type == element2.type:
            similarity = await self._calculate_similarity(element1.content, element2.content)
            if similarity > 0.9:
                return None  # Too similar, not a conflict
        
        # Check for belief contradictions
        if element1.type == "belief" and element2.type == "belief":
            conflict = await self._check_belief_contradiction(element1, element2)
            if conflict:
                return conflict
        
        # Check for fact contradictions
        if element1.type == "fact" and element2.type == "fact":
            conflict = await self._check_fact_contradiction(element1, element2)
            if conflict:
                return conflict
        
        # Check for goal inconsistencies
        if element1.type == "goal" and element2.type == "goal":
            conflict = await self._check_goal_inconsistency(element1, element2)
            if conflict:
                return conflict
        
        # Check for temporal inconsistencies
        conflict = await self._check_temporal_inconsistency(element1, element2)
        if conflict:
            return conflict
        
        return None
    
    async def _check_belief_contradiction(self, belief1: NarrativeElement, 
                                        belief2: NarrativeElement) -> Optional[NarrativeConflict]:
        """Check for contradictions between beliefs"""
        
        # Simple negation detection
        content1 = belief1.content.lower()
        content2 = belief2.content.lower()
        
        # Check for explicit negations
        negation_patterns = [
            (r"(.+) is (.+)", r"\1 is not \2"),
            (r"(.+) can (.+)", r"\1 cannot \2"),
            (r"(.+) will (.+)", r"\1 will not \2"),
            (r"(.+) should (.+)", r"\1 should not \2")
        ]
        
        for positive_pattern, negative_pattern in negation_patterns:
            pos_match = re.search(positive_pattern, content1)
            neg_match = re.search(negative_pattern, content2)
            
            if pos_match and neg_match:
                if pos_match.group(1) == neg_match.group(1):
                    return NarrativeConflict(
                        conflict_type=ConflictType.BELIEF_CONTRADICTION,
                        element1=belief1,
                        element2=belief2,
                        severity=0.8,
                        confidence=0.7,
                        description=f"Contradictory beliefs about {pos_match.group(1)}",
                        suggested_resolution="Clarify which belief is more accurate"
                    )
        
        return None
    
    async def _check_fact_contradiction(self, fact1: NarrativeElement, 
                                      fact2: NarrativeElement) -> Optional[NarrativeConflict]:
        """Check for contradictions between facts"""
        
        # Facts should have higher severity for contradictions
        content1 = fact1.content.lower()
        content2 = fact2.content.lower()
        
        # Simple contradiction detection (can be enhanced)
        contradiction_keywords = [
            ("true", "false"), ("correct", "incorrect"), ("right", "wrong"),
            ("yes", "no"), ("possible", "impossible"), ("always", "never")
        ]
        
        for pos_word, neg_word in contradiction_keywords:
            if pos_word in content1 and neg_word in content2:
                return NarrativeConflict(
                    conflict_type=ConflictType.FACTUAL_CONTRADICTION,
                    element1=fact1,
                    element2=fact2,
                    severity=0.9,  # High severity for factual contradictions
                    confidence=0.6,
                    description=f"Factual contradiction involving {pos_word}/{neg_word}",
                    suggested_resolution="Verify facts and correct inaccurate information"
                )
        
        return None
    
    async def _check_goal_inconsistency(self, goal1: NarrativeElement, 
                                      goal2: NarrativeElement) -> Optional[NarrativeConflict]:
        """Check for inconsistencies between goals"""
        
        # Goals might conflict if they're mutually exclusive
        content1 = goal1.content.lower()
        content2 = goal2.content.lower()
        
        # Simple conflict detection (can be enhanced with domain knowledge)
        conflicting_pairs = [
            ("minimize", "maximize"), ("reduce", "increase"), ("avoid", "pursue"),
            ("stop", "start"), ("prevent", "enable")
        ]
        
        for word1, word2 in conflicting_pairs:
            if word1 in content1 and word2 in content2:
                return NarrativeConflict(
                    conflict_type=ConflictType.GOAL_INCONSISTENCY,
                    element1=goal1,
                    element2=goal2,
                    severity=0.6,
                    confidence=0.5,
                    description=f"Potentially conflicting goals: {word1} vs {word2}",
                    suggested_resolution="Clarify goal priorities and resolve conflicts"
                )
        
        return None
    
    async def _check_temporal_inconsistency(self, element1: NarrativeElement, 
                                          element2: NarrativeElement) -> Optional[NarrativeConflict]:
        """Check for temporal inconsistencies"""
        
        # Check if later statements contradict earlier ones
        time_diff = abs((element1.timestamp - element2.timestamp).total_seconds())
        
        # Only check for temporal inconsistency if elements are far apart in time
        if time_diff < 3600:  # Less than 1 hour
            return None
        
        # If elements contradict and are temporally separated, it's a temporal inconsistency
        similarity = await self._calculate_similarity(element1.content, element2.content)
        if similarity < 0.3:  # Very different content
            return NarrativeConflict(
                conflict_type=ConflictType.TEMPORAL_INCONSISTENCY,
                element1=element1,
                element2=element2,
                severity=0.4,
                confidence=0.3,
                description="Potential temporal inconsistency in narrative",
                suggested_resolution="Review and align with current understanding"
            )
        
        return None
    
    async def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simple implementation)"""
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _compute_story_loss(self, conflicts: List[NarrativeConflict], 
                                new_elements: List[NarrativeElement]) -> float:
        """Compute overall story-loss value"""
        if not conflicts:
            return 0.0
        
        # Weight conflicts by severity and confidence
        weighted_conflict_score = 0.0
        total_weight = 0.0
        
        for conflict in conflicts:
            weight = conflict.severity * conflict.confidence
            weighted_conflict_score += weight
            total_weight += 1.0
        
        # Normalize by number of conflicts and new elements
        if total_weight == 0:
            return 0.0
        
        raw_score = weighted_conflict_score / total_weight
        
        # Adjust based on number of new elements (more elements = more opportunity for conflicts)
        element_factor = min(1.0, len(new_elements) / 10.0)  # Cap at 10 elements
        
        # Final story-loss calculation
        story_loss = raw_score * element_factor
        
        return min(1.0, story_loss)  # Cap at 1.0
    
    async def _load_narrative_elements(self):
        """Load existing narrative elements from narrative graph"""
        try:
            graph_data = await firebase_service.get_narrative_graph(self.agent_id)
            if not graph_data:
                return
            
            nodes = graph_data.get('nodes', [])
            for node in nodes:
                element = NarrativeElement(
                    id=node.get('id', ''),
                    type=node.get('type', 'unknown'),
                    content=node.get('content', ''),
                    confidence=node.get('confidence', 0.5),
                    timestamp=node.get('timestamp', datetime.utcnow()),
                    source=node.get('metadata', {}).get('source', 'unknown'),
                    metadata=node.get('metadata', {})
                )
                self.narrative_elements.append(element)
            
            logger.info(f"Loaded {len(self.narrative_elements)} narrative elements")
            
        except Exception as e:
            logger.error(f"Failed to load narrative elements: {e}")
    
    async def _store_narrative_elements(self, new_elements: List[NarrativeElement]):
        """Store new narrative elements in the narrative graph"""
        try:
            if not new_elements:
                return
            
            # Convert elements to graph nodes
            new_nodes = []
            for element in new_elements:
                node = {
                    'id': element.id,
                    'type': element.type,
                    'content': element.content,
                    'confidence': element.confidence,
                    'timestamp': element.timestamp,
                    'metadata': element.metadata
                }
                new_nodes.append(node)
            
            # Add to existing narrative elements
            self.narrative_elements.extend(new_elements)
            
            # Update narrative graph
            await firebase_service.update_narrative_graph(self.agent_id, {
                'nodes': new_nodes  # This will be merged with existing nodes
            })
            
            logger.info(f"Stored {len(new_elements)} new narrative elements")
            
        except Exception as e:
            logger.error(f"Failed to store narrative elements: {e}")
    
    async def _store_conflicts(self, conflicts: List[NarrativeConflict]):
        """Store detected conflicts"""
        try:
            for conflict in conflicts:
                conflict_data = {
                    'agent_id': self.agent_id,
                    'conflict_type': conflict.conflict_type.value,
                    'severity': conflict.severity,
                    'confidence': conflict.confidence,
                    'description': conflict.description,
                    'suggested_resolution': conflict.suggested_resolution,
                    'element1_id': conflict.element1.id,
                    'element2_id': conflict.element2.id,
                    'requires_attention': conflict.severity > 0.7
                }
                
                await firebase_service.create_agent_event(conflict_data)
            
            if conflicts:
                logger.info(f"Stored {len(conflicts)} narrative conflicts")
                
        except Exception as e:
            logger.error(f"Failed to store conflicts: {e}")
    
    def get_current_story_loss(self) -> float:
        """Get the most recent story-loss value"""
        # This would typically come from the metrics service
        # For now, return 0 as placeholder
        return 0.0