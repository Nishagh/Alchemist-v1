#!/usr/bin/env python3
"""
Embedded Vector Search for Agent

This module provides direct ChromaDB vector search functionality embedded within the agent,
eliminating the need for API calls to a separate knowledge base service.
Based on the Knowledge Base Service implementation.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import chromadb
import openai

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddedVectorSearch:
    """
    Embedded vector search using ChromaDB directly within the agent.
    """
    
    def __init__(self, agent_id: str, openai_api_key: str, data_dir: str = None):
        """
        Initialize embedded vector search.
        
        Args:
            agent_id: Agent ID for collection isolation
            openai_api_key: OpenAI API key for embeddings
            data_dir: Directory to store ChromaDB data (defaults to local directory)
        """
        self.agent_id = agent_id
        
        # Use local directory if not specified or if /app is not writable
        if data_dir is None:
            data_dir = f"./vector_data_{agent_id}"
        elif data_dir.startswith("/app") and not os.access("/app", os.W_OK):
            data_dir = f"./vector_data_{agent_id}"
            logger.warning(f"Cannot write to {data_dir}, using local directory instead")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=str(self.data_dir))
        
        # Get or create agent-specific collection
        collection_name = self._get_safe_collection_name(agent_id)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name="text-embedding-3-small"
            )
        )
        
        logger.info(f"Initialized embedded vector search for agent {agent_id}")
        logger.info(f"Collection: {collection_name}")
        logger.info(f"Data directory: {self.data_dir}")
    
    def _get_safe_collection_name(self, agent_id: str) -> str:
        """Get a safe ChromaDB collection name for the agent."""
        # ChromaDB collection names must be 3-63 characters, alphanumeric and hyphens only
        safe_name = f"agent-{agent_id}".lower()
        safe_name = "".join(c if c.isalnum() or c == '-' else '-' for c in safe_name)
        safe_name = safe_name[:63]  # Limit to 63 characters
        
        # Ensure it starts and ends with alphanumeric
        if not safe_name[0].isalnum():
            safe_name = 'a' + safe_name[1:]
        if not safe_name[-1].isalnum():
            safe_name = safe_name[:-1] + 'z'
            
        return safe_name
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean metadata to ensure ChromaDB compatibility.
        ChromaDB requires metadata values to be strings, numbers, or booleans (not None).
        """
        cleaned = {}
        
        for key, value in metadata.items():
            if value is None:
                # Convert None to empty string
                cleaned[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                # Keep valid types as-is
                cleaned[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to JSON strings
                import json
                try:
                    cleaned[key] = json.dumps(value)
                except (TypeError, ValueError):
                    cleaned[key] = str(value)
            else:
                # Convert everything else to string
                cleaned[key] = str(value)
        
        return cleaned
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database for relevant content.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with content, metadata, and scores
        """
        try:
            logger.info(f"Searching vectors for query: '{query}' (top_k={top_k})")
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or not results.get('documents') or not results['documents'][0]:
                logger.info("No results found")
                return []
            
            # Format results
            formatted_results = []
            documents = results['documents'][0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            for i, document in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 1.0
                
                # Convert distance to similarity score (ChromaDB uses cosine distance)
                similarity_score = 1.0 - distance
                
                result = {
                    'content': document,
                    'file_id': metadata.get('file_id', 'unknown'),
                    'filename': metadata.get('filename', 'unknown'),
                    'page_number': metadata.get('page_number'),
                    'score': similarity_score,
                    'agent_id': self.agent_id
                }
                
                formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    def add_text(self, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Add text content to the vector database.
        
        Args:
            content: Text content to add
            metadata: Metadata associated with the content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate a unique ID for this content
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Ensure agent_id is in metadata
            metadata['agent_id'] = self.agent_id
            
            # Clean metadata to ensure ChromaDB compatibility
            cleaned_metadata = self._clean_metadata(metadata)
            
            # Add to collection
            self.collection.add(
                documents=[content],
                metadatas=[cleaned_metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Added vector directly with ID {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vector directly: {str(e)}")
            return False
    
    def add_vector_directly(self, content: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """
        Add content with pre-computed embedding vector directly to the database.
        This bypasses OpenAI API calls and uses existing embeddings.
        
        Args:
            content: Text content
            embedding: Pre-computed embedding vector
            metadata: Metadata associated with the content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate a unique ID for this content
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Ensure agent_id is in metadata
            metadata['agent_id'] = self.agent_id
            
            # Clean metadata to ensure ChromaDB compatibility
            cleaned_metadata = self._clean_metadata(metadata)
            
            # Add to collection with pre-computed embedding
            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[cleaned_metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Added vector directly with ID {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vector directly: {str(e)}")
            return False
    
    def delete_by_file_id(self, file_id: str) -> bool:
        """
        Delete all vectors associated with a file ID.
        
        Args:
            file_id: File ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Query for documents with this file_id
            results = self.collection.get(
                where={"file_id": file_id}
            )
            
            if results and results.get('ids'):
                # Delete the documents
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} vectors for file_id {file_id}")
                return True
            else:
                logger.info(f"No vectors found for file_id {file_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting vectors for file_id {file_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection."""
        try:
            count = self.collection.count()
            return {
                'agent_id': self.agent_id,
                'total_vectors': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}
    
    def sync_document_vectors(self, file_id: str, vectors_data: List[Dict[str, Any]], force_refresh: bool = False) -> bool:
        """
        Sync vectors for a specific document by replacing all existing vectors.
        
        Args:
            file_id: File ID to sync
            vectors_data: List of vector data with content and metadata
            force_refresh: If True, always delete and re-add vectors. If False, check if sync is needed.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if vectors already exist and match the expected count
            if not force_refresh:
                existing_results = self.collection.get(where={"file_id": file_id})
                existing_count = len(existing_results.get('ids', [])) if existing_results else 0
                expected_count = len(vectors_data)
                
                if existing_count == expected_count and existing_count > 0:
                    logger.info(f"Vectors for file {file_id} already synced ({existing_count} vectors), skipping")
                    return True
            
            # Delete existing vectors for this file
            self.delete_by_file_id(file_id)
            
            # Add new vectors
            success_count = 0
            for vector_data in vectors_data:
                content = vector_data.get('content', '')
                metadata = vector_data.get('metadata', {})
                embedding = vector_data.get('embedding')  # Pre-computed embedding vector
                
                # Ensure file_id and agent_id are in metadata
                metadata['file_id'] = file_id
                metadata['agent_id'] = self.agent_id
                
                # Use pre-computed embedding if available, otherwise generate new one
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    if self.add_vector_directly(content, embedding, metadata):
                        success_count += 1
                else:
                    # Fallback to generating new embedding (old behavior)
                    logger.warning(f"No pre-computed embedding found for vector, generating new one")
                    if self.add_text(content, metadata):
                        success_count += 1
            
            logger.info(f"Synced {success_count}/{len(vectors_data)} vectors for file {file_id}")
            return success_count == len(vectors_data)
            
        except Exception as e:
            logger.error(f"Error syncing document vectors for {file_id}: {str(e)}")
            return False
    
    def get_files_in_collection(self) -> List[str]:
        """
        Get list of unique file IDs in the collection.
        
        Returns:
            List of file IDs
        """
        try:
            # Get all documents in the collection
            results = self.collection.get()
            
            if not results or not results.get('metadatas'):
                return []
            
            # Extract unique file IDs
            file_ids = set()
            for metadata in results['metadatas']:
                if metadata and metadata.get('file_id'):
                    file_ids.add(metadata['file_id'])
            
            return list(file_ids)
            
        except Exception as e:
            logger.error(f"Error getting files in collection: {str(e)}")
            return []
    
    def get_document_count_by_file(self, file_id: str) -> int:
        """
        Get count of vectors for a specific file.
        
        Args:
            file_id: File ID to count
            
        Returns:
            Number of vectors for the file
        """
        try:
            results = self.collection.get(
                where={"file_id": file_id}
            )
            
            return len(results.get('ids', [])) if results else 0
            
        except Exception as e:
            logger.error(f"Error getting document count for {file_id}: {str(e)}")
            return 0
    
    def bulk_add_texts(self, texts_with_metadata: List[Dict[str, Any]]) -> int:
        """
        Add multiple texts in a single operation for better performance.
        
        Args:
            texts_with_metadata: List of dicts with 'content' and 'metadata' keys
            
        Returns:
            Number of successfully added texts
        """
        try:
            import uuid
            
            documents = []
            metadatas = []
            ids = []
            
            for item in texts_with_metadata:
                content = item.get('content', '')
                metadata = item.get('metadata', {})
                
                # Ensure agent_id is in metadata
                metadata['agent_id'] = self.agent_id
                
                # Clean metadata to ensure ChromaDB compatibility
                cleaned_metadata = self._clean_metadata(metadata)
                
                documents.append(content)
                metadatas.append(cleaned_metadata)
                ids.append(str(uuid.uuid4()))
            
            # Add all documents at once
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Bulk added {len(documents)} texts to collection")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error bulk adding texts: {str(e)}")
            return 0


def create_embedded_vector_tools(agent_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    
    Args:
        agent_config: Agent configuration containing agent_id and openai_api_key
        
    Returns:
        List of tool definitions for vector operations
    """
    tools = []
    
    try:
        agent_id = agent_config.get('agent_id')
        openai_api_key = agent_config.get('openai_api_key')
        
        if not agent_id or not openai_api_key:
            logger.warning("Missing agent_id or openai_api_key for embedded vector search")
            return tools
        
        # Initialize embedded vector search
        vector_search = EmbeddedVectorSearch(
            agent_id=agent_id,
            openai_api_key=openai_api_key
        )
        
        def search_vectors(query: str, top_k: int = 5) -> str:
            """Search the embedded vector database for relevant information."""
            try:
                results = vector_search.search(query, top_k)
                
                if not results:
                    return "No relevant information found in the knowledge base."
                
                # Format results for the agent
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_result = f"Result {i}:\n"
                    formatted_result += f"Source: {result.get('filename', 'Unknown')}\n"
                    formatted_result += f"Content: {result.get('content', '')}\n"
                    formatted_result += f"Relevance: {result.get('score', 0):.2f}"
                    
                    if result.get('page_number'):
                        formatted_result += f"\nPage: {result['page_number']}"
                    
                    formatted_results.append(formatted_result)
                
                return f"Found {len(results)} relevant items in the knowledge base:\n\n" + "\n\n".join(formatted_results)
                
            except Exception as e:
                logger.error(f"Error in embedded vector search: {str(e)}")
                return f"Error searching knowledge base: {str(e)}"
        
        def add_to_vectors(content: str, filename: str = "agent_generated", source: str = "conversation") -> str:
            """Add new information to the embedded vector database."""
            try:
                metadata = {
                    'filename': filename,
                    'source': source,
                    'file_id': f"agent_generated_{agent_id}_{int(time.time())}"
                }
                
                success = vector_search.add_text(content, metadata)
                
                if success:
                    return "Successfully added information to the knowledge base."
                else:
                    return "Failed to add information to the knowledge base."
                    
            except Exception as e:
                logger.error(f"Error adding to embedded vectors: {str(e)}")
                return f"Error adding to knowledge base: {str(e)}"
        
        def get_kb_stats() -> str:
            """Get statistics about the knowledge base."""
            try:
                stats = vector_search.get_collection_stats()
                return f"Knowledge Base Statistics:\n" \
                       f"- Agent ID: {stats.get('agent_id', 'Unknown')}\n" \
                       f"- Total vectors: {stats.get('total_vectors', 0)}\n" \
                       f"- Collection: {stats.get('collection_name', 'Unknown')}"
            except Exception as e:
                return f"Error getting knowledge base statistics: {str(e)}"
        
        # Create tool definitions using direct function calls
        search_tool = {
            "name": "search_embedded_knowledge_base",
            "description": "Search the agent's embedded knowledge base for relevant information. Use this when you need to find specific information that might be stored in the agent's knowledge base.",
            "function": search_vectors
        }
        
        add_tool = {
            "name": "add_to_embedded_knowledge_base",
            "description": "Add new information to the agent's embedded knowledge base for future reference. Use this to store important information learned during conversations.",
            "function": add_to_vectors
        }
        
        stats_tool = {
            "name": "knowledge_base_stats",
            "description": "Get statistics about the agent's knowledge base, including the number of stored documents.",
            "function": get_kb_stats
        }
        
        tools.extend([search_tool, add_tool, stats_tool])
        logger.info(f"Created {len(tools)} embedded vector search tools")
        
    except Exception as e:
        logger.error(f"Error creating embedded vector tools: {str(e)}")
    
    return tools


# Import time for timestamp generation
import time