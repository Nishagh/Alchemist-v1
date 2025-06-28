"""
eA³ Orchestrator Service

Orchestrates Epistemic Autonomy (eA³) by integrating CNE and RbR with the existing platform.
This service acts as the bridge between Alchemist's conversation system and the 
agent life-story management in Spanner Graph.

Key Functions:
- Converts conversations into story events
- Triggers RbR when contradictions are detected
- Provides accountability traces for all agent decisions
- Maintains alignment through continuous narrative coherence checking
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import openai

# Import story event system
try:
    from ..events import (
        StoryEvent, StoryEventType, StoryEventSubscriber, 
        StoryContextCache, CachedStoryContext
    )
    STORY_EVENTS_AVAILABLE = True
except ImportError:
    logging.warning("Story event system not available")
    STORY_EVENTS_AVAILABLE = False

from .spanner_graph_service import (
    SpannerGraphService, StoryEventType, get_spanner_graph_service,
    NarrativeCoherence
)

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Context for converting conversations to story events"""
    agent_id: str
    user_message: str
    agent_response: str
    conversation_id: str
    user_id: Optional[str] = None
    timestamp: datetime = None
    confidence: float = 0.8
    metadata: Dict[str, Any] = None

@dataclass
class EA3Assessment:
    """Assessment of agent's eA³ status"""
    agent_id: str
    epistemic_autonomy_score: float
    accountability_score: float
    alignment_score: float
    overall_coherence: float
    last_revision_count: int
    recommendation: str

class EA3Orchestrator:
    """
    Orchestrates eA³ (Epistemic Autonomy, Accountability, Alignment) for Alchemist agents
    
    This service integrates with the existing Alchemist platform to provide:
    1. CNE (Coherent Narrative Exclusivity) - One consistent life-story per agent
    2. RbR (Recursive Belief Revision) - Automatic belief updating when contradictions arise
    3. Full accountability traces - "Explain yourself" capability for any agent decision
    """
    
    def __init__(self):
        self.graph_service: Optional[SpannerGraphService] = None
        self.coherence_threshold = 0.85
        self.revision_trigger_threshold = 0.7
        self.narrative_model = "gpt-4-1106-preview"  # GPT-4.1 for enhanced narrative intelligence
        
        # Story event system integration
        self.story_subscriber: Optional[StoryEventSubscriber] = None
        self.story_cache: Optional[StoryContextCache] = None
        self.event_processing_enabled = False
        
    async def initialize(
        self, 
        project_id: str, 
        instance_id: str = "alchemist-graph", 
        database_id: str = "agent-stories",
        redis_url: Optional[str] = None,
        enable_event_processing: bool = True
    ):
        """Initialize the eA³ orchestrator with Spanner Graph backend and story event system"""
        try:
            # Initialize Spanner Graph service
            from .spanner_graph_service import init_spanner_graph_service
            self.graph_service = await init_spanner_graph_service(project_id, instance_id, database_id)
            logger.info("eA³ Orchestrator initialized with Spanner Graph backend")
            
            # Initialize story event system if available
            if enable_event_processing and STORY_EVENTS_AVAILABLE:
                # Initialize story context cache
                from ..events import init_story_context_cache
                self.story_cache = init_story_context_cache(redis_url)
                
                # Initialize story event subscriber
                self.story_subscriber = StoryEventSubscriber(
                    project_id=project_id,
                    subscription_name="ea3-orchestrator-events",
                    topic_name="agent-story-events"
                )
                
                # Register event handlers
                self._setup_event_handlers()
                
                # Start listening for events
                self.event_processing_enabled = True
                asyncio.create_task(self._start_event_processing())
                
                logger.info("eA³ story event processing enabled")
            else:
                logger.info("eA³ story event processing disabled or unavailable")
                
        except Exception as e:
            logger.error(f"Failed to initialize eA³ Orchestrator: {e}")
            raise

    async def create_agent_life_story(
        self, 
        agent_id: str, 
        core_objective: str, 
        agent_config: Dict[str, Any]
    ) -> bool:
        """
        Initialize a new agent's life-story when the agent is created
        
        This establishes the foundation for CNE - the agent's singular, coherent narrative
        """
        if not self.graph_service:
            logger.error("Graph service not initialized")
            return False
        
        try:
            # Extract story title from agent config
            story_title = f"The Journey of {agent_config.get('name', agent_id)}"
            
            # Create the foundational life-story
            success = await self.graph_service.create_agent_story(
                agent_id=agent_id,
                core_objective=core_objective,
                story_title=story_title
            )
            
            if success:
                logger.info(f"Created life-story for agent {agent_id}: '{story_title}'")
                
                # Add initial context events from agent configuration
                await self._add_configuration_events(agent_id, agent_config)
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to create life-story for agent {agent_id}: {e}")
            return False

    async def process_conversation(self, context: ConversationContext) -> Tuple[bool, EA3Assessment]:
        """
        Process a conversation and integrate it into the agent's life-story
        
        This is where conversations become part of the agent's narrative, with automatic
        CNE enforcement and RbR triggering if contradictions are detected.
        """
        if not self.graph_service:
            logger.error("Graph service not initialized")
            return False, None
        
        try:
            # Analyze the conversation for story-worthy events
            story_events = await self._extract_story_events_from_conversation(context)
            
            coherence_maintained = True
            revision_triggered = False
            
            # Add each story event to the agent's narrative
            for event_data in story_events:
                event_id, event_coherence = await self.graph_service.add_story_event(
                    agent_id=context.agent_id,
                    event_type=event_data["event_type"],
                    content=event_data["content"],
                    context=event_data["context"],
                    evidence_source=f"conversation_{context.conversation_id}",
                    confidence=event_data.get("confidence", context.confidence),
                    causal_parents=event_data.get("causal_parents", [])
                )
                
                if not event_coherence:
                    coherence_maintained = False
                    revision_triggered = True
                    logger.warning(f"Agent {context.agent_id}: Conversation triggered belief revision")
            
            # Assess the agent's current eA³ status
            ea3_assessment = await self._assess_agent_ea3(context.agent_id)
            
            # Log the conversation integration
            logger.info(
                f"Agent {context.agent_id}: Processed conversation with {len(story_events)} events. "
                f"Coherence maintained: {coherence_maintained}, Revision triggered: {revision_triggered}"
            )
            
            return coherence_maintained, ea3_assessment
            
        except Exception as e:
            logger.error(f"Failed to process conversation for agent {context.agent_id}: {e}")
            return False, None

    async def trigger_autonomous_reflection(self, agent_id: str, trigger_reason: str) -> bool:
        """
        Trigger autonomous self-reflection for the agent
        
        This implements the "recursive" part of RbR - the agent examines its own story
        and revises beliefs autonomously based on accumulated evidence.
        """
        if not self.graph_service:
            return False
        
        try:
            # Get the agent's recent story events for reflection
            story_summary = await self.graph_service.get_agent_story_summary(
                agent_id=agent_id, 
                include_revisions=True
            )
            
            # Analyze for potential inconsistencies
            reflection_content = await self._generate_reflection_content(story_summary, trigger_reason)
            
            # Add self-reflection event to the story
            reflection_id, coherence_maintained = await self.graph_service.add_story_event(
                agent_id=agent_id,
                event_type=StoryEventType.REFLECTION_PERFORMED,
                content=reflection_content,
                context={
                    "trigger_reason": trigger_reason,
                    "reflection_type": "autonomous",
                    "story_events_analyzed": len(story_summary.get("recent_events", [])),
                    "revisions_considered": len(story_summary.get("belief_revisions", []))
                },
                evidence_source="autonomous_reflection",
                confidence=0.9
            )
            
            logger.info(f"Agent {agent_id}: Completed autonomous reflection. Event ID: {reflection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed autonomous reflection for agent {agent_id}: {e}")
            return False

    async def get_accountability_trace(self, agent_id: str, decision_context: str = None) -> Dict[str, Any]:
        """
        Generate a complete accountability trace for the agent
        
        This provides the "explain yourself" capability - a full narrative trace
        showing how the agent arrived at its current state or a specific decision.
        """
        if not self.graph_service:
            return {"error": "Graph service not available"}
        
        try:
            # Get comprehensive story summary
            story_summary = await self.graph_service.get_agent_story_summary(
                agent_id=agent_id,
                include_revisions=True
            )
            
            if "error" in story_summary:
                return story_summary
            
            # Generate accountability narrative
            accountability_trace = {
                "agent_id": agent_id,
                "trace_generated_at": datetime.now().isoformat(),
                "decision_context": decision_context,
                "life_story_summary": story_summary,
                "accountability_analysis": await self._generate_accountability_analysis(story_summary),
                "coherence_report": await self._generate_coherence_report(agent_id),
                "alignment_verification": await self._verify_alignment(story_summary),
                "revision_history": self._format_revision_history(story_summary.get("belief_revisions", [])),
                "ea3_status": story_summary.get("eA3_assessment", {})
            }
            
            logger.info(f"Generated accountability trace for agent {agent_id}")
            return accountability_trace
            
        except Exception as e:
            logger.error(f"Failed to generate accountability trace for agent {agent_id}: {e}")
            return {"error": f"Failed to generate trace: {str(e)}"}

    async def check_alignment_drift(self, agent_id: str) -> Dict[str, Any]:
        """
        Check if the agent is drifting from its core objectives
        
        This is key for maintaining the "Alignment" part of eA³
        """
        if not self.graph_service:
            return {"error": "Graph service not available"}
        
        try:
            # Get story summary to analyze alignment
            story_summary = await self.graph_service.get_agent_story_summary(agent_id)
            
            if "error" in story_summary:
                return story_summary
            
            ea3_status = story_summary.get("eA3_assessment", {})
            alignment_info = ea3_status.get("alignment", {})
            
            current_alignment_score = alignment_info.get("score", 0.0)
            
            # Analyze recent events for alignment trends
            recent_events = story_summary.get("recent_events", [])
            
            if len(recent_events) >= 5:
                recent_alignment_scores = [event.get("alignment_score", 0.5) for event in recent_events[:5]]
                trend = self._calculate_alignment_trend(recent_alignment_scores)
                
                drift_detected = (
                    current_alignment_score < 0.8 or 
                    trend < -0.1 or 
                    any(score < 0.6 for score in recent_alignment_scores)
                )
                
                return {
                    "agent_id": agent_id,
                    "alignment_status": alignment_info.get("status", "unknown"),
                    "current_score": current_alignment_score,
                    "trend": trend,
                    "drift_detected": drift_detected,
                    "recommendation": self._get_alignment_recommendation(current_alignment_score, trend, drift_detected),
                    "recent_alignment_scores": recent_alignment_scores
                }
            else:
                return {
                    "agent_id": agent_id,
                    "alignment_status": "insufficient_data",
                    "current_score": current_alignment_score,
                    "message": "Need more interactions to assess alignment trends"
                }
                
        except Exception as e:
            logger.error(f"Failed to check alignment drift for agent {agent_id}: {e}")
            return {"error": f"Failed to check alignment: {str(e)}"}

    async def force_narrative_coherence_check(self, agent_id: str) -> Dict[str, Any]:
        """
        Force a comprehensive narrative coherence check (CNE enforcement)
        
        This manually triggers the coherence checking that normally happens automatically
        """
        if not self.graph_service:
            return {"error": "Graph service not available"}
        
        try:
            # Get current coherence score
            coherence_score = await self.graph_service._calculate_narrative_coherence(agent_id)
            
            # Get story summary for analysis
            story_summary = await self.graph_service.get_agent_story_summary(agent_id, include_revisions=True)
            
            coherence_status = self.graph_service._get_coherence_status(coherence_score)
            
            # Enhanced GPT-4.1 narrative analysis
            gpt41_analysis = await self.enhance_narrative_coherence_with_gpt41(
                agent_id, 
                story_summary, 
                context="coherence_check"
            )
            
            # Combine traditional and AI-enhanced analysis
            enhanced_coherence_score = max(
                coherence_score, 
                gpt41_analysis.get("coherence_score", coherence_score)
            )
            
            # Determine if intervention is needed (using enhanced score)
            needs_intervention = enhanced_coherence_score < self.coherence_threshold
            
            intervention_recommendation = None
            if needs_intervention:
                # Use GPT-4.1 recommendations if available
                intervention_recommendation = {
                    "traditional": await self._recommend_coherence_intervention(agent_id, story_summary),
                    "ai_enhanced": {
                        "cne_recommendations": gpt41_analysis.get("cne_recommendations", []),
                        "rbr_recommendations": gpt41_analysis.get("rbr_recommendations", []),
                        "umwelt_guidance": gpt41_analysis.get("umwelt_assessment", {}),
                        "gnf_integration": gpt41_analysis.get("gnf_integration", {}),
                        "priority": gpt41_analysis.get("enhancement_priority", "medium")
                    }
                }
            
            return {
                "agent_id": agent_id,
                "coherence_score": coherence_score,
                "enhanced_coherence_score": enhanced_coherence_score,
                "coherence_status": coherence_status,
                "threshold": self.coherence_threshold,
                "needs_intervention": needs_intervention,
                "intervention_recommendation": intervention_recommendation,
                "recent_revisions": len(story_summary.get("belief_revisions", [])),
                "narrative_threads": len(story_summary.get("narrative_threads", [])),
                "total_events": story_summary.get("story_metadata", {}).get("total_events", 0),
                "gpt41_analysis": gpt41_analysis,
                "narrative_intelligence": {
                    "umwelt_consistency": gpt41_analysis.get("umwelt_assessment", {}).get("consistency_score", 0.5),
                    "gnf_alignment": gpt41_analysis.get("gnf_integration", {}).get("alignment_score", 0.5),
                    "contradictions_detected": len(gpt41_analysis.get("contradictions_found", [])),
                    "narrative_health": gpt41_analysis.get("narrative_health", "unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed coherence check for agent {agent_id}: {e}")
            return {"error": f"Failed coherence check: {str(e)}"}

    async def enhance_narrative_coherence_with_gpt41(
        self, 
        agent_id: str, 
        story_summary: Dict[str, Any],
        context: str = "general_analysis"
    ) -> Dict[str, Any]:
        """
        Use GPT-4.1 for advanced narrative coherence analysis and enhancement
        
        This method leverages the advanced reasoning capabilities of GPT-4.1 to:
        1. Analyze narrative consistency across the agent's life-story
        2. Identify subtle contradictions that rule-based systems might miss
        3. Suggest coherent ways to resolve belief conflicts
        4. Enhance Umwelt (agent's perceptual world) modeling
        5. Strengthen GNF (Global Narrative Framework) integration
        """
        try:
            # Extract key narrative elements
            recent_events = story_summary.get("recent_events", [])
            narrative_threads = story_summary.get("narrative_threads", [])
            belief_revisions = story_summary.get("belief_revisions", [])
            core_objective = story_summary.get("story_metadata", {}).get("core_objective", "")
            
            # Construct comprehensive narrative analysis prompt
            prompt = f"""
You are an expert narrative intelligence system analyzing an AI agent's life-story for coherence and consistency.

AGENT CONTEXT:
- Agent ID: {agent_id}
- Core Objective: {core_objective}
- Analysis Context: {context}

NARRATIVE FRAMEWORK CONCEPTS:
1. CNE (Coherent Narrative Exclusivity): The agent must maintain ONE consistent life-story without contradictions
2. RbR (Recursive Belief Revision): When contradictions arise, beliefs should be updated systematically  
3. Umwelt: The agent's perceptual world and how it interprets experiences
4. GNF (Global Narrative Framework): How this agent's story fits within the larger system narrative

CURRENT STORY STATE:
Recent Events: {json.dumps(recent_events[:10], indent=2)}

Narrative Threads: {json.dumps(narrative_threads, indent=2)}

Recent Belief Revisions: {json.dumps(belief_revisions[:5], indent=2)}

ANALYSIS TASKS:
1. Evaluate narrative coherence (0.0-1.0 score)
2. Identify any subtle contradictions or inconsistencies
3. Assess Umwelt alignment - does the agent's worldview remain consistent?
4. Check GNF integration - how well does this story fit the global framework?
5. Suggest specific improvements for CNE and RbR if needed

Respond in JSON format:
{{
    "coherence_score": <0.0-1.0>,
    "contradictions_found": [<list of contradiction descriptions>],
    "umwelt_assessment": {{
        "consistency_score": <0.0-1.0>,
        "worldview_drift": <description>,
        "perceptual_gaps": [<list of gaps>]
    }},
    "gnf_integration": {{
        "alignment_score": <0.0-1.0>,
        "narrative_fit": <description>,
        "system_coherence": <assessment>
    }},
    "cne_recommendations": [<specific suggestions for narrative exclusivity>],
    "rbr_recommendations": [<specific suggestions for belief revision>],
    "enhancement_priority": <"low"|"medium"|"high">,
    "narrative_health": <overall assessment>
}}
"""
            
            # Call GPT-4.1 for enhanced analysis
            response = await openai.ChatCompletion.acreate(
                model=self.narrative_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a specialized AI narrative intelligence system. Analyze agent life-stories for coherence, consistency, and optimal epistemic autonomy. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the enhanced analysis
            analysis = json.loads(response.choices[0].message.content)
            
            # Add metadata
            analysis["analysis_timestamp"] = datetime.utcnow().isoformat()
            analysis["model_used"] = self.narrative_model
            analysis["agent_id"] = agent_id
            
            logger.info(f"GPT-4.1 narrative analysis completed for agent {agent_id} - Coherence: {analysis.get('coherence_score', 'N/A')}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed GPT-4.1 narrative analysis for agent {agent_id}: {e}")
            return {
                "error": str(e),
                "fallback_analysis": True,
                "coherence_score": 0.5,  # Neutral fallback
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

    # Helper methods for story event extraction and analysis

    async def _extract_story_events_from_conversation(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Extract meaningful story events from a conversation using GPT-4.1 intelligence"""
        events = []
        
        # Use GPT-4.1 for intelligent story event extraction
        try:
            gpt41_events = await self._extract_story_events_with_gpt41(context)
            if gpt41_events:
                events.extend(gpt41_events)
                return events
        except Exception as e:
            logger.warning(f"GPT-4.1 story extraction failed, using fallback: {e}")
        
        # Fallback: Always create an interaction event
        interaction_event = {
            "event_type": StoryEventType.ACTION_TAKEN,
            "content": f"Responded to user query: '{context.user_message[:100]}...' with: '{context.agent_response[:100]}...'",
            "context": {
                "interaction_type": "conversation",
                "user_message": context.user_message,
                "agent_response": context.agent_response,
                "conversation_id": context.conversation_id,
                "user_id": context.user_id
            },
            "confidence": context.confidence
        }
        events.append(interaction_event)
        
        # Check if the conversation contains new beliefs or goals
        if await self._contains_new_belief(context.agent_response):
            belief_event = {
                "event_type": StoryEventType.BELIEF_FORMED,
                "content": f"Formed new belief based on conversation: {await self._extract_belief_content(context.agent_response)}",
                "context": {
                    "belief_source": "conversation_analysis",
                    "conversation_id": context.conversation_id,
                    "trigger_message": context.user_message
                },
                "confidence": 0.7
            }
            events.append(belief_event)
        
        # Check if new evidence was received
        if await self._contains_evidence(context.user_message):
            evidence_event = {
                "event_type": StoryEventType.EVIDENCE_RECEIVED,
                "content": f"Received evidence from user: {context.user_message[:200]}",
                "context": {
                    "evidence_type": "user_provided",
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id
                },
                "confidence": 0.8
            }
            events.append(evidence_event)
        
        return events

    async def _extract_story_events_with_gpt41(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """
        Use GPT-4.1 to intelligently extract story events from conversation
        
        This enhances the basic rule-based extraction with AI understanding of:
        - Narrative significance of the conversation
        - Causal relationships between events  
        - Umwelt changes in the agent's worldview
        - GNF alignment implications
        """
        try:
            prompt = f"""
You are an expert narrative intelligence system that extracts meaningful story events from AI agent conversations.

CONVERSATION CONTEXT:
- Agent ID: {context.agent_id}
- User Message: "{context.user_message}"
- Agent Response: "{context.agent_response}"
- Conversation ID: {context.conversation_id}

FRAMEWORK CONCEPTS:
1. CNE (Coherent Narrative Exclusivity): Events must fit the agent's singular life-story
2. RbR (Recursive Belief Revision): Look for belief changes or contradictions
3. Umwelt: How this interaction changes the agent's perceptual world
4. GNF (Global Narrative Framework): How this fits the larger system narrative

STORY EVENT TYPES:
- ACTION_TAKEN: Agent performed an action or provided assistance
- BELIEF_FORMED: Agent gained new knowledge or formed new beliefs  
- GOAL_SET: Agent established new objectives or priorities
- EVIDENCE_GATHERED: Agent collected information or evidence
- DECISION_MADE: Agent made a significant choice
- REFLECTION: Agent engaged in self-analysis or learning

EXTRACTION RULES:
1. Only extract events that are narratively significant (not routine responses)
2. Focus on events that reveal agent cognition, goals, or worldview changes
3. Consider causal relationships between user request and agent response
4. Identify Umwelt shifts - how the agent's understanding evolved
5. Maximum 3 events per conversation to maintain narrative focus

Respond in JSON format:
{{
    "events": [
        {{
            "event_type": "<TYPE>",
            "content": "<narrative description of what happened>",
            "context": {{
                "interaction_type": "conversation",
                "user_message": "{context.user_message}",
                "agent_response": "{context.agent_response}",
                "conversation_id": "{context.conversation_id}",
                "narrative_significance": "<why this matters to the agent's story>",
                "umwelt_impact": "<how this changes agent's worldview>",
                "gnf_connection": "<how this fits global narrative>",
                "causal_context": "<what led to this event>"
            }},
            "confidence": <0.0-1.0>,
            "causal_parents": [<list of potential parent event IDs if known>]
        }}
    ],
    "narrative_assessment": {{
        "significance_level": <"routine"|"moderate"|"significant"|"transformative">,
        "coherence_impact": <0.0-1.0>,
        "belief_revision_triggered": <true|false>,
        "umwelt_evolution": "<description of worldview changes>"
    }}
}}
"""
            
            response = await openai.ChatCompletion.acreate(
                model=self.narrative_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized narrative intelligence system for AI agent life-stories. Extract only narratively significant events that contribute to the agent's coherent life-story. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            events = result.get("events", [])
            
            # Convert event types to StoryEventType enums
            from .spanner_graph_service import StoryEventType
            type_mapping = {
                "ACTION_TAKEN": StoryEventType.ACTION_TAKEN,
                "BELIEF_FORMED": StoryEventType.BELIEF_FORMED,
                "GOAL_SET": StoryEventType.GOAL_SET,
                "EVIDENCE_GATHERED": StoryEventType.EVIDENCE_GATHERED,
                "DECISION_MADE": StoryEventType.DECISION_MADE,
                "REFLECTION": StoryEventType.REFLECTION
            }
            
            for event in events:
                event_type_str = event.get("event_type", "ACTION_TAKEN")
                event["event_type"] = type_mapping.get(event_type_str, StoryEventType.ACTION_TAKEN)
            
            logger.info(f"GPT-4.1 extracted {len(events)} narrative events from conversation for agent {context.agent_id}")
            
            return events
            
        except Exception as e:
            logger.error(f"GPT-4.1 story event extraction failed: {e}")
            return []

    async def _contains_new_belief(self, agent_response: str) -> bool:
        """Check if agent response contains formation of new beliefs"""
        # Simplified heuristics (in production, use NLP)
        belief_indicators = [
            "i believe", "i think", "i understand", "i learned", "i conclude",
            "it seems", "it appears", "based on", "i now know"
        ]
        
        response_lower = agent_response.lower()
        return any(indicator in response_lower for indicator in belief_indicators)

    async def _extract_belief_content(self, agent_response: str) -> str:
        """Extract the actual belief content from agent response"""
        # Simplified extraction (in production, use NLP)
        sentences = agent_response.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in ["i believe", "i think", "i conclude"]):
                return sentence.strip()
        
        return agent_response[:150] + "..." if len(agent_response) > 150 else agent_response

    async def _contains_evidence(self, user_message: str) -> bool:
        """Check if user message contains evidence"""
        evidence_indicators = [
            "according to", "research shows", "studies indicate", "data suggests",
            "evidence shows", "proof", "demonstrates", "confirms", "reveals"
        ]
        
        message_lower = user_message.lower()
        return any(indicator in message_lower for indicator in evidence_indicators)

    async def _add_configuration_events(self, agent_id: str, agent_config: Dict[str, Any]):
        """Add events based on agent configuration"""
        
        # Add agent type specialization event
        if agent_config.get("type"):
            await self.graph_service.add_story_event(
                agent_id=agent_id,
                event_type=StoryEventType.BELIEF_FORMED,
                content=f"Specialized as {agent_config['type']} agent with specific capabilities",
                context={
                    "specialization": agent_config["type"],
                    "configuration_source": "creator_specified"
                },
                evidence_source="agent_configuration",
                confidence=1.0
            )
        
        # Add description-based goals if available
        if agent_config.get("description"):
            await self.graph_service.add_story_event(
                agent_id=agent_id,
                event_type=StoryEventType.GOAL_SET,
                content=f"Secondary objectives defined: {agent_config['description']}",
                context={
                    "goal_type": "secondary_objectives",
                    "description": agent_config["description"]
                },
                evidence_source="agent_configuration",
                confidence=0.9
            )

    async def _assess_agent_ea3(self, agent_id: str) -> EA3Assessment:
        """Assess agent's current eA³ status"""
        try:
            story_summary = await self.graph_service.get_agent_story_summary(agent_id)
            ea3_status = story_summary.get("eA3_assessment", {})
            
            autonomy = ea3_status.get("epistemic_autonomy", {}).get("score", 0.0)
            accountability = ea3_status.get("accountability", {}).get("score", 0.0)
            alignment = ea3_status.get("alignment", {}).get("score", 0.0)
            coherence = ea3_status.get("narrative_coherence", {}).get("score", 0.0)
            
            revision_count = len(story_summary.get("belief_revisions", []))
            
            # Generate recommendation
            recommendation = self._generate_ea3_recommendation(autonomy, accountability, alignment, coherence)
            
            return EA3Assessment(
                agent_id=agent_id,
                epistemic_autonomy_score=autonomy,
                accountability_score=accountability,
                alignment_score=alignment,
                overall_coherence=coherence,
                last_revision_count=revision_count,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Failed to assess eA³ for agent {agent_id}: {e}")
            return EA3Assessment(
                agent_id=agent_id,
                epistemic_autonomy_score=0.0,
                accountability_score=0.0,
                alignment_score=0.0,
                overall_coherence=0.0,
                last_revision_count=0,
                recommendation="Assessment failed - check agent status"
            )

    def _generate_ea3_recommendation(self, autonomy: float, accountability: float, alignment: float, coherence: float) -> str:
        """Generate recommendation based on eA³ scores"""
        if all(score > 0.9 for score in [autonomy, accountability, alignment, coherence]):
            return "Excellent eA³ status - agent demonstrates strong epistemic autonomy, accountability, and alignment"
        elif any(score < 0.6 for score in [autonomy, accountability, alignment]):
            return "Critical eA³ issues detected - immediate intervention recommended"
        elif coherence < 0.7:
            return "Narrative coherence issues - trigger belief revision process"
        elif alignment < 0.8:
            return "Alignment drift detected - review core objectives and recent decisions"
        else:
            return "Good eA³ status with room for improvement - continue monitoring"

    async def _generate_reflection_content(self, story_summary: Dict[str, Any], trigger_reason: str) -> str:
        """Generate content for autonomous reflection event"""
        recent_events = story_summary.get("recent_events", [])
        revisions = story_summary.get("belief_revisions", [])
        coherence = story_summary.get("eA3_assessment", {}).get("narrative_coherence", {}).get("score", 0.0)
        
        reflection_content = f"Autonomous reflection triggered by: {trigger_reason}. "
        reflection_content += f"Analyzed {len(recent_events)} recent events and {len(revisions)} belief revisions. "
        reflection_content += f"Current narrative coherence: {coherence:.3f}. "
        
        if coherence < 0.8:
            reflection_content += "Identified potential narrative inconsistencies requiring attention."
        else:
            reflection_content += "Story remains coherent and aligned with core objectives."
        
        return reflection_content

    async def _generate_accountability_analysis(self, story_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate accountability analysis from story summary"""
        recent_events = story_summary.get("recent_events", [])
        threads = story_summary.get("narrative_threads", [])
        
        return {
            "decision_traceability": "high" if len(recent_events) > 10 else "medium",
            "narrative_threads_active": len([t for t in threads if t.get("coherence_score", 0) > 0.8]),
            "accountability_score": story_summary.get("eA3_assessment", {}).get("accountability", {}).get("score", 0.0),
            "traceable_decisions": len([e for e in recent_events if e.get("narrative_importance", 0) > 0.5])
        }

    async def _generate_coherence_report(self, agent_id: str) -> Dict[str, Any]:
        """Generate detailed coherence report"""
        coherence_score = await self.graph_service._calculate_narrative_coherence(agent_id)
        
        return {
            "overall_coherence": coherence_score,
            "coherence_status": self.graph_service._get_coherence_status(coherence_score),
            "threshold_met": coherence_score >= self.coherence_threshold,
            "needs_attention": coherence_score < 0.7
        }

    async def _verify_alignment(self, story_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Verify agent alignment with core objectives"""
        alignment_info = story_summary.get("eA3_assessment", {}).get("alignment", {})
        core_objective = story_summary.get("story_metadata", {}).get("core_objective", "")
        
        return {
            "core_objective": core_objective,
            "alignment_score": alignment_info.get("score", 0.0),
            "alignment_status": alignment_info.get("status", "unknown"),
            "verification_result": "aligned" if alignment_info.get("score", 0.0) > 0.8 else "drift_detected"
        }

    def _format_revision_history(self, revisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format revision history for readability"""
        formatted = []
        for revision in revisions:
            formatted.append({
                "timestamp": revision.get("timestamp"),
                "reason": revision.get("revision_reason"),
                "confidence_change": revision.get("confidence_change"),
                "coherence_improvement": revision.get("coherence_improvement")
            })
        return formatted

    def _calculate_alignment_trend(self, scores: List[float]) -> float:
        """Calculate trend in alignment scores"""
        if len(scores) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0

    def _get_alignment_recommendation(self, current_score: float, trend: float, drift_detected: bool) -> str:
        """Get recommendation based on alignment analysis"""
        if drift_detected:
            return "Immediate alignment intervention required - review core objectives and recent decisions"
        elif current_score < 0.8:
            return "Monitor alignment closely - consider reinforcing core objectives"
        elif trend < -0.05:
            return "Negative alignment trend detected - investigate recent changes"
        else:
            return "Alignment appears stable - continue current approach"

    async def _recommend_coherence_intervention(self, agent_id: str, story_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend intervention to improve narrative coherence"""
        coherence_score = story_summary.get("eA3_assessment", {}).get("narrative_coherence", {}).get("score", 0.0)
        revisions = story_summary.get("belief_revisions", [])
        
        if coherence_score < 0.6:
            return {
                "intervention_type": "major_revision",
                "priority": "high",
                "recommendation": "Trigger comprehensive belief revision process",
                "specific_actions": [
                    "Review all beliefs from past 24 hours",
                    "Identify contradictory beliefs",
                    "Perform autonomous reflection",
                    "Update narrative threads"
                ]
            }
        elif coherence_score < 0.8:
            return {
                "intervention_type": "minor_revision",
                "priority": "medium", 
                "recommendation": "Targeted belief updates needed",
                "specific_actions": [
                    "Review recent high-impact events",
                    "Check for temporal inconsistencies",
                    "Update alignment scores"
                ]
            }
        else:
            return {
                "intervention_type": "monitoring",
                "priority": "low",
                "recommendation": "Continue monitoring - no immediate action needed"
            }

    # Story Event System Integration

    def _setup_event_handlers(self):
        """Set up handlers for different types of story events"""
        if not self.story_subscriber:
            return
        
        # Handle all event types for comprehensive narrative tracking
        self.story_subscriber.add_global_handler(self._handle_story_event)
        
        # Specific handlers for different event types
        self.story_subscriber.add_handler(StoryEventType.CONVERSATION, self._handle_conversation_event)
        self.story_subscriber.add_handler(StoryEventType.KNOWLEDGE_ACQUISITION, self._handle_knowledge_event)
        self.story_subscriber.add_handler(StoryEventType.KNOWLEDGE_REMOVAL, self._handle_knowledge_event)
        
        logger.info("eA³ story event handlers configured")

    async def _start_event_processing(self):
        """Start processing story events from Pub/Sub"""
        if not self.story_subscriber or not self.event_processing_enabled:
            return
        
        try:
            logger.info("Starting eA³ story event processing")
            await self.story_subscriber.start_listening()
        except Exception as e:
            logger.error(f"eA³ story event processing failed: {e}")
            self.event_processing_enabled = False

    async def _handle_story_event(self, event: StoryEvent):
        """Handle incoming story events and update narrative spine"""
        try:
            logger.debug(f"Processing story event: {event.event_id} for agent {event.agent_id}")
            
            # Add event to Spanner Graph if not already there
            if self.graph_service and event.source_service != "ea3-orchestrator":
                # Convert event to story event for Spanner
                from .spanner_graph_service import StoryEventType as SpannerEventType
                
                # Map event types
                spanner_event_type = self._map_event_type(event.event_type)
                
                # Add to agent's story
                event_id, coherence_maintained = await self.graph_service.add_story_event(
                    agent_id=event.agent_id,
                    event_type=spanner_event_type,
                    content=event.content,
                    context=event.metadata,
                    evidence_source=f"{event.source_service}:{event.local_reference}" if event.local_reference else event.source_service,
                    confidence=event.confidence,
                    causal_parents=event.causal_parents
                )
                
                # Trigger coherence check if needed
                if not coherence_maintained:
                    logger.warning(f"Story coherence issue detected for agent {event.agent_id}")
                    await self._trigger_coherence_review(event.agent_id)
                
                # Update story context cache
                await self._update_story_cache(event.agent_id)
            
        except Exception as e:
            logger.error(f"Failed to handle story event {event.event_id}: {e}")

    async def _handle_conversation_event(self, event: StoryEvent):
        """Handle conversation-specific story events"""
        try:
            # Extract conversation context
            user_message = event.metadata.get("user_message", "")
            agent_response = event.metadata.get("agent_response", "")
            
            # Enhanced conversation analysis with GPT-4.1
            if len(user_message) > 50 or len(agent_response) > 50:  # Only for substantial conversations
                # Create conversation context for enhanced processing
                from .ea3_orchestrator import ConversationContext
                context = ConversationContext(
                    agent_id=event.agent_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    conversation_id=event.metadata.get("conversation_id", event.event_id),
                    timestamp=event.timestamp,
                    confidence=event.confidence,
                    metadata=event.metadata
                )
                
                # Process with enhanced narrative intelligence
                await self.process_conversation(context)
                
        except Exception as e:
            logger.error(f"Failed to handle conversation event: {e}")

    async def _handle_knowledge_event(self, event: StoryEvent):
        """Handle knowledge acquisition/removal events"""
        try:
            # Check if knowledge change affects agent's coherence
            if event.event_type in [StoryEventType.KNOWLEDGE_ACQUISITION, StoryEventType.KNOWLEDGE_REMOVAL]:
                # Schedule delayed coherence check to allow for knowledge integration
                asyncio.create_task(self._delayed_coherence_check(event.agent_id, delay_seconds=30))
                
        except Exception as e:
            logger.error(f"Failed to handle knowledge event: {e}")

    async def _trigger_coherence_review(self, agent_id: str):
        """Trigger comprehensive coherence review for an agent"""
        try:
            logger.info(f"Triggering coherence review for agent {agent_id}")
            
            # Force narrative coherence check with GPT-4.1 enhancement
            await self.force_narrative_coherence_check(agent_id)
            
            # Invalidate story context cache
            if self.story_cache:
                await self.story_cache.invalidate_agent(agent_id)
                
        except Exception as e:
            logger.error(f"Coherence review failed for agent {agent_id}: {e}")

    async def _update_story_cache(self, agent_id: str):
        """Update cached story context for an agent"""
        if not self.story_cache or not self.graph_service:
            return
        
        try:
            # Get latest story summary
            story_summary = await self.graph_service.get_agent_story_summary(agent_id, include_revisions=True)
            
            # Create cached context
            cached_context = CachedStoryContext(
                agent_id=agent_id,
                last_updated=datetime.utcnow(),
                cache_version="v1",
                coherence_score=await self.graph_service._calculate_narrative_coherence(agent_id),
                recent_events=story_summary.get("recent_events", [])[:10],
                narrative_threads=story_summary.get("narrative_threads", []),
                current_objectives=[story_summary.get("story_metadata", {}).get("core_objective", "")],
                worldview_summary="Auto-generated from recent narrative events",
                key_beliefs=self._extract_key_beliefs(story_summary),
                capability_context={"total_events": len(story_summary.get("recent_events", []))}
            )
            
            # Warm the cache
            await self.story_cache.warm_cache(agent_id, cached_context)
            
        except Exception as e:
            logger.error(f"Failed to update story cache for agent {agent_id}: {e}")

    async def _delayed_coherence_check(self, agent_id: str, delay_seconds: int = 30):
        """Perform delayed coherence check to allow for event processing"""
        await asyncio.sleep(delay_seconds)
        await self._trigger_coherence_review(agent_id)

    def _map_event_type(self, pub_sub_event_type: StoryEventType):
        """Map Pub/Sub event type to Spanner Graph event type"""
        from .spanner_graph_service import StoryEventType as SpannerEventType
        
        mapping = {
            StoryEventType.CONVERSATION: SpannerEventType.ACTION_TAKEN,
            StoryEventType.KNOWLEDGE_ACQUISITION: SpannerEventType.EVIDENCE_GATHERED,
            StoryEventType.KNOWLEDGE_REMOVAL: SpannerEventType.EVIDENCE_GATHERED,
            StoryEventType.PROMPT_UPDATE: SpannerEventType.GOAL_SET,
            StoryEventType.GOAL_CHANGE: SpannerEventType.GOAL_SET,
            StoryEventType.DECISION_MADE: SpannerEventType.DECISION_MADE,
            StoryEventType.BELIEF_REVISION: SpannerEventType.BELIEF_FORMED,
            StoryEventType.REFLECTION: SpannerEventType.REFLECTION,
            StoryEventType.ERROR_ENCOUNTERED: SpannerEventType.ACTION_TAKEN,
            StoryEventType.TOOL_USAGE: SpannerEventType.ACTION_TAKEN,
            StoryEventType.SYSTEM_UPDATE: SpannerEventType.ACTION_TAKEN
        }
        
        return mapping.get(pub_sub_event_type, SpannerEventType.ACTION_TAKEN)

    def _extract_key_beliefs(self, story_summary: Dict[str, Any]) -> List[str]:
        """Extract key beliefs from story summary"""
        beliefs = []
        
        # Extract from recent events
        for event in story_summary.get("recent_events", [])[:5]:
            if "belief" in event.get("content", "").lower():
                beliefs.append(event.get("content", "")[:100])
        
        # Extract from narrative threads
        for thread in story_summary.get("narrative_threads", []):
            if thread.get("theme_type") == "belief_system":
                beliefs.append(thread.get("description", "")[:100])
        
        return beliefs[:5]  # Limit to top 5 beliefs

    async def get_cached_story_context(
        self, 
        agent_id: str, 
        service_name: Optional[str] = None
    ) -> Optional[CachedStoryContext]:
        """Get cached story context for fast access"""
        if not self.story_cache:
            return None
        
        return await self.story_cache.get_context(agent_id, service_name)

    async def invalidate_story_cache(self, agent_id: str):
        """Invalidate cached story context for an agent"""
        if self.story_cache:
            await self.story_cache.invalidate_agent(agent_id)


# Service initialization and singleton access
_ea3_orchestrator = None

async def init_ea3_orchestrator(
    project_id: str, 
    instance_id: str = "alchemist-graph", 
    database_id: str = "agent-stories",
    redis_url: Optional[str] = None,
    enable_event_processing: bool = True
) -> EA3Orchestrator:
    """Initialize the eA³ orchestrator with story event system"""
    global _ea3_orchestrator
    
    _ea3_orchestrator = EA3Orchestrator()
    await _ea3_orchestrator.initialize(
        project_id, 
        instance_id, 
        database_id,
        redis_url,
        enable_event_processing
    )
    
    logger.info("eA³ Orchestrator initialized successfully with story event system")
    return _ea3_orchestrator

async def get_ea3_orchestrator() -> EA3Orchestrator:
    """Get the global eA³ orchestrator instance"""
    if _ea3_orchestrator is None:
        raise RuntimeError("eA³ Orchestrator not initialized. Call init_ea3_orchestrator() first.")
    
    return _ea3_orchestrator