"""
Query Generation API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
import structlog

from app.models import (
    GenerateQueriesRequest, GenerateQueriesResponse, GeneratedQuery,
    QueryDifficulty, QueryCategory, AgentContext, QuerySettings
)
from app.services.training_service import TrainingService
from app.services.query_generation_service import QueryGenerationService
from app.middleware.auth import get_current_user, get_optional_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# Dependency injection
async def get_query_generation_service() -> QueryGenerationService:
    service = QueryGenerationService()
    await service.initialize()
    return service

async def get_training_service() -> TrainingService:
    service = TrainingService()
    await service.initialize()
    return service


@router.post("/generate", response_model=GenerateQueriesResponse, status_code=status.HTTP_200_OK)
async def generate_queries(
    request: GenerateQueriesRequest,
    query_service: QueryGenerationService = Depends(get_query_generation_service)
):
    """Generate contextual training queries for an agent"""
    try:
        # Validate agent access
        agent_id = request.agent_context.agent_id
        
        # Generate context-aware queries
        queries = await query_service.generate_queries(
            agent_context=request.agent_context,
            query_settings=request.query_settings
        )
        
        response = GenerateQueriesResponse(
            queries=queries,
            agent_id=agent_id,
            generation_metadata={
                "difficulty": request.query_settings.difficulty,
                "count_requested": request.query_settings.count,
                "count_generated": len(queries),
                "categories": [cat.value for cat in request.query_settings.categories] if request.query_settings.categories else "all"
            }
        )
        
        logger.info(
            "Queries generated successfully",
            agent_id=agent_id,
            count=len(queries),
            difficulty=request.query_settings.difficulty
        )
        
        return response
        
    except ValueError as e:
        logger.warning("Invalid query generation request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to generate queries", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate queries"
        )


@router.post("/analyze-agent", status_code=status.HTTP_200_OK)
async def analyze_agent_context(
    agent_id: str,
    query_service: QueryGenerationService = Depends(get_query_generation_service)
):
    """Analyze an agent to extract context for query generation"""
    try:
        context = await query_service.analyze_agent_context(
            agent_id=agent_id
        )
        
        logger.info(
            "Agent context analyzed",
            agent_id=agent_id
        )
        
        return {
            "agent_id": agent_id,
            "context": context,
            "analysis_metadata": {
                "analyzed_at": context.get("analyzed_at"),
                "confidence": context.get("confidence", 0.8)
            }
        }
        
    except ValueError as e:
        logger.warning("Invalid agent analysis request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to analyze agent context", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze agent context"
        )


@router.get("/categories", response_model=List[str])
async def get_query_categories():
    """Get available query categories"""
    return [category.value for category in QueryCategory]


@router.get("/difficulties", response_model=List[str])
async def get_query_difficulties():
    """Get available query difficulty levels"""
    return [difficulty.value for difficulty in QueryDifficulty]