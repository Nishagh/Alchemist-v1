"""
Agent Generation Service Module

This module provides functions to generate agent metadata like names,
descriptions, and purpose statements using GPT-4o model.
"""
import logging
from typing import Dict, Any

from .openai_service import default_openai_service

logger = logging.getLogger(__name__)


async def generate_agent_name(message: str) -> str:
    """
    Generate a suitable name for an agent based on the user message.
    
    Args:
        message: The user message describing what they want the agent to do
        
    Returns:
        A concise, appropriate name for the agent
    """
    # Get the OpenAI chat model
    chat_model = default_openai_service.get_chat_model(model="gpt-4o", temperature=0.7)
    
    # Define the prompt
    prompt = [
        {"role": "system", "content": "You are a helpful AI assistant that generates concise, professional names for AI agents based on their purpose."},
        {"role": "user", "content": f"Generate a short, professional name (2-4 words) for an AI agent that will: {message}. Only respond with the name, nothing else."}
    ]
    
    # Generate the name
    try:
        response = await chat_model.ainvoke(prompt)
        agent_name = response.content.strip()
        # Ensure the name is not too long
        if len(agent_name.split()) > 5:
            # Try to extract a shorter version
            agent_name = " ".join(agent_name.split()[:4])
        return agent_name
    except Exception as e:
        logger.error(f"Error generating agent name: {str(e)}")
        return "Custom Assistant"  # Fallback name


async def generate_agent_description(message: str) -> str:
    """
    Generate a brief description for an agent based on the user message.
    
    Args:
        message: The user message describing what they want the agent to do
        
    Returns:
        A concise description of the agent's capabilities
    """
    # Get the OpenAI chat model
    chat_model = default_openai_service.get_chat_model(model="gpt-4o", temperature=0.7)
    
    # Define the prompt
    prompt = [
        {"role": "system", "content": "You are a helpful AI assistant that generates concise, professional descriptions for AI agents."},
        {"role": "user", "content": f"Generate a brief description (1-2 sentences) for an AI agent that will: {message}. Focus on what the agent does and its key capabilities. Only respond with the description, nothing else."}
    ]
    
    # Generate the description
    try:
        response = await chat_model.ainvoke(prompt)
        description = response.content.strip()
        return description
    except Exception as e:
        logger.error(f"Error generating agent description: {str(e)}")
        return f"An assistant that helps with: {message[:50]}..."  # Fallback description


async def generate_agent_purpose(message: str) -> str:
    """
    Generate a clear statement of purpose for an agent based on the user message.
    
    Args:
        message: The user message describing what they want the agent to do
        
    Returns:
        A clear, specific statement of the agent's purpose
    """
    # Get the OpenAI chat model
    chat_model = default_openai_service.get_chat_model(model="gpt-4o", temperature=0.7)
    
    # Define the prompt
    prompt = [
        {"role": "system", "content": "You are a helpful AI assistant that generates clear purpose statements for AI agents."},
        {"role": "user", "content": f"Generate a clear, specific statement of purpose (1 sentence) for an AI agent that will: {message}. The statement should begin with 'To' followed by a verb. Only respond with the purpose statement, nothing else."}
    ]
    
    # Generate the purpose statement
    try:
        response = await chat_model.ainvoke(prompt)
        purpose = response.content.strip()
        return purpose
    except Exception as e:
        logger.error(f"Error generating agent purpose: {str(e)}")
        return f"To assist with {message[:40]}..."  # Fallback purpose
