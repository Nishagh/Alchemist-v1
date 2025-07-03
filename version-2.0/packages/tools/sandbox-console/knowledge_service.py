#!/usr/bin/env python3
"""
Knowledge Base Service Client for Standalone Agent

This module provides a client for semantic search functionality with the Knowledge Base Service.
"""
import os
import logging
import requests
from typing import Dict, Any, List, Optional
from alchemist_shared.config.base_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeBaseClient:
    """Client for searching the Knowledge Base Service."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Knowledge Base client.
        
        Args:
            base_url: URL of the Knowledge Base Service. If None, uses environment variable.
        """
        settings = BaseSettings()
        # Use specified knowledge vault URL as default
        self.base_url = base_url or settings.get_service_url("knowledge-vault") or os.environ.get("KNOWLEDGE_BASE_URL", "https://alchemist-knowledge-vault-851487020021.us-central1.run.app")
        logger.info(f"Initialized Knowledge Base client with URL: {self.base_url}")
    
    def search(self, agent_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base.
        
        Args:
            agent_id: ID of the agent
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of search results
        """
        logging.info(f"🔍 Knowledge Base Service: Searching knowledge base for agent '{agent_id}'")
        logging.info(f"🔍 Knowledge Base Service: Query: '{query}', top_k: {top_k}")
        logging.info(f"🔍 Knowledge Base Service: API endpoint: {self.base_url}/api/search-knowledge-base")
        
        search_data = {
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k
        }
        
        try:
            logging.info(f"🔍 Knowledge Base Service: Sending request to knowledge base service")
            response = requests.post(
                f"{self.base_url}/api/search-knowledge-base/storage",
                json=search_data,
                timeout=30  # Increased timeout for knowledge base search
            )
            logging.info(f"🔍 Knowledge Base Service: Received response with status code: {response.status_code}")
        except requests.exceptions.Timeout:
            logging.error("🔍 Knowledge Base Service: Request timed out when connecting to knowledge base service")
            return []
        except requests.exceptions.ConnectionError as e:
            logging.error(f"🔍 Knowledge Base Service: Connection error: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"🔍 Knowledge Base Service: Unexpected error: {str(e)}")
            return []
        
        # Check response
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Error searching knowledge base: {error_text}")
            raise Exception(f"Error searching knowledge base: {error_text}")
        
        # Parse response
        result = response.json()
        logger.info(f"Search completed, found {len(result.get('results', []))} results")
        return result.get('results', [])
    
    def get_knowledge_base_files(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get the knowledge base files for an agent."""
        logging.info(f"🔍 Knowledge Base Service: Getting knowledge base files for agent '{agent_id}'")
        logging.info(f"🔍 Knowledge Base Service: API endpoint: {self.base_url}/api/knowledge-base/{agent_id}/files")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/knowledge-base/{agent_id}/files",
                timeout=30
            )
            result = response.json()
            logging.info(f"🔍 Knowledge Base Service: Received response: {result}")
            logging.info(f"🔍 Knowledge Base Service: Received response with status code: {response.status_code}")
        except requests.exceptions.Timeout:
            logging.error("🔍 Knowledge Base Service: Request timed out when connecting to knowledge base service")
            return []
        
    def get_knowledge_base_vectors(self, agent_id: str, file_id: str) -> List[Dict[str, Any]]:
        """Get the knowledge base vectors for an agent."""
        logging.info(f"🔍 Knowledge Base Service: Getting knowledge base vectors for agent '{agent_id}'")
        logging.info(f"🔍 Knowledge Base Service: API endpoint: {self.base_url}/api/knowledge-base/files/{file_id}/vectors")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/knowledge-base/{agent_id}/vector-files",
                timeout=30
            )
            result = response.json()
            logging.info(f"🔍 Knowledge Base Service: Received response: {result}")
            logging.info(f"🔍 Knowledge Base Service: Received response with status code: {response.status_code}")
        except requests.exceptions.Timeout:
            logging.error("🔍 Knowledge Base Service: Request timed out when connecting to knowledge base service")
            return []
        except requests.exceptions.ConnectionError as e:
            logging.error(f"🔍 Knowledge Base Service: Connection error: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"🔍 Knowledge Base Service: Unexpected error: {str(e)}")
            return []

# Create a default client instance
default_knowledge_client = KnowledgeBaseClient()
