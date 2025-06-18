#!/usr/bin/env python3
"""
Knowledge Base Search Tool for Standalone Agent

This module provides a tool for semantic search in the agent's knowledge base.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from langchain.tools import Tool
from knowledge_service import default_knowledge_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def search_knowledge_base(agent_id: str, query: str, top_k: int = 3) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        agent_id: ID of the agent
        query: The search query
        top_k: Number of results to return
        
    Returns:
        String containing the search results
    """
    logging.info(f"📚 Knowledge Base Search Tool: Executing search with query: '{query}'")
    logging.info(f"📚 Knowledge Base Search Tool: Using agent_id: {agent_id}, top_k: {top_k}")
    
    try:
        # Parse parameters from the input
        # The input could be a JSON string or just a plain query
        search_query = query
        search_top_k = top_k
        
        if isinstance(query, str) and "{" in query and "}" in query:
            try:
                # Try to parse as JSON
                query_params = json.loads(query)
                if isinstance(query_params, dict):
                    if "query" in query_params:
                        search_query = query_params["query"]
                    if "top_k" in query_params:
                        search_top_k = query_params["top_k"]
            except json.JSONDecodeError:
                # Not valid JSON, treat as plain query
                pass
        
        # Use the agent_id to search knowledge base
        logging.info(f"📚 Knowledge Base Search Tool: Executing search with query: '{search_query}'")
        logging.info(f"📚 Knowledge Base Search Tool: Using agent_id: {agent_id}, top_k: {search_top_k}")

        if not search_query:
            logging.warning("📚 Knowledge Base Search Tool: Empty search query provided")
            return "Please provide a valid search query."
            
        logging.info(f"📚 Knowledge Base Search Tool: Calling knowledge base client search")
        try:
            results = default_knowledge_client.search(
                agent_id=agent_id,
                query=search_query,
                top_k=search_top_k
            )
            logging.info(f"📚 Knowledge Base Search Tool: Received {len(results)} results from knowledge base")
        except Exception as e:
            error_msg = f"📚 Knowledge Base Search Tool: Error searching knowledge base: {str(e)}"
            logging.error(error_msg)
            return f"Error searching knowledge base: {str(e)}"
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        # Format the results with much clearer attribution
        formatted_results = []
        for i, result in enumerate(results, 1):
            # Handle results from ChromaDB service (new format)
            content = result.get('content', result.get('page_content', ''))
            file_id = result.get('file_id', 'Unknown document')
            filename = result.get('filename', 'Unknown source')
            score = result.get('score', 0.0)
            page_number = result.get('page_number', None)
            
            # Also try to get metadata from the old format as fallback
            metadata = result.get('metadata', {})
            
            formatted_result = f"Result {i}:\n"
            formatted_result += f"Source: {filename}\n"
            formatted_result += f"Document ID: {file_id}\n"
            formatted_result += f"Content: {content}"
            
            # Add relevance score
            formatted_result += f"\nRelevance: {score:.2f}"
            
            # Add page number if available
            if page_number:
                formatted_result += f"\nPage: {page_number}"
            elif 'page' in metadata:
                formatted_result += f"\nPage: {metadata['page']}"
                
            formatted_results.append(formatted_result)
        
        return "\n\n".join([
            f"Found {len(results)} relevant items in the knowledge base:",
            *formatted_results
        ])
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        return f"Error searching knowledge base: {str(e)}"


def get_knowledge_base_tools(agent_id: str) -> List[Tool]:
    """
    Get knowledge base search tool for an agent.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        List containing the knowledge base search tool
    """
    search_tool = Tool.from_function(
        func=lambda query, top_k=3: search_knowledge_base(agent_id, query, top_k),
        name="search_knowledge_base",
        description="""Search the agent's knowledge base for relevant information based on a query. 
        Use this tool when you need to find specific information that might be stored in the agent's knowledge base.
        """
    )
    
    return [search_tool]
