"""
Main FastAPI application for the Accountable AI Agent
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from core.accountable_agent import AccountableAgent, get_agent, initialize_agent
from core.conversation_manager import ConversationResult
from config.settings import settings
from config.accountability_config import accountability_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global agent instance
global_agent: Optional[AccountableAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global global_agent
    
    try:
        # Initialize agent on startup
        logger.info(f"Initializing agent with ID: {settings.agent_id}")
        global_agent = await initialize_agent(settings.agent_id)
        logger.info("Agent initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise
    finally:
        # Cleanup on shutdown
        if global_agent:
            await global_agent.shutdown()
            logger.info("Agent shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="Accountable AI Agent",
    description="AI Agent with comprehensive accountability tracking via GNF integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    user_id: Optional[str] = Field(None, description="User ID")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponse(BaseModel):
    success: bool
    response: str
    conversation_id: str
    token_usage: Dict[str, int]
    accountability_data: Dict[str, Any]
    error: Optional[str] = None


class ConversationCreate(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID")


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    description: str
    model: str
    initialized: bool
    tools_count: int
    knowledge_base_enabled: bool
    mcp_enabled: bool
    accountability_enabled: bool
    development_stage: str
    narrative_coherence_score: float
    responsibility_score: float
    version: str
    last_updated: Optional[str]


# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_id": settings.agent_id,
        "service": "Accountable AI Agent",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    health_status = await global_agent.health_check()
    
    if health_status.get("overall_healthy", False):
        return health_status
    else:
        return JSONResponse(
            status_code=503,
            content=health_status
        )


@app.get("/agent/info", response_model=AgentInfo)
async def get_agent_info():
    """Get agent information"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    info = global_agent.get_agent_info()
    
    if "error" in info:
        raise HTTPException(status_code=500, detail=info["error"])
    
    return info


@app.post("/conversations", response_model=Dict[str, str])
async def create_conversation(request: ConversationCreate):
    """Create a new conversation"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        conversation_id = await global_agent.create_conversation(request.user_id)
        return {"conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the agent"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Create conversation if not provided
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await global_agent.create_conversation(request.user_id)
        
        # Handle streaming
        if request.stream:
            return StreamingResponse(
                _stream_chat_response(conversation_id, request.message, request.user_id),
                media_type="text/plain"
            )
        
        # Regular chat
        result = await global_agent.process_message(
            conversation_id=conversation_id,
            message=request.message,
            user_id=request.user_id
        )
        
        return ChatResponse(
            success=result.success,
            response=result.response,
            conversation_id=result.conversation_id,
            token_usage={
                "prompt_tokens": result.token_usage.prompt_tokens,
                "completion_tokens": result.token_usage.completion_tokens,
                "total_tokens": result.token_usage.total_tokens
            },
            accountability_data=result.accountability_data,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_chat_response(conversation_id: str, message: str, user_id: Optional[str]):
    """Stream chat response"""
    global global_agent
    
    try:
        async for chunk in global_agent.stream_response(
            conversation_id=conversation_id,
            message=message,
            user_id=user_id
        ):
            yield f"data: {chunk}\n\n"
            
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: Error: {str(e)}\n\n"


@app.get("/conversations/{conversation_id}/stats")
async def get_conversation_stats(conversation_id: str):
    """Get conversation statistics"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    stats = await global_agent.get_conversation_stats(conversation_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return stats


@app.get("/agent/accountability")
async def get_accountability_summary():
    """Get accountability summary"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    summary = await global_agent.get_accountability_summary()
    
    if "error" in summary:
        raise HTTPException(status_code=500, detail=summary["error"])
    
    return summary


@app.get("/agent/token-usage")
async def get_token_usage():
    """Get token usage statistics"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    usage = global_agent.get_token_usage()
    
    if "error" in usage:
        raise HTTPException(status_code=500, detail=usage["error"])
    
    return usage


@app.get("/agent/tools")
async def get_available_tools():
    """Get available tools"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        tools = await global_agent._get_available_tools()
        return {"tools": tools, "count": len(tools)}
    except Exception as e:
        logger.error(f"Failed to get tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get agent configuration"""
    return {
        "agent_id": settings.agent_id,
        "enable_gnf": settings.enable_gnf,
        "max_tokens": settings.max_tokens,
        "conversation_memory_limit": settings.conversation_memory_limit,
        "story_loss_threshold": settings.story_loss_threshold,
        "accountability_thresholds": {
            "story_loss_warning": accountability_config.thresholds.story_loss_warning,
            "story_loss_critical": accountability_config.thresholds.story_loss_critical,
            "responsibility_warning": accountability_config.thresholds.responsibility_warning,
            "coherence_warning": accountability_config.thresholds.coherence_warning
        },
        "development_stages": [stage.value for stage in accountability_config.development_stages],
        "self_reflection_enabled": accountability_config.self_reflection_settings.enable_automatic_reflection
    }


@app.post("/agent/reflect")
async def trigger_self_reflection():
    """Manually trigger self-reflection"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # This would trigger the agent's self-reflection mechanism
        # For now, just return a success message
        return {
            "success": True,
            "message": "Self-reflection triggered successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger self-reflection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/narrative-state")
async def get_narrative_state():
    """Get current narrative state"""
    global global_agent
    
    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # This would return the current narrative state from GNF
        # For now, return basic state information
        return {
            "agent_id": settings.agent_id,
            "development_stage": "nascent",  # This would come from GNF
            "narrative_coherence_score": 0.5,
            "responsibility_score": 0.5,
            "experience_points": 0,
            "total_interactions": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get narrative state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )