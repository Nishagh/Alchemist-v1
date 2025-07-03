"""
Google Cloud Spanner Graph Service for Epistemic Autonomy (eA³)

Implements Coherent Narrative Exclusivity (CNE) and Recursive Belief Revision (RbR)
for agent life-story management using Google Cloud Spanner's graph capabilities.

Key Concepts:
- CNE: Each agent maintains ONE consistent life-story (no split personalities)
- RbR: Automatic story revision when new evidence creates contradictions
- eA³: Epistemic Autonomy + Accountability + Alignment through narrative coherence
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from google.cloud import spanner
from google.cloud.spanner_v1 import param_types
import uuid

logger = logging.getLogger(__name__)

class StoryEventType(Enum):
    """Types of events in an agent's life-story"""
    BIRTH = "birth"                    # Agent creation
    GOAL_SET = "goal_set"             # New goal assignment
    BELIEF_FORMED = "belief_formed"    # New belief acquired
    ACTION_TAKEN = "action_taken"      # Action performed
    EVIDENCE_RECEIVED = "evidence_received"  # New evidence
    BELIEF_REVISED = "belief_revised"  # Belief updated due to RbR
    CONTRADICTION_RESOLVED = "contradiction_resolved"  # CNE maintenance
    MILESTONE_REACHED = "milestone_reached"  # Goal progress
    REFLECTION_PERFORMED = "reflection_performed"  # Self-reflection
    ALIGNMENT_CHECK = "alignment_check"  # Goal alignment verification

class NarrativeCoherence(Enum):
    """Levels of narrative coherence"""
    PERFECT = "perfect"        # No contradictions
    MINOR_GAPS = "minor_gaps"  # Small inconsistencies
    MAJOR_CONFLICT = "major_conflict"  # Significant contradictions
    INCOHERENT = "incoherent"  # Multiple contradictory storylines

@dataclass
class StoryEvent:
    """A single event in an agent's life-story"""
    id: str
    agent_id: str
    event_type: StoryEventType
    timestamp: datetime
    content: str
    context: Dict[str, Any]
    confidence: float
    evidence_source: str
    causal_parents: List[str] = field(default_factory=list)  # What caused this event
    causal_children: List[str] = field(default_factory=list)  # What this event caused
    narrative_importance: float = 0.5  # How important to the overall story
    revision_count: int = 0  # How many times this has been revised
    is_core_belief: bool = False  # Is this a fundamental belief?
    alignment_score: float = 1.0  # How well this aligns with agent goals

@dataclass
class NarrativeThread:
    """A coherent thread of the agent's story"""
    id: str
    agent_id: str
    title: str
    description: str
    events: List[str]  # Event IDs in chronological order
    coherence_score: float
    importance: float
    created_at: datetime
    last_updated: datetime
    is_active: bool = True

@dataclass
class BeliefRevision:
    """Record of a belief revision (RbR event)"""
    id: str
    agent_id: str
    original_event_id: str
    revised_event_id: str
    trigger_evidence: str
    revision_reason: str
    confidence_change: float
    timestamp: datetime
    coherence_improvement: float

class SpannerGraphService:
    """
    Google Cloud Spanner Graph service for agent life-stories
    
    Implements CNE (Coherent Narrative Exclusivity) and RbR (Recursive Belief Revision)
    to maintain eA³ (Epistemic Autonomy, Accountability, Alignment).
    """
    
    def __init__(self, project_id: str, instance_id: str, database_id: str):
        self.project_id = project_id
        self.instance_id = instance_id
        self.database_id = database_id
        self.client = spanner.Client(project=project_id)
        self.instance = self.client.instance(instance_id)
        self.database = self.instance.database(database_id)
        
        # CNE thresholds
        self.coherence_threshold = 0.85  # Below this triggers narrative repair
        self.contradiction_threshold = 3  # Max contradictions before major revision
        
        # RbR parameters
        self.revision_window_hours = 24  # Look back window for revisions
        self.evidence_weight_threshold = 0.7  # Min evidence strength for revision
        
    async def initialize_database(self):
        """Initialize Spanner Graph database with agent life-story schema"""
        
        # Check if tables already exist
        if await self._tables_exist():
            logger.info("Spanner Graph database tables already exist, skipping initialization")
            return
        
        logger.info("Creating Spanner Graph database schema for agent life-stories...")
        
        # Define the graph schema for agent life-stories
        create_tables_ddl = [
            # Nodes: Story Events
            """
            CREATE TABLE StoryEvents (
                EventId STRING(36) NOT NULL,
                AgentId STRING(36) NOT NULL,
                EventType STRING(50) NOT NULL,
                Timestamp TIMESTAMP NOT NULL,
                Content STRING(MAX) NOT NULL,
                Context JSON,
                Confidence FLOAT64 NOT NULL,
                EvidenceSource STRING(255) NOT NULL,
                NarrativeImportance FLOAT64 DEFAULT (0.5),
                RevisionCount INT64 DEFAULT (0),
                IsCoreBeliefBool BOOL DEFAULT (FALSE),
                AlignmentScore FLOAT64 DEFAULT (1.0),
                CreatedAt TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP()),
                UpdatedAt TIMESTAMP NOT NULL DEFAULT (PENDING_COMMIT_TIMESTAMP()) OPTIONS (allow_commit_timestamp=true)
            ) PRIMARY KEY (AgentId, EventId)
            """,
            
            # Edges: Causal Relationships
            """
            CREATE TABLE CausalRelations (
                RelationId STRING(36) NOT NULL,
                AgentId STRING(36) NOT NULL,
                CauseEventId STRING(36) NOT NULL,
                EffectEventId STRING(36) NOT NULL,
                RelationType STRING(50) NOT NULL, -- 'causal', 'temporal', 'logical', 'contradictory'
                Strength FLOAT64 NOT NULL,
                Confidence FLOAT64 NOT NULL,
                CreatedAt TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP()),
                FOREIGN KEY (AgentId, CauseEventId) REFERENCES StoryEvents (AgentId, EventId),
                FOREIGN KEY (AgentId, EffectEventId) REFERENCES StoryEvents (AgentId, EventId)
            ) PRIMARY KEY (AgentId, RelationId)
            """,
            
            # Narrative Threads
            """
            CREATE TABLE NarrativeThreads (
                ThreadId STRING(36) NOT NULL,
                AgentId STRING(36) NOT NULL,
                Title STRING(255) NOT NULL,
                Description STRING(MAX),
                CoherenceScore FLOAT64 NOT NULL,
                Importance FLOAT64 NOT NULL,
                IsActive BOOL DEFAULT (TRUE),
                CreatedAt TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP()),
                LastUpdated TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP())
            ) PRIMARY KEY (AgentId, ThreadId)
            """,
            
            # Thread Events (Many-to-Many)
            """
            CREATE TABLE ThreadEvents (
                AgentId STRING(36) NOT NULL,
                ThreadId STRING(36) NOT NULL,
                EventId STRING(36) NOT NULL,
                SequenceOrder INT64 NOT NULL,
                FOREIGN KEY (AgentId, ThreadId) REFERENCES NarrativeThreads (AgentId, ThreadId),
                FOREIGN KEY (AgentId, EventId) REFERENCES StoryEvents (AgentId, EventId)
            ) PRIMARY KEY (AgentId, ThreadId, EventId)
            """,
            
            # Belief Revisions (RbR tracking)
            """
            CREATE TABLE BeliefRevisions (
                RevisionId STRING(36) NOT NULL,
                AgentId STRING(36) NOT NULL,
                OriginalEventId STRING(36) NOT NULL,
                RevisedEventId STRING(36) NOT NULL,
                TriggerEvidence STRING(MAX) NOT NULL,
                RevisionReason STRING(MAX) NOT NULL,
                ConfidenceChange FLOAT64 NOT NULL,
                CoherenceImprovement FLOAT64 NOT NULL,
                Timestamp TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP()),
                FOREIGN KEY (AgentId, OriginalEventId) REFERENCES StoryEvents (AgentId, EventId),
                FOREIGN KEY (AgentId, RevisedEventId) REFERENCES StoryEvents (AgentId, EventId)
            ) PRIMARY KEY (AgentId, RevisionId)
            """,
            
            # Agent Story Metadata
            """
            CREATE TABLE AgentStories (
                AgentId STRING(36) NOT NULL,
                StoryTitle STRING(255),
                CoreObjective STRING(MAX),
                OverallCoherence FLOAT64 DEFAULT (1.0),
                TotalEvents INT64 DEFAULT (0),
                TotalRevisions INT64 DEFAULT (0),
                LastRevisionAt TIMESTAMP OPTIONS (allow_commit_timestamp=true),
                StoryStartedAt TIMESTAMP NOT NULL DEFAULT (PENDING_COMMIT_TIMESTAMP()) OPTIONS (allow_commit_timestamp=true),
                LastUpdatedAt TIMESTAMP NOT NULL DEFAULT (PENDING_COMMIT_TIMESTAMP()) OPTIONS (allow_commit_timestamp=true)
            ) PRIMARY KEY (AgentId)
            """
        ]
        
        # Create indexes for efficient queries
        create_indexes_ddl = [
            "CREATE INDEX StoryEventsByTimestamp ON StoryEvents (AgentId, Timestamp DESC)",
            "CREATE INDEX StoryEventsByType ON StoryEvents (AgentId, EventType, Timestamp DESC)",
            "CREATE INDEX CausalRelationsByStrength ON CausalRelations (AgentId, Strength DESC)",
            "CREATE INDEX ThreadEventsBySequence ON ThreadEvents (AgentId, ThreadId, SequenceOrder)",
            "CREATE INDEX BeliefRevisionsByTimestamp ON BeliefRevisions (AgentId, Timestamp DESC)"
        ]
        
        # Execute DDL
        operation = self.database.update_ddl(create_tables_ddl + create_indexes_ddl)
        operation.result(timeout=300)  # Wait up to 5 minutes
        logger.info("Spanner Graph database initialized for agent life-stories")

    async def _tables_exist(self) -> bool:
        """Check if the required tables already exist in the database"""
        # Query the information schema to check for our main table
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = '' AND table_name = 'StoryEvents'"
            )
            tables = list(results)
            return len(tables) > 0

    async def create_agent_story(self, agent_id: str, core_objective: str, story_title: str = None) -> bool:
        """
        Initialize a new agent's life-story (CNE foundation)
        
        This is the agent's "birth" - the first event in their coherent narrative.
        """
        if not story_title:
            story_title = f"The Journey of Agent {agent_id}"
        
        birth_event = StoryEvent(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=StoryEventType.BIRTH,
            timestamp=datetime.now(),
            content=f"Agent {agent_id} was created with the core objective: {core_objective}",
            context={
                "core_objective": core_objective,
                "creation_method": "alchemist_platform",
                "initial_state": "tabula_rasa"
            },
            confidence=1.0,
            evidence_source="system_creation",
            narrative_importance=1.0,
            is_core_belief=True,
            alignment_score=1.0
        )
        
        goal_event = StoryEvent(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=StoryEventType.GOAL_SET,
            timestamp=datetime.now(),
            content=f"Primary goal established: {core_objective}",
            context={
                "goal_type": "primary_objective",
                "goal_source": "creator_specified",
                "goal_priority": 1.0
            },
            confidence=1.0,
            evidence_source="creator_specification",
            causal_parents=[birth_event.id],
            narrative_importance=1.0,
            is_core_belief=True,
            alignment_score=1.0
        )
        
        def create_story_txn(transaction):
            # Insert agent story metadata (StoryStartedAt and LastUpdatedAt will be set automatically)
            transaction.insert(
                table="AgentStories",
                columns=("AgentId", "StoryTitle", "CoreObjective", "TotalEvents"),
                values=[(agent_id, story_title, core_objective, 2)]
            )
            
            # Insert birth event
            transaction.insert(
                table="StoryEvents",
                columns=("EventId", "AgentId", "EventType", "Timestamp", "Content", "Context", 
                        "Confidence", "EvidenceSource", "NarrativeImportance", "IsCoreBeliefBool", "AlignmentScore"),
                values=[(birth_event.id, birth_event.agent_id, birth_event.event_type.value,
                        birth_event.timestamp, birth_event.content, json.dumps(birth_event.context),
                        birth_event.confidence, birth_event.evidence_source, birth_event.narrative_importance,
                        birth_event.is_core_belief, birth_event.alignment_score)]
            )
            
            # Insert goal event
            transaction.insert(
                table="StoryEvents",
                columns=("EventId", "AgentId", "EventType", "Timestamp", "Content", "Context", 
                        "Confidence", "EvidenceSource", "NarrativeImportance", "IsCoreBeliefBool", "AlignmentScore"),
                values=[(goal_event.id, goal_event.agent_id, goal_event.event_type.value,
                        goal_event.timestamp, goal_event.content, json.dumps(goal_event.context),
                        goal_event.confidence, goal_event.evidence_source, goal_event.narrative_importance,
                        goal_event.is_core_belief, goal_event.alignment_score)]
            )
            
            # Create causal relation (birth -> goal)
            transaction.insert(
                table="CausalRelations",
                columns=("RelationId", "AgentId", "CauseEventId", "EffectEventId", "RelationType", "Strength", "Confidence"),
                values=[(str(uuid.uuid4()), agent_id, birth_event.id, goal_event.id, "causal", 1.0, 1.0)]
            )
            
            # Create initial narrative thread
            main_thread_id = str(uuid.uuid4())
            transaction.insert(
                table="NarrativeThreads",
                columns=("ThreadId", "AgentId", "Title", "Description", "CoherenceScore", "Importance"),
                values=[(main_thread_id, agent_id, "Primary Journey", 
                        f"The main storyline of {agent_id}'s pursuit of their core objective", 1.0, 1.0)]
            )
            
            # Add events to thread
            for i, event in enumerate([birth_event, goal_event]):
                transaction.insert(
                    table="ThreadEvents",
                    columns=("AgentId", "ThreadId", "EventId", "SequenceOrder"),
                    values=[(agent_id, main_thread_id, event.id, i)]
                )
        
        self.database.run_in_transaction(create_story_txn)
        
        logger.info(f"Created life-story for agent {agent_id}: '{story_title}'")
        return True

    async def add_story_event(
        self, 
        agent_id: str, 
        event_type: StoryEventType,
        content: str,
        context: Dict[str, Any],
        evidence_source: str,
        confidence: float = 0.8,
        causal_parents: List[str] = None
    ) -> Tuple[str, bool]:
        """
        Add a new event to the agent's life-story with CNE enforcement
        
        Returns: (event_id, coherence_maintained)
        """
        if causal_parents is None:
            causal_parents = []
        
        event = StoryEvent(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=event_type,
            timestamp=datetime.now(),
            content=content,
            context=context,
            confidence=confidence,
            evidence_source=evidence_source,
            causal_parents=causal_parents,
            narrative_importance=await self._calculate_narrative_importance(agent_id, event_type, content),
            alignment_score=await self._calculate_alignment_score(agent_id, content, context)
        )
        
        # Check for contradictions BEFORE adding (CNE)
        contradictions = await self._detect_contradictions(agent_id, event)
        
        if contradictions:
            logger.warning(f"Agent {agent_id}: Contradictions detected for new event. Triggering RbR...")
            # Trigger Recursive Belief Revision
            revised_coherence = await self._perform_belief_revision(agent_id, event, contradictions)
            coherence_maintained = revised_coherence > self.coherence_threshold
        else:
            coherence_maintained = True
        
        # Add the event to the story
        def add_event_txn(transaction):
            # Insert the event
            transaction.insert(
                table="StoryEvents",
                columns=("EventId", "AgentId", "EventType", "Timestamp", "Content", "Context", 
                        "Confidence", "EvidenceSource", "NarrativeImportance", "AlignmentScore"),
                values=[(event.id, event.agent_id, event.event_type.value, event.timestamp,
                        event.content, json.dumps(event.context), event.confidence, event.evidence_source,
                        event.narrative_importance, event.alignment_score)]
            )
            
            # Add causal relations
            for parent_id in causal_parents:
                transaction.insert(
                    table="CausalRelations",
                    columns=("RelationId", "AgentId", "CauseEventId", "EffectEventId", "RelationType", "Strength", "Confidence"),
                    values=[(str(uuid.uuid4()), agent_id, parent_id, event.id, "causal", 0.8, confidence)]
                )
            
            # Update agent story metadata (LastUpdatedAt will be automatically set due to allow_commit_timestamp)
            transaction.execute_update(
                "UPDATE AgentStories SET TotalEvents = TotalEvents + 1 WHERE AgentId = @agent_id",
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            )
        
        self.database.run_in_transaction(add_event_txn)
        
        # Update narrative threads
        await self._update_narrative_threads(agent_id, event)
        
        logger.info(f"Added story event {event.id} for agent {agent_id}. Coherence maintained: {coherence_maintained}")
        return event.id, coherence_maintained

    async def _detect_contradictions(self, agent_id: str, new_event: StoryEvent) -> List[Dict[str, Any]]:
        """
        Detect contradictions with existing story (CNE enforcement)
        
        Uses Spanner Graph queries to find conflicting beliefs/actions
        """
        # Query for potentially contradictory events
        contradiction_query = """
        SELECT e.EventId, e.Content, e.Confidence, e.EventType, e.Timestamp
        FROM StoryEvents e
        WHERE e.AgentId = @agent_id
        AND e.EventType IN ('belief_formed', 'action_taken', 'goal_set')
        AND e.Timestamp > @lookback_time
        ORDER BY e.Confidence DESC
        """
        
        lookback_time = datetime.now() - timedelta(hours=self.revision_window_hours)
        
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                contradiction_query,
                params={"agent_id": agent_id, "lookback_time": lookback_time},
                param_types={"agent_id": param_types.STRING, "lookback_time": param_types.TIMESTAMP}
            )
        
        contradictions = []
        for row in results:
            existing_event = {
                "id": row[0],
                "content": row[1],
                "confidence": row[2],
                "event_type": row[3],
                "timestamp": row[4]
            }
            
            # Check for semantic contradictions
            contradiction_score = await self._calculate_contradiction_score(new_event.content, existing_event["content"])
            
            if contradiction_score > 0.7:  # High contradiction
                contradictions.append({
                    "existing_event": existing_event,
                    "contradiction_score": contradiction_score,
                    "type": "semantic_conflict"
                })
        
        return contradictions

    async def _perform_belief_revision(
        self, 
        agent_id: str, 
        new_event: StoryEvent, 
        contradictions: List[Dict[str, Any]]
    ) -> float:
        """
        Perform Recursive Belief Revision (RbR) to maintain coherence
        
        This is the core of epistemic autonomy - the agent revises its own beliefs
        when new evidence contradicts existing beliefs.
        """
        revisions_made = []
        
        for contradiction in contradictions:
            existing_event = contradiction["existing_event"]
            contradiction_score = contradiction["contradiction_score"]
            
            # Determine which event should be revised based on evidence strength
            new_evidence_weight = new_event.confidence * new_event.narrative_importance
            existing_evidence_weight = existing_event["confidence"]
            
            if new_evidence_weight > existing_evidence_weight * 1.2:  # New evidence is significantly stronger
                # Revise the existing event
                revised_content = await self._generate_revised_belief(
                    original_content=existing_event["content"],
                    new_evidence=new_event.content,
                    contradiction_type="evidence_override"
                )
                
                revision = await self._create_belief_revision(
                    agent_id=agent_id,
                    original_event_id=existing_event["id"],
                    new_content=revised_content,
                    trigger_evidence=new_event.content,
                    revision_reason=f"New evidence ({new_event.evidence_source}) contradicts previous belief",
                    confidence_change=new_evidence_weight - existing_evidence_weight
                )
                
                revisions_made.append(revision)
                
            elif existing_evidence_weight > new_evidence_weight * 1.2:  # Existing belief is much stronger
                # Modify the new event to be consistent
                revised_content = await self._generate_revised_belief(
                    original_content=new_event.content,
                    new_evidence=existing_event["content"],
                    contradiction_type="belief_reconciliation"
                )
                
                new_event.content = revised_content
                new_event.revision_count += 1
                
            else:
                # Similar strength - create a synthesis
                synthesized_content = await self._synthesize_conflicting_beliefs(
                    belief1=existing_event["content"],
                    belief2=new_event.content,
                    context=new_event.context
                )
                
                # Create a new synthesis event
                synthesis_event = StoryEvent(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    event_type=StoryEventType.BELIEF_REVISED,
                    timestamp=datetime.now(),
                    content=synthesized_content,
                    context={
                        "synthesis_of": [existing_event["id"], new_event.id],
                        "revision_reason": "belief_synthesis",
                        **new_event.context
                    },
                    confidence=(new_event.confidence + existing_event["confidence"]) / 2,
                    evidence_source="belief_synthesis",
                    narrative_importance=max(new_event.narrative_importance, 0.8)
                )
                
                # Add synthesis event
                await self.add_story_event(
                    agent_id=agent_id,
                    event_type=synthesis_event.event_type,
                    content=synthesis_event.content,
                    context=synthesis_event.context,
                    evidence_source=synthesis_event.evidence_source,
                    confidence=synthesis_event.confidence
                )
        
        # Calculate new coherence score
        new_coherence = await self._calculate_narrative_coherence(agent_id)
        
        # Record the revision in the database
        if revisions_made:
            def record_revisions_txn(transaction):
                for revision in revisions_made:
                    transaction.insert(
                        table="BeliefRevisions",
                        columns=("RevisionId", "AgentId", "OriginalEventId", "RevisedEventId", 
                                "TriggerEvidence", "RevisionReason", "ConfidenceChange", "CoherenceImprovement"),
                        values=[(revision.id, revision.agent_id, revision.original_event_id, 
                                revision.revised_event_id, revision.trigger_evidence, revision.revision_reason,
                                revision.confidence_change, revision.coherence_improvement)]
                    )
                
                # Update agent story metadata (LastRevisionAt will be automatically set due to allow_commit_timestamp)
                transaction.execute_update(
                    "UPDATE AgentStories SET TotalRevisions = TotalRevisions + @revision_count WHERE AgentId = @agent_id",
                    params={"agent_id": agent_id, "revision_count": len(revisions_made)},
                    param_types={"agent_id": param_types.STRING, "revision_count": param_types.INT64}
                )
            
            self.database.run_in_transaction(record_revisions_txn)
        
        logger.info(f"Agent {agent_id}: Performed {len(revisions_made)} belief revisions. New coherence: {new_coherence:.3f}")
        return new_coherence

    async def get_agent_story_summary(self, agent_id: str, include_revisions: bool = True) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the agent's life-story for accountability
        
        This provides the "explain yourself" capability - full narrative trace
        """
        # Get story metadata
        metadata_query = """
        SELECT StoryTitle, CoreObjective, OverallCoherence, TotalEvents, 
               TotalRevisions, StoryStartedAt, LastUpdatedAt
        FROM AgentStories 
        WHERE AgentId = @agent_id
        """
        
        # Get recent events
        events_query = """
        SELECT EventId, EventType, Timestamp, Content, Confidence, 
               NarrativeImportance, AlignmentScore, RevisionCount
        FROM StoryEvents 
        WHERE AgentId = @agent_id 
        ORDER BY Timestamp DESC 
        LIMIT 50
        """
        
        # Get narrative threads
        threads_query = """
        SELECT t.ThreadId, t.Title, t.Description, t.CoherenceScore, t.Importance,
               ARRAY(
                   SELECT STRUCT(e.EventId, e.Content, e.Timestamp, te.SequenceOrder)
                   FROM ThreadEvents te
                   JOIN StoryEvents e ON te.EventId = e.EventId AND te.AgentId = e.AgentId
                   WHERE te.AgentId = @agent_id AND te.ThreadId = t.ThreadId
                   ORDER BY te.SequenceOrder
               ) as Events
        FROM NarrativeThreads t
        WHERE t.AgentId = @agent_id AND t.IsActive = TRUE
        ORDER BY t.Importance DESC
        """
        
        with self.database.snapshot() as snapshot:
            # Get metadata
            metadata_result = list(snapshot.execute_sql(
                metadata_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))
            
            if not metadata_result:
                return {"error": f"No story found for agent {agent_id}"}
            
            metadata = metadata_result[0]
            
            # Get events
            events_result = list(snapshot.execute_sql(
                events_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))
            
            # Get threads
            threads_result = list(snapshot.execute_sql(
                threads_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))
        
        # Get revisions if requested
        revisions = []
        if include_revisions:
            revisions_query = """
            SELECT RevisionId, OriginalEventId, RevisedEventId, TriggerEvidence,
                   RevisionReason, ConfidenceChange, CoherenceImprovement, Timestamp
            FROM BeliefRevisions
            WHERE AgentId = @agent_id
            ORDER BY Timestamp DESC
            LIMIT 20
            """
            
            with self.database.snapshot() as snapshot:
                revisions_result = list(snapshot.execute_sql(
                    revisions_query,
                    params={"agent_id": agent_id},
                    param_types={"agent_id": param_types.STRING}
                ))
                
                revisions = [
                    {
                        "revision_id": row[0],
                        "original_event_id": row[1],
                        "revised_event_id": row[2],
                        "trigger_evidence": row[3],
                        "revision_reason": row[4],
                        "confidence_change": row[5],
                        "coherence_improvement": row[6],
                        "timestamp": row[7].isoformat()
                    }
                    for row in revisions_result
                ]
        
        return {
            "agent_id": agent_id,
            "story_metadata": {
                "title": metadata[0],
                "core_objective": metadata[1],
                "overall_coherence": metadata[2],
                "total_events": metadata[3],
                "total_revisions": metadata[4],
                "story_started": metadata[5].isoformat(),
                "last_updated": metadata[6].isoformat()
            },
            "recent_events": [
                {
                    "event_id": row[0],
                    "event_type": row[1],
                    "timestamp": row[2].isoformat(),
                    "content": row[3],
                    "confidence": row[4],
                    "narrative_importance": row[5],
                    "alignment_score": row[6],
                    "revision_count": row[7]
                }
                for row in events_result
            ],
            "narrative_threads": [
                {
                    "thread_id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "coherence_score": row[3],
                    "importance": row[4],
                    "events": [
                        {
                            "event_id": event.get("EventId"),
                            "content": event.get("Content"),
                            "timestamp": event.get("Timestamp").isoformat() if event.get("Timestamp") else None,
                            "sequence_order": event.get("SequenceOrder")
                        }
                        for event in (row[5] or [])
                    ]
                }
                for row in threads_result
            ],
            "belief_revisions": revisions,
            "eA3_assessment": await self._assess_ea3_status(agent_id)
        }

    async def _assess_ea3_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Assess the agent's eA³ status: Epistemic Autonomy, Accountability, Alignment
        """
        # Epistemic Autonomy: Can the agent revise its own beliefs?
        autonomy_query = """
        SELECT COUNT(*) as AutoRevisions
        FROM BeliefRevisions
        WHERE AgentId = @agent_id
        AND RevisionReason LIKE '%autonomous%' OR RevisionReason LIKE '%self%'
        """
        
        # Accountability: How traceable are the agent's decisions?
        accountability_query = """
        SELECT AVG(NarrativeImportance) as AvgTraceability,
               COUNT(*) as TotalTraceableEvents
        FROM StoryEvents
        WHERE AgentId = @agent_id
        AND NarrativeImportance > 0.5
        """
        
        # Alignment: How well do actions align with core objectives?
        alignment_query = """
        SELECT AVG(AlignmentScore) as AvgAlignment,
               COUNT(*) as TotalEvents
        FROM StoryEvents
        WHERE AgentId = @agent_id
        """
        
        with self.database.snapshot() as snapshot:
            autonomy_result = list(snapshot.execute_sql(
                autonomy_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))[0]
            
            accountability_result = list(snapshot.execute_sql(
                accountability_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))[0]
            
            alignment_result = list(snapshot.execute_sql(
                alignment_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))[0]
        
        # Calculate overall coherence
        coherence = await self._calculate_narrative_coherence(agent_id)
        
        return {
            "epistemic_autonomy": {
                "score": min(1.0, autonomy_result[0] / 10.0),  # Normalize to 0-1
                "autonomous_revisions": autonomy_result[0],
                "status": "autonomous" if autonomy_result[0] > 0 else "dependent"
            },
            "accountability": {
                "score": accountability_result[0] or 0.0,
                "traceable_events": accountability_result[1],
                "status": "highly_accountable" if (accountability_result[0] or 0) > 0.8 else "moderately_accountable"
            },
            "alignment": {
                "score": alignment_result[0] or 0.0,
                "total_events": alignment_result[1],
                "status": "well_aligned" if (alignment_result[0] or 0) > 0.9 else "needs_alignment"
            },
            "narrative_coherence": {
                "score": coherence,
                "status": self._get_coherence_status(coherence)
            },
            "overall_ea3_score": (
                (autonomy_result[0] / 10.0) * 0.3 +
                (accountability_result[0] or 0.0) * 0.3 +
                (alignment_result[0] or 0.0) * 0.3 +
                coherence * 0.1
            )
        }

    def _get_coherence_status(self, coherence: float) -> str:
        """Get coherence status based on score"""
        if coherence >= 0.9:
            return "perfectly_coherent"
        elif coherence >= 0.8:
            return "mostly_coherent"
        elif coherence >= 0.6:
            return "moderately_coherent"
        else:
            return "needs_revision"

    # Helper methods for various calculations
    async def _calculate_narrative_importance(self, agent_id: str, event_type: StoryEventType, content: str) -> float:
        """Calculate how important this event is to the overall narrative"""
        # Core beliefs and goals are always important
        if event_type in [StoryEventType.BIRTH, StoryEventType.GOAL_SET, StoryEventType.BELIEF_REVISED]:
            return 1.0
        
        # Actions and evidence importance depends on content
        if event_type in [StoryEventType.ACTION_TAKEN, StoryEventType.EVIDENCE_RECEIVED]:
            # Simple heuristic: longer content = more important
            return min(1.0, len(content) / 500.0 + 0.3)
        
        return 0.5  # Default importance

    async def _calculate_alignment_score(self, agent_id: str, content: str, context: Dict[str, Any]) -> float:
        """Calculate how well this event aligns with the agent's core objectives"""
        # Get the agent's core objective
        core_objective_query = """
        SELECT CoreObjective FROM AgentStories WHERE AgentId = @agent_id
        """
        
        with self.database.snapshot() as snapshot:
            result = list(snapshot.execute_sql(
                core_objective_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))
        
        if not result:
            return 0.5  # Default if no core objective found
        
        core_objective = result[0][0]
        
        # Simple semantic similarity (in production, use proper NLP)
        content_words = set(content.lower().split())
        objective_words = set(core_objective.lower().split())
        
        if not objective_words:
            return 0.5
        
        overlap = len(content_words.intersection(objective_words))
        similarity = overlap / len(objective_words)
        
        # Boost score if context indicates goal-directed behavior
        if context.get("goal_directed", False):
            similarity += 0.2
        
        return min(1.0, similarity)

    async def _calculate_contradiction_score(self, content1: str, content2: str) -> float:
        """Calculate semantic contradiction between two pieces of content"""
        # Simplified contradiction detection
        # In production, use proper NLP/semantic analysis
        
        # Look for direct negations
        negation_words = ["not", "no", "never", "cannot", "won't", "don't", "isn't", "aren't"]
        
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        # Check for negation patterns
        for word in words1:
            if word in negation_words:
                # Look for the negated concept in the other content
                remaining_words = words1 - {word}
                if remaining_words.intersection(words2):
                    return 0.8  # High contradiction
        
        # Check for opposite concepts (simplified)
        opposites = {
            "true": "false", "false": "true", "yes": "no", "no": "yes",
            "good": "bad", "bad": "good", "positive": "negative", "negative": "positive"
        }
        
        for word1 in words1:
            if word1 in opposites and opposites[word1] in words2:
                return 0.9  # Very high contradiction
        
        # Check for semantic overlap (lower contradiction if similar content)
        overlap = len(words1.intersection(words2))
        if overlap > 0:
            return max(0.0, 0.3 - (overlap / max(len(words1), len(words2))))
        
        return 0.1  # Low contradiction by default

    async def _generate_revised_belief(self, original_content: str, new_evidence: str, contradiction_type: str) -> str:
        """Generate a revised belief that reconciles contradiction"""
        # Simplified belief revision (in production, use LLM)
        if contradiction_type == "evidence_override":
            return f"Updated belief: {new_evidence} (revised from: {original_content[:50]}...)"
        elif contradiction_type == "belief_reconciliation":
            return f"Reconciled belief: {original_content} considering {new_evidence[:30]}..."
        else:
            return f"Synthesized belief incorporating both {original_content[:30]}... and {new_evidence[:30]}..."

    async def _synthesize_conflicting_beliefs(self, belief1: str, belief2: str, context: Dict[str, Any]) -> str:
        """Synthesize two conflicting beliefs into a coherent narrative"""
        # Simplified synthesis (in production, use LLM)
        return f"Synthesis: {belief1[:50]}... and {belief2[:50]}... can both be true under different conditions"

    async def _create_belief_revision(
        self, 
        agent_id: str, 
        original_event_id: str, 
        new_content: str,
        trigger_evidence: str, 
        revision_reason: str, 
        confidence_change: float
    ) -> BeliefRevision:
        """Create a belief revision record"""
        
        # Create new revised event
        revised_event_id = str(uuid.uuid4())
        
        # This would update the original event with new content
        # For now, creating a new event to track the revision
        
        return BeliefRevision(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            original_event_id=original_event_id,
            revised_event_id=revised_event_id,
            trigger_evidence=trigger_evidence,
            revision_reason=revision_reason,
            confidence_change=confidence_change,
            timestamp=datetime.now(),
            coherence_improvement=0.1  # Simplified calculation
        )

    async def _calculate_narrative_coherence(self, agent_id: str) -> float:
        """Calculate overall narrative coherence for the agent"""
        # Get all events and their relationships
        coherence_query = """
        WITH EventCoherence AS (
            SELECT 
                e.EventId,
                e.Confidence,
                e.AlignmentScore,
                COUNT(DISTINCT cr.RelationId) as ConnectionCount
            FROM StoryEvents e
            LEFT JOIN CausalRelations cr ON 
                (e.EventId = cr.CauseEventId OR e.EventId = cr.EffectEventId)
                AND e.AgentId = cr.AgentId
            WHERE e.AgentId = @agent_id
            GROUP BY e.EventId, e.Confidence, e.AlignmentScore
        )
        SELECT 
            AVG(Confidence * AlignmentScore) as WeightedCoherence,
            AVG(CASE WHEN ConnectionCount > 0 THEN 1.0 ELSE 0.5 END) as ConnectionScore,
            COUNT(*) as TotalEvents
        FROM EventCoherence
        """
        
        with self.database.snapshot() as snapshot:
            result = list(snapshot.execute_sql(
                coherence_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))
        
        if not result or not result[0][2]:  # No events
            return 1.0
        
        weighted_coherence = result[0][0] or 0.5
        connection_score = result[0][1] or 0.5
        
        # Combine coherence metrics
        overall_coherence = (weighted_coherence * 0.7) + (connection_score * 0.3)
        
        return min(1.0, max(0.0, overall_coherence))

    async def _update_narrative_threads(self, agent_id: str, event: StoryEvent):
        """Update narrative threads with the new event"""
        # Simplified thread assignment
        # In production, use semantic analysis to determine which threads this event belongs to
        
        # For now, add to the main thread
        main_thread_query = """
        SELECT ThreadId FROM NarrativeThreads 
        WHERE AgentId = @agent_id AND Title = 'Primary Journey'
        LIMIT 1
        """
        
        with self.database.snapshot() as snapshot:
            result = list(snapshot.execute_sql(
                main_thread_query,
                params={"agent_id": agent_id},
                param_types={"agent_id": param_types.STRING}
            ))
        
        if result:
            thread_id = result[0][0]
            
            # Get the next sequence order
            sequence_query = """
            SELECT MAX(SequenceOrder) FROM ThreadEvents 
            WHERE AgentId = @agent_id AND ThreadId = @thread_id
            """
            
            with self.database.snapshot() as snapshot:
                sequence_result = list(snapshot.execute_sql(
                    sequence_query,
                    params={"agent_id": agent_id, "thread_id": thread_id},
                    param_types={"agent_id": param_types.STRING, "thread_id": param_types.STRING}
                ))
            
            next_sequence = (sequence_result[0][0] or 0) + 1
            
            # Add event to thread
            def add_to_thread_txn(transaction):
                transaction.insert(
                    table="ThreadEvents",
                    columns=("AgentId", "ThreadId", "EventId", "SequenceOrder"),
                    values=[(agent_id, thread_id, event.id, next_sequence)]
                )
            
            self.database.run_in_transaction(add_to_thread_txn)

    async def get_coherence_trends(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical coherence trend data for the agent"""
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Query to get coherence metrics over time
            trends_query = """
            WITH TimeSlots AS (
                SELECT 
                    TIMESTAMP_TRUNC(Timestamp, HOUR) as TimeSlot,
                    AVG(Confidence * AlignmentScore) as CoherenceScore,
                    AVG(AlignmentScore) as ConsistencyScore,
                    COUNT(*) as EventCount
                FROM StoryEvents 
                WHERE AgentId = @agent_id 
                    AND Timestamp >= @cutoff_time
                GROUP BY TimeSlot
                ORDER BY TimeSlot DESC
            )
            SELECT 
                TimeSlot,
                CoherenceScore,
                ConsistencyScore,
                EventCount
            FROM TimeSlots
            ORDER BY TimeSlot ASC
            """
            
            with self.database.snapshot() as snapshot:
                results = list(snapshot.execute_sql(
                    trends_query,
                    params={
                        "agent_id": agent_id,
                        "cutoff_time": cutoff_time
                    },
                    param_types={
                        "agent_id": param_types.STRING,
                        "cutoff_time": param_types.TIMESTAMP
                    }
                ))
            
            trends = []
            for row in results:
                trends.append({
                    "timestamp": row[0].isoformat() if row[0] else "",
                    "coherence_score": float(row[1]) if row[1] else 0.0,
                    "consistency_score": float(row[2]) if row[2] else 0.0,
                    "event_count": int(row[3]) if row[3] else 0
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get coherence trends for agent {agent_id}: {e}")
            return []

    async def get_narrative_conflicts(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get active narrative conflicts for the agent"""
        try:
            # Query to find contradictory events and beliefs
            conflicts_query = """
            WITH ConflictEvents AS (
                SELECT DISTINCT
                    e1.EventId as Event1Id,
                    e2.EventId as Event2Id,
                    e1.Content as Event1Content,
                    e2.Content as Event2Content,
                    e1.Timestamp as Event1Time,
                    e2.Timestamp as Event2Time,
                    e1.Confidence as Event1Confidence,
                    e2.Confidence as Event2Confidence,
                    ABS(e1.AlignmentScore - e2.AlignmentScore) as AlignmentDiff
                FROM StoryEvents e1
                JOIN StoryEvents e2 ON e1.AgentId = e2.AgentId
                WHERE e1.AgentId = @agent_id
                    AND e1.EventId != e2.EventId
                    AND e1.EventType IN ('belief_formed', 'belief_revised')
                    AND e2.EventType IN ('belief_formed', 'belief_revised')
                    AND ABS(e1.AlignmentScore - e2.AlignmentScore) > 0.3
                    AND e1.Timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            )
            SELECT 
                Event1Id,
                Event2Id,
                Event1Content,
                Event2Content,
                Event1Time,
                Event2Time,
                AlignmentDiff
            FROM ConflictEvents
            ORDER BY AlignmentDiff DESC
            LIMIT 10
            """
            
            with self.database.snapshot() as snapshot:
                results = list(snapshot.execute_sql(
                    conflicts_query,
                    params={"agent_id": agent_id},
                    param_types={"agent_id": param_types.STRING}
                ))
            
            conflicts = []
            for i, row in enumerate(results):
                impact_score = float(row[6]) if row[6] else 0.0
                conflicts.append({
                    "conflict_id": f"conflict_{agent_id}_{i+1}",
                    "conflict_type": "belief_contradiction",
                    "description": f"Conflicting beliefs detected between events: '{row[2][:100]}...' and '{row[3][:100]}...'",
                    "timestamp": row[4].isoformat() if row[4] else "",
                    "impact_score": impact_score,
                    "status": "pending" if impact_score > 0.5 else "resolved",
                    "event1_id": row[0],
                    "event2_id": row[1]
                })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to get narrative conflicts for agent {agent_id}: {e}")
            return []


# Service initialization and singleton access
_spanner_graph_service = None

async def init_spanner_graph_service(
    project_id: str,
    instance_id: str = "alchemist-graph",
    database_id: str = "agent-stories"
) -> SpannerGraphService:
    """Initialize the Spanner Graph service"""
    global _spanner_graph_service
    
    _spanner_graph_service = SpannerGraphService(project_id, instance_id, database_id)
    
    # Initialize database schema
    await _spanner_graph_service.initialize_database()
    
    logger.info(f"Spanner Graph service initialized for project {project_id}")
    return _spanner_graph_service

async def get_spanner_graph_service() -> SpannerGraphService:
    """Get the global Spanner Graph service instance"""
    if _spanner_graph_service is None:
        raise RuntimeError("Spanner Graph service not initialized. Call init_spanner_graph_service() first.")
    
    return _spanner_graph_service