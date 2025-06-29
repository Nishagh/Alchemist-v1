"""
Usage tracking routes for the Alchemist Billing Service
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
from datetime import datetime, timedelta

from app.services.firebase_service import FirebaseService
from app.middleware.auth_middleware import get_firebase_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/usage/{agent_id}")
async def get_agent_usage(
    agent_id: str,
    user_id: str = Query(..., description="User ID who owns the agent"),
    start_date: Optional[str] = Query(None, description="Start date for usage data (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date for usage data (ISO format)"),
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """
    Get usage data for a specific agent
    """
    try:
        logger.info(f"Getting usage data for agent {agent_id} owned by user {user_id}")
        
        # Verify the user owns this agent
        agent_ref = firebase.db.collection('agents').document(agent_id)
        agent_doc = agent_ref.get()
        
        if not agent_doc.exists:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found"
            )
        
        agent_data = agent_doc.to_dict()
        if agent_data.get('userId') != user_id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this agent's usage data"
            )
        
        # Set default date range (last 30 days if not specified)
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Get conversations for usage calculation
        conversations_ref = firebase.db.collection('conversations').document(agent_id)
        conversations_doc = conversations_ref.get()
        
        usage_data = {
            "agent_id": agent_id,
            "user_id": user_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "total_conversations": 0,
                "total_messages": 0,
                "total_api_calls": 0,
                "compute_time_minutes": 0,
                "storage_mb": 0
            },
            "costs": {
                "api_costs": 0.0,
                "compute_costs": 0.0,
                "storage_costs": 0.0,
                "total_cost": 0.0
            },
            "performance": {
                "avg_response_time_ms": 0,
                "success_rate": 0,
                "user_satisfaction": 0
            }
        }
        
        if conversations_doc.exists:
            # Get messages from the conversation
            messages_ref = firebase.db.collection('conversations').document(agent_id).collection('messages')
            messages_query = messages_ref.where('timestamp', '>=', start_date).where('timestamp', '<=', end_date)
            messages_docs = messages_query.get()
            
            total_messages = len(messages_docs)
            total_api_calls = total_messages  # Rough estimate
            
            # Calculate costs based on usage
            api_cost_per_call = 0.002  # $0.002 per API call
            compute_cost_per_minute = 0.02  # $0.02 per minute
            storage_cost_per_mb = 0.001  # $0.001 per MB
            
            # Estimate compute time (2 seconds per message)
            compute_time_minutes = (total_messages * 2) / 60
            
            # Estimate storage (500 bytes per message)
            storage_mb = (total_messages * 500) / (1024 * 1024)
            
            api_costs = total_api_calls * api_cost_per_call
            compute_costs = compute_time_minutes * compute_cost_per_minute
            storage_costs = storage_mb * storage_cost_per_mb
            total_cost = api_costs + compute_costs + storage_costs
            
            # Calculate response times
            response_times = []
            successful_messages = 0
            user_ratings = []
            
            for msg_doc in messages_docs:
                msg_data = msg_doc.to_dict()
                if msg_data.get('response_time_ms'):
                    response_times.append(msg_data['response_time_ms'])
                if msg_data.get('role') == 'assistant' and msg_data.get('content'):
                    successful_messages += 1
                if msg_data.get('user_rating'):
                    user_ratings.append(msg_data['user_rating'])
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            success_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0
            avg_user_satisfaction = sum(user_ratings) / len(user_ratings) if user_ratings else 0
            
            usage_data.update({
                "metrics": {
                    "total_conversations": 1 if total_messages > 0 else 0,
                    "total_messages": total_messages,
                    "total_api_calls": total_api_calls,
                    "compute_time_minutes": round(compute_time_minutes, 2),
                    "storage_mb": round(storage_mb, 4)
                },
                "costs": {
                    "api_costs": round(api_costs, 4),
                    "compute_costs": round(compute_costs, 4),
                    "storage_costs": round(storage_costs, 4),
                    "total_cost": round(total_cost, 2)
                },
                "performance": {
                    "avg_response_time_ms": round(avg_response_time),
                    "success_rate": round(success_rate, 1),
                    "user_satisfaction": round(avg_user_satisfaction, 1)
                }
            })
        
        logger.info(f"Retrieved usage data for agent {agent_id}: {usage_data['costs']['total_cost']} total cost")
        
        return {
            "success": True,
            "data": usage_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage data for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve usage data: {str(e)}"
        )


@router.get("/usage/user/{user_id}/summary")
async def get_user_usage_summary(
    user_id: str,
    start_date: Optional[str] = Query(None, description="Start date for usage data (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date for usage data (ISO format)"),
    firebase: FirebaseService = Depends(get_firebase_service)
):
    """
    Get usage summary for all agents owned by a user
    """
    try:
        logger.info(f"Getting usage summary for user {user_id}")
        
        # Set default date range (last 30 days if not specified)
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Get all agents for the user
        agents_ref = firebase.db.collection('agents')
        agents_query = agents_ref.where('userId', '==', user_id)
        agents_docs = agents_query.get()
        
        total_cost = 0
        total_messages = 0
        total_agents = len(agents_docs)
        agent_costs = []
        
        for agent_doc in agents_docs:
            agent_id = agent_doc.id
            agent_data = agent_doc.to_dict()
            
            # Get conversations for this agent
            conversations_ref = firebase.db.collection('conversations').document(agent_id)
            conversations_doc = conversations_ref.get()
            
            agent_cost = 0
            agent_messages = 0
            
            if conversations_doc.exists:
                # Get messages from the conversation
                messages_ref = firebase.db.collection('conversations').document(agent_id).collection('messages')
                messages_query = messages_ref.where('timestamp', '>=', start_date).where('timestamp', '<=', end_date)
                messages_docs = messages_query.get()
                
                agent_messages = len(messages_docs)
                
                # Calculate costs
                api_costs = agent_messages * 0.002
                compute_costs = (agent_messages * 2 / 60) * 0.02
                storage_costs = (agent_messages * 500 / (1024 * 1024)) * 0.001
                agent_cost = api_costs + compute_costs + storage_costs
            
            total_cost += agent_cost
            total_messages += agent_messages
            
            agent_costs.append({
                "agent_id": agent_id,
                "agent_name": agent_data.get('name', f'Agent {agent_id[:8]}'),
                "messages": agent_messages,
                "cost": round(agent_cost, 2)
            })
        
        # Sort agents by cost (highest first)
        agent_costs.sort(key=lambda x: x['cost'], reverse=True)
        
        summary = {
            "user_id": user_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_agents": total_agents,
                "total_messages": total_messages,
                "total_cost": round(total_cost, 2),
                "avg_cost_per_agent": round(total_cost / total_agents, 2) if total_agents > 0 else 0,
                "avg_cost_per_message": round(total_cost / total_messages, 4) if total_messages > 0 else 0
            },
            "agent_breakdown": agent_costs[:10]  # Top 10 most expensive agents
        }
        
        logger.info(f"Retrieved usage summary for user {user_id}: {total_cost} total cost across {total_agents} agents")
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting usage summary for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve usage summary: {str(e)}"
        )