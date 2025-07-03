"""
Embedded Knowledge Service - Local semantic search with embeddings
"""

import logging
import asyncio
import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib

# Import embedding and vector search dependencies
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy/sklearn not available. Install with: pip install numpy scikit-learn")

from services.tool_registry import ToolRegistry
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddedKnowledgeService:
    """
    Self-contained knowledge service with local embedding search
    Implements knowledge-vault-like functionality within the agent
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dim = 1536
        
        # Local storage paths
        self.knowledge_path = Path(f"knowledge_data/{agent_id}")
        self.embeddings_path = self.knowledge_path / "embeddings"
        self.documents_path = self.knowledge_path / "documents"
        self.index_path = self.knowledge_path / "index.json"
        
        # Create directories
        self.knowledge_path.mkdir(parents=True, exist_ok=True)
        self.embeddings_path.mkdir(exist_ok=True)
        self.documents_path.mkdir(exist_ok=True)
        
        # Initialize OpenAI client
        self.openai_client = None
        if OPENAI_AVAILABLE:
            # Try to use alchemist-shared OpenAI service first
            openai_service = settings.get_openai_service()
            if openai_service and hasattr(openai_service, 'api_key'):
                self.openai_client = AsyncOpenAI(api_key=openai_service.api_key)
            else:
                api_key = settings.get_openai_api_key()
                if api_key:
                    self.openai_client = AsyncOpenAI(api_key=api_key)
        
        # In-memory cache
        self.embeddings_cache = {}
        self.documents_cache = {}
        self.index_cache = None
        
        logger.info(f"Embedded knowledge service initialized for agent {agent_id}")
    
    async def _load_from_firestore(self):
        """Load knowledge files and embeddings from Firestore"""
        try:
            from services.firebase_service import firebase_service
            
            # Load knowledge files by querying for documents with this agent_id
            knowledge_files = await firebase_service.query_documents('knowledge_files', 'agent_id', self.agent_id)
            files_count = len(knowledge_files)
            
            # Store files in documents cache
            for file_data in knowledge_files:
                file_id = file_data.get('id')
                if file_id:
                    self.documents_cache[file_id] = file_data
            
            # Load embeddings
            documents = await firebase_service.get_documents(f"knowledge_embeddings/{self.agent_id}/embeddings")
            for document in documents:
                if 'embedding' in document:
                    embeddings = document['embedding']
                    if isinstance(embeddings, list):
                        embeddings_count = len(embeddings)
                        logger.info(f"Found {embeddings_count} embeddings in Firestore")
                        
                        # Store embeddings in local cache format
                        for i, embedding_data in enumerate(embeddings):
                            try:
                                if isinstance(embedding_data, dict):
                                    chunk_id = embedding_data.get('chunk_id', f'chunk_{i}')
                                    self.embeddings_cache[chunk_id] = {
                                        'embedding': np.array(embedding_data.get('vector', [])),
                                        'content': embedding_data.get('content', ''),
                                        'metadata': embedding_data.get('metadata', {})
                                    }
                                elif isinstance(embedding_data, (list, float)):
                                    # Handle case where embedding is just a vector array
                                    chunk_id = f'chunk_{i}'
                                    self.embeddings_cache[chunk_id] = {
                                        'embedding': np.array(embedding_data if isinstance(embedding_data, list) else [embedding_data]),
                                        'content': f'Chunk {i}',
                                        'metadata': {}
                                    }
                            except Exception as e:
                                logger.warning(f"Failed to process embedding {i}: {e}")
                                continue
            
            # Update documents cache count
            total_chunks = len(self.embeddings_cache)
            
            logger.info(f"Loaded {files_count} documents and {total_chunks} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to load from Firestore: {e}")
    
    async def initialize(self):
        """Initialize the knowledge service and load existing data"""
        try:
            await self._load_from_firestore()
            await self._load_index()
            await self._load_embeddings_cache()
            logger.info(f"Knowledge service initialized with {len(self.documents_cache)} documents")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge service: {e}")
    
    async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base using local embeddings
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with similarity scores
        """
        try:
            if not self.openai_client:
                logger.warning("OpenAI client not available for embeddings")
                return []
            
            if not NUMPY_AVAILABLE:
                logger.warning("NumPy/sklearn not available for similarity search")
                return []
            
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            if query_embedding is None:
                return []
            
            # Load all embeddings if not cached
            await self._ensure_embeddings_loaded()
            
            # Calculate similarities
            results = []
            for doc_id, doc_data in self.documents_cache.items():
                if doc_id in self.embeddings_cache:
                    doc_embedding = self.embeddings_cache[doc_id]
                    similarity = self._calculate_similarity(query_embedding, doc_embedding)
                    
                    results.append({
                        'content': doc_data.get('content', ''),
                        'filename': doc_data.get('filename', 'Unknown'),
                        'file_id': doc_data.get('file_id', doc_id),
                        'chunk_index': doc_data.get('chunk_index', 0),
                        'page_number': doc_data.get('page_number', ''),
                        'similarity_score': float(similarity),
                        'metadata': doc_data.get('metadata', {})
                    })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:top_k]
            
            logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
            return results
                
        except Exception as e:
            logger.error(f"Knowledge search error: {e}")
            return []
    
    async def add_document(self, content: str, filename: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a document to the knowledge base
        
        Args:
            content: Document content
            filename: Original filename
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        try:
            # Generate document ID
            doc_id = hashlib.md5(f"{filename}_{content[:100]}".encode()).hexdigest()
            
            # Process content into chunks
            chunks = self._chunk_content(
                content, 
                filename, 
                chunk_size=settings.knowledge_chunk_size,
                overlap=settings.knowledge_chunk_overlap
            )
            
            # Generate embeddings for each chunk
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                
                # Generate embedding
                embedding = await self._generate_embedding(chunk['content'])
                if embedding is not None:
                    # Store chunk data
                    chunk_data = {
                        'content': chunk['content'],
                        'filename': filename,
                        'file_id': doc_id,
                        'chunk_index': i,
                        'page_number': chunk.get('page_number', ''),
                        'metadata': metadata or {},
                        'created_at': datetime.utcnow().isoformat()
                    }
                    
                    # Save to cache and disk
                    self.documents_cache[chunk_id] = chunk_data
                    self.embeddings_cache[chunk_id] = embedding
                    
                    # Save chunk to disk
                    await self._save_chunk(chunk_id, chunk_data, embedding)
            
            # Update index
            await self._update_index(doc_id, filename, len(chunks), metadata)
            
            logger.info(f"Added document {filename} with {len(chunks)} chunks")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def get_agent_files(self) -> List[Dict[str, Any]]:
        """
        Get all files indexed for this agent
        
        Returns:
            List of agent files with metadata
        """
        try:
            await self._load_index()
            
            if not self.index_cache:
                return []
            
            files = []
            for file_id, file_info in self.index_cache.get('files', {}).items():
                files.append({
                    'id': file_id,
                    'filename': file_info.get('filename', 'Unknown'),
                    'chunk_count': file_info.get('chunk_count', 0),
                    'created_at': file_info.get('created_at', ''),
                    'metadata': file_info.get('metadata', {})
                })
            
            logger.info(f"Retrieved {len(files)} files for agent {self.agent_id}")
            return files
                
        except Exception as e:
            logger.error(f"Error retrieving agent files: {e}")
            return []
    
    async def get_file_embeddings(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get embeddings for a specific file
        
        Args:
            file_id: File identifier
            
        Returns:
            List of file embeddings/chunks
        """
        try:
            await self._ensure_embeddings_loaded()
            
            embeddings = []
            for chunk_id, chunk_data in self.documents_cache.items():
                if chunk_data.get('file_id') == file_id:
                    embeddings.append(chunk_data)
            
            # Sort by chunk index
            embeddings.sort(key=lambda x: x.get('chunk_index', 0))
            
            logger.info(f"Retrieved {len(embeddings)} embeddings for file {file_id}")
            return embeddings
                
        except Exception as e:
            logger.error(f"Error retrieving file embeddings: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text using OpenAI"""
        try:
            if not self.openai_client:
                return None
            
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text.strip()
            )
            
            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def _calculate_similarity(self, query_embedding: np.ndarray, doc_embedding: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            # Reshape to 2D arrays for sklearn
            query_embedding = query_embedding.reshape(1, -1)
            doc_embedding = doc_embedding.reshape(1, -1)
            
            similarity = cosine_similarity(query_embedding, doc_embedding)[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def _chunk_content(self, content: str, filename: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Split content into overlapping chunks"""
        chunks = []
        
        # Simple text chunking (can be enhanced with semantic splitting)
        words = content.split()
        
        start = 0
        chunk_index = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = ' '.join(words[start:end])
            
            chunks.append({
                'content': chunk_text,
                'chunk_index': chunk_index,
                'start_word': start,
                'end_word': end,
                'filename': filename
            })
            
            # Move start position with overlap
            start = end - overlap if end < len(words) else end
            chunk_index += 1
        
        return chunks
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get embedding statistics for this agent
        
        Returns:
            Statistics about agent's embeddings
        """
        try:
            await self._load_index()
            
            if not self.index_cache:
                return {}
            
            total_files = len(self.index_cache.get('files', {}))
            total_embeddings = sum(
                file_info.get('chunk_count', 0) 
                for file_info in self.index_cache.get('files', {}).values()
            )
            
            # Calculate storage size
            storage_size = 0
            if self.knowledge_path.exists():
                storage_size = sum(
                    f.stat().st_size 
                    for f in self.knowledge_path.rglob('*') 
                    if f.is_file()
                )
            
            stats = {
                'total_files': total_files,
                'total_embeddings': total_embeddings,
                'total_size': storage_size,
                'last_updated': self.index_cache.get('last_updated', ''),
                'embedding_model': self.embedding_model,
                'embedding_dimension': self.embedding_dim
            }
            
            logger.info(f"Retrieved embedding stats for agent {self.agent_id}: {total_embeddings} embeddings")
            return stats
                
        except Exception as e:
            logger.error(f"Error retrieving embedding stats: {e}")
            return {}
    
    async def _load_index(self):
        """Load the knowledge index from disk"""
        try:
            if self.index_path.exists():
                with open(self.index_path, 'r') as f:
                    self.index_cache = json.load(f)
            else:
                self.index_cache = {
                    'files': {},
                    'created_at': datetime.utcnow().isoformat(),
                    'last_updated': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self.index_cache = {'files': {}}
    
    async def _update_index(self, file_id: str, filename: str, chunk_count: int, metadata: Dict[str, Any]):
        """Update the knowledge index"""
        try:
            if not self.index_cache:
                await self._load_index()
            
            self.index_cache['files'][file_id] = {
                'filename': filename,
                'chunk_count': chunk_count,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }
            self.index_cache['last_updated'] = datetime.utcnow().isoformat()
            
            # Save to disk
            with open(self.index_path, 'w') as f:
                json.dump(self.index_cache, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update index: {e}")
    
    async def _save_chunk(self, chunk_id: str, chunk_data: Dict[str, Any], embedding: np.ndarray):
        """Save chunk data and embedding to disk"""
        try:
            # Save chunk data
            chunk_path = self.documents_path / f"{chunk_id}.json"
            with open(chunk_path, 'w') as f:
                json.dump(chunk_data, f, indent=2)
            
            # Save embedding
            embedding_path = self.embeddings_path / f"{chunk_id}.npy"
            np.save(embedding_path, embedding)
            
        except Exception as e:
            logger.error(f"Failed to save chunk {chunk_id}: {e}")
    
    async def _ensure_embeddings_loaded(self):
        """Ensure all embeddings are loaded in cache"""
        try:
            if self.embeddings_cache and self.documents_cache:
                return  # Already loaded
            
            # Load all chunks
            for chunk_file in self.documents_path.glob("*.json"):
                chunk_id = chunk_file.stem
                
                # Load chunk data
                with open(chunk_file, 'r') as f:
                    chunk_data = json.load(f)
                self.documents_cache[chunk_id] = chunk_data
                
                # Load embedding
                embedding_file = self.embeddings_path / f"{chunk_id}.npy"
                if embedding_file.exists():
                    embedding = np.load(embedding_file)
                    self.embeddings_cache[chunk_id] = embedding
            
            logger.info(f"Loaded {len(self.documents_cache)} documents and {len(self.embeddings_cache)} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
    
    async def _load_embeddings_cache(self):
        """Load embeddings into memory cache"""
        await self._ensure_embeddings_loaded()
    
    async def register_tools(self, tool_registry: ToolRegistry):
        """Register embedded knowledge tools with the tool registry"""
        try:
            # Register semantic search tool
            tool_registry.register_function_tool(
                name="search_knowledge_base",
                description="Search the agent's local knowledge base using semantic embeddings",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant information"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["query"]
                },
                function=self._search_knowledge_tool
            )
            
            # Register document addition tool
            tool_registry.register_function_tool(
                name="add_document_to_knowledge",
                description="Add a document to the agent's knowledge base",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Document content to add"
                        },
                        "filename": {
                            "type": "string", 
                            "description": "Name for the document"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata for the document"
                        }
                    },
                    "required": ["content", "filename"]
                },
                function=self._add_document_tool
            )
            
            # Register agent files listing tool
            tool_registry.register_function_tool(
                name="list_knowledge_files",
                description="List all files indexed in the agent's knowledge base",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                function=self._list_files_tool
            )
            
            # Register file content retrieval tool
            tool_registry.register_function_tool(
                name="get_file_content",
                description="Get all content chunks from a specific file in the knowledge base",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "File ID to retrieve content from"
                        }
                    },
                    "required": ["file_id"]
                },
                function=self._get_file_content_tool
            )
            
            # Register knowledge stats tool
            tool_registry.register_function_tool(
                name="get_knowledge_stats",
                description="Get statistics about the agent's knowledge base",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                function=self._get_stats_tool
            )
            
            logger.info("Embedded knowledge tools registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register knowledge tools: {e}")
    
    async def _search_knowledge_tool(self, query: str, top_k: int = 5) -> str:
        """Tool function for embedded knowledge search"""
        try:
            results = await self.search_knowledge(query, top_k)
            
            if not results:
                return "No relevant information found in the knowledge base."
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                content = result.get('content', '').strip()
                filename = result.get('filename', 'Unknown')
                similarity = result.get('similarity_score', 0.0)
                page_number = result.get('page_number', '')
                chunk_index = result.get('chunk_index', '')
                
                source_info = f"{filename}"
                if page_number:
                    source_info += f" (page {page_number})"
                if chunk_index is not None:
                    source_info += f" [chunk {chunk_index}]"
                
                formatted_results.append(
                    f"[Result {i}] (Similarity: {similarity:.3f})\n"
                    f"Source: {source_info}\n"
                    f"Content: {content}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Knowledge search tool error: {e}")
            return f"Error searching knowledge base: {str(e)}"
    
    async def _add_document_tool(self, content: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Tool function for adding documents to knowledge base"""
        try:
            doc_id = await self.add_document(content, filename, metadata or {})
            return f"Successfully added document '{filename}' to knowledge base with ID: {doc_id}"
            
        except Exception as e:
            logger.error(f"Add document tool error: {e}")
            return f"Error adding document to knowledge base: {str(e)}"
    
    async def _list_files_tool(self) -> str:
        """Tool function for listing agent files"""
        try:
            files = await self.get_agent_files()
            
            if not files:
                return "No files found in the knowledge base for this agent."
            
            formatted_files = []
            for file_info in files:
                filename = file_info.get('filename', 'Unknown')
                file_id = file_info.get('id', 'Unknown')
                chunk_count = file_info.get('chunk_count', 0)
                created_at = file_info.get('created_at', 'Unknown')
                
                formatted_files.append(
                    f"• {filename}\n"
                    f"  ID: {file_id}\n"
                    f"  Chunks: {chunk_count}\n"
                    f"  Created: {created_at}\n"
                )
            
            return f"Files in knowledge base ({len(files)} total):\n\n" + "\n".join(formatted_files)
            
        except Exception as e:
            logger.error(f"List files tool error: {e}")
            return f"Error listing files: {str(e)}"
    
    async def _get_file_content_tool(self, file_id: str) -> str:
        """Tool function for getting file content"""
        try:
            embeddings = await self.get_file_embeddings(file_id)
            
            if not embeddings:
                return f"No content found for file ID {file_id}."
            
            # Sort by chunk index if available
            sorted_embeddings = sorted(embeddings, key=lambda x: x.get('chunk_index', 0))
            
            content_chunks = []
            filename = "Unknown"
            
            for chunk in sorted_embeddings:
                if filename == "Unknown":
                    filename = chunk.get('filename', 'Unknown')
                
                chunk_content = chunk.get('content', '').strip()
                chunk_index = chunk.get('chunk_index', '')
                page_number = chunk.get('page_number', '')
                
                chunk_header = f"[Chunk {chunk_index}"
                if page_number:
                    chunk_header += f", Page {page_number}"
                chunk_header += "]"
                
                content_chunks.append(f"{chunk_header}\n{chunk_content}")
            
            return f"Content from {filename} ({len(content_chunks)} chunks):\n\n" + "\n\n".join(content_chunks)
            
        except Exception as e:
            logger.error(f"Get file content tool error: {e}")
            return f"Error retrieving file content: {str(e)}"
    
    async def _get_stats_tool(self) -> str:
        """Tool function for getting knowledge base statistics"""
        try:
            stats = await self.get_embedding_stats()
            
            if not stats:
                return "Unable to retrieve knowledge base statistics."
            
            total_embeddings = stats.get('total_embeddings', 0)
            total_files = stats.get('total_files', 0)
            total_size = stats.get('total_size', 0)
            embedding_model = stats.get('embedding_model', 'Unknown')
            last_updated = stats.get('last_updated', 'Unknown')
            
            return (
                f"Local Knowledge Base Statistics:\n"
                f"• Total files: {total_files}\n"
                f"• Total content chunks: {total_embeddings}\n"
                f"• Storage size: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)\n"
                f"• Embedding model: {embedding_model}\n"
                f"• Last updated: {last_updated}"
            )
            
        except Exception as e:
            logger.error(f"Get stats tool error: {e}")
            return f"Error retrieving statistics: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check if embedded knowledge service is healthy"""
        try:
            # Check if required dependencies are available
            if not OPENAI_AVAILABLE or not NUMPY_AVAILABLE:
                return False
            
            # Check if OpenAI client is configured
            if not self.openai_client:
                return False
            
            # Check if knowledge directory exists
            if not self.knowledge_path.exists():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Knowledge service health check failed: {e}")
            return False
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get embedded knowledge service information"""
        try:
            stats = await self.get_embedding_stats()
            
            return {
                "service": "embedded-knowledge",
                "agent_id": self.agent_id,
                "embedding_model": self.embedding_model,
                "embedding_dimension": self.embedding_dim,
                "openai_available": OPENAI_AVAILABLE,
                "numpy_available": NUMPY_AVAILABLE,
                "storage_path": str(self.knowledge_path),
                "stats": stats,
                "status": "healthy" if await self.health_check() else "unhealthy"
            }
                
        except Exception as e:
            logger.error(f"Failed to get embedded knowledge service info: {e}")
            return {
                "service": "embedded-knowledge",
                "agent_id": self.agent_id,
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close the knowledge service and cleanup"""
        try:
            # Clear caches
            self.embeddings_cache.clear()
            self.documents_cache.clear()
            self.index_cache = None
            
            logger.info("Embedded knowledge service closed")
            
        except Exception as e:
            logger.error(f"Error closing knowledge service: {e}")


# Alias for backward compatibility
KnowledgeService = EmbeddedKnowledgeService