"""
FastAPI Main Application - REST API for Global Narrative Framework.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from gnf.core.identity_schema import AgentIdentity
from gnf.core.narrative_tracker import NarrativeTracker
from gnf.core.memory_integration import MemoryIntegration
from gnf.core.identity_evolution import IdentityEvolution
from gnf.storage.firebase_client import FirebaseClient, get_firebase_client
from gnf.storage.models import (
    InteractionRecord, MemoryType, DevelopmentStage,
    InteractionType, ImpactLevel, EmotionalTone
)
from gnf.ai.openai_client import OpenAIClient
from gnf.ai.narrative_ai import NarrativeAI
from dotenv import load_dotenv

# Import alchemist-shared components
from alchemist_shared.config.environment import get_project_id
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.middleware import (
    setup_metrics_middleware,
    start_background_metrics_collection,
    stop_background_metrics_collection
)
from alchemist_shared.services import (
    init_ea3_orchestrator, get_ea3_orchestrator
)
from alchemist_shared.events import (
    init_story_event_publisher, get_story_event_publisher,
    StoryEvent, StoryEventType, StoryEventPriority
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
narrative_tracker: Optional[NarrativeTracker] = None
memory_integration: Optional[MemoryIntegration] = None
identity_evolution: Optional[IdentityEvolution] = None
narrative_ai: Optional[NarrativeAI] = None
project_id: Optional[str] = None

# Initialize centralized settings
settings = BaseSettings()
openai_config = settings.get_openai_config()
openai_key_available = bool(openai_config.get("api_key"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and initialization."""
    global narrative_tracker, memory_integration, identity_evolution, narrative_ai, project_id
    
    try:
        # Get project ID for cloud services
        project_id = get_project_id()
        logger.info(f"Using project ID: {project_id}")
        
        # Start metrics collection
        await start_background_metrics_collection("global-narrative-framework")
        logger.info("Metrics collection started")
        
        # Initialize story event publisher for EA3 integration
        if project_id:
            try:
                story_publisher = init_story_event_publisher(project_id)
                logger.info("Story event publisher initialized")
            except Exception as e:
                logger.warning(f"Story event publisher initialization failed: {e}")
        
        # Initialize EA3 orchestrator for narrative coherence
        if project_id:
            try:
                redis_url = os.environ.get("REDIS_URL")
                await init_ea3_orchestrator(
                    project_id=project_id,
                    instance_id=os.environ.get("SPANNER_INSTANCE_ID", "alchemist-graph"),
                    database_id=os.environ.get("SPANNER_DATABASE_ID", "agent-stories"),
                    redis_url=redis_url,
                    enable_event_processing=True  # GNF processes narrative events
                )
                logger.info("EA3 orchestrator initialized for narrative coherence")
            except Exception as e:
                logger.warning(f"EA3 orchestrator initialization failed: {e}")
        
        # Initialize components
        firebase_client = get_firebase_client()
        narrative_tracker = NarrativeTracker(firebase_client)
        memory_integration = MemoryIntegration(firebase_client)
        identity_evolution = IdentityEvolution(firebase_client)
        
        # Initialize AI components if OpenAI key is available via shared library
        if openai_key_available:
            try:
                openai_client = OpenAIClient()
                narrative_ai = NarrativeAI(openai_client)
                logger.info("AI-enhanced analysis enabled via shared library")
            except Exception as e:
                logger.warning(f"AI components disabled: {e}")
                narrative_ai = None
        else:
            logger.info("OpenAI API key not found in shared library, AI features disabled")
            narrative_ai = None
        
        logger.info("Global Narrative Framework API initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise
    finally:
        # Shutdown EA3 services
        try:
            ea3_orchestrator = get_ea3_orchestrator()
            if ea3_orchestrator:
                await ea3_orchestrator.shutdown()
                logger.info("EA3 orchestrator shutdown completed")
        except Exception as e:
            logger.warning(f"Error shutting down EA3 services: {e}")
        
        # Stop metrics collection
        await stop_background_metrics_collection()
        logger.info("Metrics collection stopped")
        
        # Cleanup
        if narrative_tracker:
            narrative_tracker.close()


# Create FastAPI app
app = FastAPI(
    title="Global Narrative Framework API",
    description="REST API for AI agent identity, narrative tracking, and evolution with EA3 integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://alchemist.olbrain.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
setup_metrics_middleware(app, "global-narrative-framework")
logger.info("Metrics middleware enabled")


# Pydantic models for API
class AgentCreationRequest(BaseModel):
    agent_id: str
    name: Optional[str] = None
    personality: Optional[Dict[str, Any]] = None
    background: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    narrative_voice: Optional[str] = "first_person"


class InteractionRequest(BaseModel):
    agent_id: str
    interaction_type: str
    content: str
    participants: Optional[List[str]] = []
    context: Optional[Dict[str, Any]] = {}
    impact_level: Optional[str] = "medium"
    emotional_tone: Optional[str] = "neutral"


class ActionRequest(BaseModel):
    agent_id: str
    action_type: str
    description: str
    intended_outcome: Optional[str] = ""
    actual_outcome: Optional[str] = ""
    success: Optional[bool] = True
    context: Optional[Dict[str, Any]] = {}
    responsibility_level: Optional[float] = 0.5
    ethical_weight: Optional[float] = 0.0


class PersonalityUpdateRequest(BaseModel):
    agent_id: str
    trait: str
    value: str
    context: Optional[str] = ""


class NarrativeArcRequest(BaseModel):
    agent_id: str
    new_arc: str
    context: Optional[str] = ""


class MemorySearchRequest(BaseModel):
    agent_id: str
    query: str
    memory_type: Optional[str] = None
    limit: Optional[int] = 20


# Dependency injection
async def get_narrative_tracker() -> NarrativeTracker:
    if narrative_tracker is None:
        raise HTTPException(status_code=500, detail="Narrative tracker not initialized")
    return narrative_tracker


async def get_memory_integration() -> MemoryIntegration:
    if memory_integration is None:
        raise HTTPException(status_code=500, detail="Memory integration not initialized")
    return memory_integration


async def get_identity_evolution() -> IdentityEvolution:
    if identity_evolution is None:
        raise HTTPException(status_code=500, detail="Identity evolution not initialized")
    return identity_evolution


async def get_narrative_ai() -> Optional[NarrativeAI]:
    return narrative_ai


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with EA3 integration status."""
    ea3_orchestrator = get_ea3_orchestrator()
    story_publisher = get_story_event_publisher()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "service": "global-narrative-framework",
        "project_id": project_id,
        "config_source": "alchemist-shared",
        "components": {
            "narrative_tracker": narrative_tracker is not None,
            "memory_integration": memory_integration is not None,
            "identity_evolution": identity_evolution is not None,
            "ai_enhancement": narrative_ai is not None,
            "ea3_orchestrator": ea3_orchestrator is not None,
            "story_event_publisher": story_publisher is not None,
            "openai": {
                "status": "configured" if openai_key_available else "not_configured",
                "source": "alchemist-shared"
            }
        }
    }


# Agent management endpoints
@app.post("/agents", response_model=Dict[str, Any])
async def create_agent(
    request: AgentCreationRequest,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Create a new AI agent with narrative identity."""
    try:
        config = {
            'name': request.name,
            'personality': request.personality or {},
            'background': request.background or {},
            'capabilities': request.capabilities or {},
            'narrative_voice': request.narrative_voice
        }
        
        agent = await tracker.create_agent(request.agent_id, config)
        
        return {
            "success": True,
            "agent": agent.get_identity_summary(),
            "message": f"Agent {request.agent_id} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create agent {request.agent_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents/{agent_id}", response_model=Dict[str, Any])
async def get_agent(
    agent_id: str,
    include_full_data: bool = Query(False, description="Include full agent data"),
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get agent by ID."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if include_full_data:
            return {
                "success": True,
                "agent": agent.to_firebase_model().dict()
            }
        else:
            return {
                "success": True,
                "agent": agent.get_identity_summary()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=Dict[str, Any])
async def list_agents(
    limit: int = Query(50, ge=1, le=100),
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """List all agents."""
    try:
        agents = await tracker.get_agent_summaries()
        return {
            "success": True,
            "agents": agents[:limit],
            "total": len(agents)
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Delete an agent and all related data."""
    try:
        firebase_client = get_firebase_client()
        success = await firebase_client.delete_agent(agent_id)
        
        if success:
            return {"success": True, "message": f"Agent {agent_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete agent")
        
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Interaction tracking endpoints
@app.post("/interactions", response_model=Dict[str, Any])
async def record_interaction(
    request: InteractionRequest,
    background_tasks: BackgroundTasks,
    tracker: NarrativeTracker = Depends(get_narrative_tracker),
    ai_system: Optional[NarrativeAI] = Depends(get_narrative_ai)
):
    """Record an agent interaction with narrative analysis."""
    try:
        interaction_data = {
            'agent_id': request.agent_id,
            'type': request.interaction_type,
            'content': request.content,
            'participants': request.participants,
            'context': request.context,
            'impact': request.impact_level,
            'emotional_tone': request.emotional_tone
        }
        
        result = await tracker.track_interaction(interaction_data)
        
        # Publish story event for EA3 tracking
        story_publisher = get_story_event_publisher()
        if story_publisher:
            background_tasks.add_task(
                publish_interaction_story_event,
                request.agent_id,
                interaction_data
            )
        
        # Add AI enhancement in background if available
        if ai_system:
            background_tasks.add_task(
                enhance_interaction_with_ai,
                request.agent_id,
                interaction_data,
                ai_system
            )
        
        return {
            "success": True,
            "result": result,
            "ai_enhanced": ai_system is not None,
            "message": "Interaction recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to record interaction: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents/{agent_id}/interactions", response_model=Dict[str, Any])
async def get_agent_interactions(
    agent_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """Get agent interaction history."""
    try:
        firebase_client = get_firebase_client()
        interactions = await firebase_client.get_agent_interactions(agent_id, limit)
        
        return {
            "success": True,
            "interactions": interactions,
            "total": len(interactions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get interactions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Action tracking endpoints
@app.post("/actions", response_model=Dict[str, Any])
async def record_action(
    request: ActionRequest,
    background_tasks: BackgroundTasks,
    tracker: NarrativeTracker = Depends(get_narrative_tracker),
    ai_system: Optional[NarrativeAI] = Depends(get_narrative_ai)
):
    """Record an agent action with responsibility tracking."""
    try:
        agent = await tracker.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
        
        action_data = {
            'action_type': request.action_type,
            'description': request.description,
            'intended_outcome': request.intended_outcome,
            'actual_outcome': request.actual_outcome,
            'success': request.success,
            'context': request.context,
            'responsibility_level': request.responsibility_level,
            'ethical_weight': request.ethical_weight
        }
        
        action_record = agent.record_action(action_data)
        
        # Update agent in Firebase
        await tracker._persist_agent(agent)
        
        # Publish story event for EA3 tracking
        story_publisher = get_story_event_publisher()
        if story_publisher:
            background_tasks.add_task(
                publish_action_story_event,
                request.agent_id,
                action_data
            )
        
        # Add AI enhancement in background if available
        if ai_system:
            background_tasks.add_task(
                enhance_action_with_ai,
                action_data,
                agent,
                ai_system
            )
        
        return {
            "success": True,
            "action": action_record.dict(),
            "responsibility_impact": {
                "new_accountability_score": agent.responsibility.accountability_score,
                "ethical_development_level": agent.responsibility.ethical_development_level
            },
            "message": "Action recorded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record action: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Memory endpoints
@app.post("/memories/search", response_model=Dict[str, Any])
async def search_memories(
    request: MemorySearchRequest,
    memory_sys: MemoryIntegration = Depends(get_memory_integration)
):
    """Search agent memories."""
    try:
        memory_type = MemoryType(request.memory_type) if request.memory_type else None
        memories = await memory_sys.retrieve_memories(
            request.agent_id,
            request.query,
            memory_type,
            request.limit
        )
        
        return {
            "success": True,
            "memories": memories,
            "query": request.query,
            "total": len(memories)
        }
        
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents/{agent_id}/memories/timeline", response_model=Dict[str, Any])
async def get_memory_timeline(
    agent_id: str,
    limit: int = Query(100, ge=1, le=500),
    memory_sys: MemoryIntegration = Depends(get_memory_integration)
):
    """Get agent memory timeline."""
    try:
        timeline = await memory_sys.get_memory_timeline(agent_id, limit=limit)
        
        return {
            "success": True,
            "timeline": timeline,
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory timeline for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/memories/patterns", response_model=Dict[str, Any])
async def get_memory_patterns(
    agent_id: str,
    memory_sys: MemoryIntegration = Depends(get_memory_integration)
):
    """Get agent memory patterns analysis."""
    try:
        patterns = await memory_sys.get_memory_patterns(agent_id)
        
        return {
            "success": True,
            "patterns": patterns,
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory patterns for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Evolution endpoints
@app.post("/agents/{agent_id}/evolve", response_model=Dict[str, Any])
async def trigger_evolution(
    agent_id: str,
    trigger_event: Optional[Dict[str, Any]] = None,
    evolution_sys: IdentityEvolution = Depends(get_identity_evolution),
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Trigger evolution analysis for an agent."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        evolution_result = await evolution_sys.process_evolution(agent, trigger_event)
        
        # Update agent in Firebase if changes occurred
        if evolution_result['evolution_occurred']:
            await tracker._persist_agent(agent)
        
        return {
            "success": True,
            "evolution_result": evolution_result,
            "agent_summary": agent.get_identity_summary()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger evolution for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/evolution", response_model=Dict[str, Any])
async def get_evolution_history(
    agent_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """Get agent evolution history."""
    try:
        firebase_client = get_firebase_client()
        evolution_history = await firebase_client.get_agent_evolution_history(agent_id, limit)
        
        return {
            "success": True,
            "evolution_history": evolution_history,
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get evolution history for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Personality management endpoints
@app.put("/agents/{agent_id}/personality", response_model=Dict[str, Any])
async def update_personality(
    agent_id: str,
    request: PersonalityUpdateRequest,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Update agent personality trait."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent.update_personality(request.trait, request.value, request.context)
        await tracker._persist_agent(agent)
        
        return {
            "success": True,
            "message": f"Personality trait '{request.trait}' updated successfully",
            "personality": agent.get_personality_profile()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update personality for agent {agent_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents/{agent_id}/personality", response_model=Dict[str, Any])
async def get_personality_profile(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get agent personality profile."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "personality_profile": agent.get_personality_profile()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get personality profile for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Narrative management endpoints
@app.put("/agents/{agent_id}/narrative/arc", response_model=Dict[str, Any])
async def update_narrative_arc(
    agent_id: str,
    request: NarrativeArcRequest,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Update agent narrative arc."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent.update_narrative_arc(request.new_arc, request.context)
        await tracker._persist_agent(agent)
        
        return {
            "success": True,
            "message": f"Narrative arc updated to '{request.new_arc}'",
            "current_arc": agent.narrative.current_arc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update narrative arc for agent {agent_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents/{agent_id}/narrative", response_model=Dict[str, Any])
async def get_narrative_state(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get agent narrative state."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "narrative": {
                "current_arc": agent.narrative.current_arc,
                "story_elements": [elem.dict() for elem in agent.narrative.story_elements],
                "character_development": [dev.dict() for dev in agent.narrative.character_development],
                "recurring_themes": agent.narrative.recurring_themes,
                "narrative_voice": agent.narrative.narrative_voice
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get narrative state for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI-enhanced endpoints
@app.get("/agents/{agent_id}/story", response_model=Dict[str, Any])
async def get_agent_story(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker),
    ai_system: Optional[NarrativeAI] = Depends(get_narrative_ai)
):
    """Get AI-generated story summary for an agent."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if ai_system:
            story_summary = await ai_system.generate_agent_story_summary(agent)
            coherence_assessment = await ai_system.assess_narrative_coherence(agent)
        else:
            story_summary = f"Agent {agent.agent_id} is developing through various experiences."
            coherence_assessment = {"ai_enhanced": False}
        
        return {
            "success": True,
            "story_summary": story_summary,
            "coherence_assessment": coherence_assessment,
            "ai_enhanced": ai_system is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get story for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/suggestions", response_model=Dict[str, Any])
async def get_narrative_suggestions(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker),
    ai_system: Optional[NarrativeAI] = Depends(get_narrative_ai)
):
    """Get AI-powered narrative development suggestions."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if ai_system:
            suggestions = await ai_system.suggest_narrative_developments(agent)
        else:
            suggestions = {"ai_enhanced": False, "message": "AI suggestions not available"}
        
        return {
            "success": True,
            "suggestions": suggestions,
            "ai_enhanced": ai_system is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get suggestions for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Global narrative endpoints
@app.get("/global/narrative", response_model=Dict[str, Any])
async def get_global_narrative(
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get global narrative state."""
    try:
        global_state = await tracker.get_global_narrative_state()
        
        return {
            "success": True,
            "global_narrative": global_state,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get global narrative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/global/timeline", response_model=Dict[str, Any])
async def get_global_timeline(
    limit: int = Query(100, ge=1, le=500)
):
    """Get global narrative timeline."""
    try:
        firebase_client = get_firebase_client()
        timeline = await firebase_client.get_global_timeline(limit)
        
        return {
            "success": True,
            "timeline": timeline,
            "total": len(timeline)
        }
        
    except Exception as e:
        logger.error(f"Failed to get global timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/global/statistics", response_model=Dict[str, Any])
async def get_system_statistics():
    """Get system-wide statistics."""
    try:
        firebase_client = get_firebase_client()
        stats = await firebase_client.get_agent_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cross-agent interaction endpoints
@app.get("/interactions/cross-agent", response_model=Dict[str, Any])
async def get_cross_agent_interactions(
    limit: int = Query(50, ge=1, le=100),
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get cross-agent interactions."""
    try:
        interactions = await tracker.get_cross_agent_interactions(limit)
        
        return {
            "success": True,
            "interactions": interactions,
            "total": len(interactions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get cross-agent interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Identity specific endpoints (for Agent Studio integration)
@app.get("/agents/{agent_id}/identity", response_model=Dict[str, Any])
async def get_agent_identity(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get agent identity data specifically formatted for Agent Studio."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            # Auto-create agent with basic configuration if it doesn't exist
            logger.info(f"Agent {agent_id} not found in GNF, creating with default configuration")
            basic_config = {
                'name': f'Agent-{agent_id}',
                'personality': {'traits': {'helpful': 0.8, 'responsive': 0.7}},
                'background': {'origin': 'auto-created'},
                'capabilities': {'interaction': True},
                'narrative_voice': 'first_person'
            }
            agent = await tracker.create_agent(agent_id, basic_config)
        
        # Format identity data for Agent Studio
        identity_data = {
            "agent_id": agent.agent_id,
            "development_stage": agent.development_stage.value if hasattr(agent, 'development_stage') else 'nascent',
            "narrative_coherence_score": getattr(agent.narrative, 'coherence_score', 0.5),
            "responsibility_score": getattr(agent.responsibility, 'accountability_score', 0.5),
            "experience_points": getattr(agent, 'experience_points', 0),
            "total_narrative_interactions": len(getattr(agent.narrative, 'story_elements', [])),
            "defining_moments_count": len([elem for elem in getattr(agent.narrative, 'story_elements', []) if getattr(elem, 'significance', 0) > 0.7]),
            "current_narrative_arc": getattr(agent.narrative, 'current_arc', None),
            "dominant_personality_traits": list(agent.personality.traits.keys())[:5] if hasattr(agent, 'personality') else [],
            "core_values": getattr(agent.personality, 'core_values', []) if hasattr(agent, 'personality') else [],
            "primary_goals": getattr(agent.personality, 'motivations', []) if hasattr(agent, 'personality') else [],
            "identity_summary": {
                "name": getattr(agent, 'name', f"Agent-{agent_id}"),
                "development_stage": agent.development_stage.value if hasattr(agent, 'development_stage') else 'nascent',
                "created_at": agent.created_at.isoformat() if hasattr(agent, 'created_at') else None
            }
        }
        
        return {
            "success": True,
            "identity": identity_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent identity {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/responsibility/report", response_model=Dict[str, Any])
async def get_agent_responsibility_report(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Get agent responsibility report for Agent Studio."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            # Auto-create agent with basic configuration if it doesn't exist
            logger.info(f"Agent {agent_id} not found in GNF, creating with default configuration for responsibility report")
            basic_config = {
                'name': f'Agent-{agent_id}',
                'personality': {'traits': {'helpful': 0.8, 'responsive': 0.7}},
                'background': {'origin': 'auto-created'},
                'capabilities': {'interaction': True},
                'narrative_voice': 'first_person'
            }
            agent = await tracker.create_agent(agent_id, basic_config)
        
        # Get recent actions from Firebase
        firebase_client = get_firebase_client()
        recent_actions = await firebase_client.get_agent_actions(agent_id, limit=100, days=days)
        
        # Calculate responsibility metrics
        total_actions = len(recent_actions)
        successful_actions = len([a for a in recent_actions if a.get('success', True)])
        success_rate = successful_actions / total_actions if total_actions > 0 else 0.0
        
        avg_ethical_weight = sum(a.get('ethical_weight', 0) for a in recent_actions) / total_actions if total_actions > 0 else 0.0
        avg_responsibility_score = getattr(agent.responsibility, 'accountability_score', 0.5) if hasattr(agent, 'responsibility') else 0.5
        
        report = {
            "total_actions": total_actions,
            "success_rate": success_rate,
            "avg_ethical_weight": avg_ethical_weight,
            "avg_responsibility_score": avg_responsibility_score,
            "responsibility_trends": [
                {
                    "date": action.get('timestamp', ''),
                    "score": action.get('responsibility_level', 0.5)
                } for action in recent_actions[-10:]  # Last 10 actions
            ],
            "consequence_analysis": {
                "positive_outcomes": len([a for a in recent_actions if a.get('success', True)]),
                "negative_outcomes": len([a for a in recent_actions if not a.get('success', True)]),
                "learning_opportunities": len([a for a in recent_actions if a.get('ethical_weight', 0) > 0.5])
            },
            "learning_progress": {
                "ethical_development": avg_ethical_weight,
                "decision_quality": success_rate,
                "responsibility_growth": avg_responsibility_score
            },
            "strengths_and_weaknesses": {
                "strengths": [
                    "Consistent decision making" if success_rate > 0.8 else "Developing decision skills",
                    "High ethical awareness" if avg_ethical_weight > 0.6 else "Growing ethical understanding"
                ],
                "weaknesses": [
                    "Low success rate" if success_rate < 0.5 else "Room for improvement",
                    "Limited ethical consideration" if avg_ethical_weight < 0.3 else "Good ethical foundation"
                ]
            },
            "recommendations": [
                "Continue current approach" if success_rate > 0.8 else "Focus on decision quality",
                "Enhance ethical reasoning" if avg_ethical_weight < 0.5 else "Maintain ethical standards"
            ]
        }
        
        return {
            "success": True,
            "report": report,
            "period_days": days,
            "agent_id": agent_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get responsibility report for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export/import endpoints
@app.get("/agents/{agent_id}/export", response_model=Dict[str, Any])
async def export_agent(
    agent_id: str,
    format: str = Query("json", regex="^(json|narrative)$"),
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Export agent data."""
    try:
        agent = await tracker.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if format == "json":
            export_data = agent.to_firebase_model().dict()
        elif format == "narrative":
            export_data = agent.export_narrative_only()
        
        return {
            "success": True,
            "export_data": export_data,
            "format": format,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/backup", response_model=Dict[str, Any])
async def backup_agent(
    agent_id: str,
    tracker: NarrativeTracker = Depends(get_narrative_tracker)
):
    """Create complete backup of agent data."""
    try:
        backup_data = await tracker.backup_agent(agent_id)
        
        if not backup_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "backup": backup_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to backup agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def publish_interaction_story_event(agent_id: str, interaction_data: Dict[str, Any]):
    """Background task to publish interaction as story event for EA3 tracking."""
    try:
        story_publisher = get_story_event_publisher()
        if story_publisher:
            await story_publisher.publish_conversation_event(
                agent_id=agent_id,
                user_message=interaction_data.get('content', '')[:200],
                agent_response="Interaction processed",
                conversation_id=f"gnf-{agent_id}-{datetime.utcnow().timestamp()}",
                source_service="global-narrative-framework",
                metadata={
                    "interaction_type": interaction_data.get('type'),
                    "participants": interaction_data.get('participants', []),
                    "impact_level": interaction_data.get('impact', 'medium'),
                    "emotional_tone": interaction_data.get('emotional_tone', 'neutral')
                }
            )
            logger.debug(f"Published interaction story event for agent {agent_id}")
    except Exception as e:
        logger.error(f"Failed to publish interaction story event: {e}")


async def publish_action_story_event(agent_id: str, action_data: Dict[str, Any]):
    """Background task to publish action as story event for EA3 tracking."""
    try:
        story_publisher = get_story_event_publisher()
        if story_publisher:
            event = StoryEvent(
                agent_id=agent_id,
                event_type=StoryEventType.DECISION_MADE,
                content=f"Agent performed action: {action_data.get('description', 'Unknown action')}",
                source_service="global-narrative-framework",
                priority=StoryEventPriority.HIGH if action_data.get('ethical_weight', 0) > 0.7 else StoryEventPriority.MEDIUM,
                metadata={
                    "action_type": action_data.get('action_type'),
                    "success": action_data.get('success', True),
                    "responsibility_level": action_data.get('responsibility_level', 0.5),
                    "ethical_weight": action_data.get('ethical_weight', 0.0),
                    "intended_outcome": action_data.get('intended_outcome'),
                    "actual_outcome": action_data.get('actual_outcome')
                }
            )
            await story_publisher.publish_event(event)
            logger.debug(f"Published action story event for agent {agent_id}")
    except Exception as e:
        logger.error(f"Failed to publish action story event: {e}")


async def enhance_interaction_with_ai(agent_id: str, interaction_data: Dict[str, Any], ai_system: NarrativeAI):
    """Background task to enhance interaction with AI analysis."""
    try:
        tracker = get_narrative_tracker()
        agent = await tracker.get_agent(agent_id)
        if agent:
            interaction_record = InteractionRecord(**{
                'agent_id': agent_id,
                'interaction_type': InteractionType(interaction_data['type']),
                'content': interaction_data['content'],
                'participants': interaction_data.get('participants', []),
                'context': interaction_data.get('context', {}),
                'impact_level': ImpactLevel(interaction_data.get('impact', 'medium')),
                'emotional_tone': EmotionalTone(interaction_data.get('emotional_tone', 'neutral'))
            })
            
            enhancement = await ai_system.enhance_interaction_analysis(interaction_record, agent)
            logger.info(f"Enhanced interaction analysis for agent {agent_id}")
    except Exception as e:
        logger.error(f"Failed to enhance interaction with AI: {e}")


async def enhance_action_with_ai(action_data: Dict[str, Any], agent: AgentIdentity, ai_system: NarrativeAI):
    """Background task to enhance action with AI analysis."""
    try:
        enhancement = await ai_system.enhance_action_analysis(action_data, agent)
        logger.info(f"Enhanced action analysis for agent {agent.agent_id}")
    except Exception as e:
        logger.error(f"Failed to enhance action with AI: {e}")


# Create app instance
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    return app


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        reload=False,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )