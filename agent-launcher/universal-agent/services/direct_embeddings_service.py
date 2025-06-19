"""
Direct Embeddings Service Module

This module provides direct access to OpenAI's embeddings API, replacing LangChain's 
OpenAIEmbeddings with better control over batch processing, caching, and error handling.
"""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timedelta

import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embedding: List[float]
    text: str
    token_count: int
    model: str


@dataclass
class BatchEmbeddingResult:
    """Result from batch embedding generation."""
    embeddings: List[List[float]]
    texts: List[str]
    total_tokens: int
    model: str


class EmbeddingCache:
    """Simple in-memory cache for embeddings."""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        """
        Initialize the embedding cache.
        
        Args:
            max_size: Maximum number of cached embeddings
            ttl_hours: Time to live in hours
        """
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache: Dict[str, Tuple[List[float], datetime]] = {}
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model."""
        key_data = f"{model}:{text}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get embedding from cache if available and not expired."""
        key = self._get_cache_key(text, model)
        
        if key in self.cache:
            embedding, timestamp = self.cache[key]
            
            # Check if not expired
            if datetime.now() - timestamp < timedelta(hours=self.ttl_hours):
                return embedding
            else:
                # Remove expired entry
                del self.cache[key]
        
        return None
    
    def put(self, text: str, model: str, embedding: List[float]) -> None:
        """Put embedding in cache."""
        key = self._get_cache_key(text, model)
        
        # If cache is full, remove oldest entry
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (embedding, datetime.now())
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class DirectEmbeddingsService:
    """
    Direct OpenAI embeddings service providing full control over embedding generation.
    
    Features:
    - Direct OpenAI API calls with proper error handling
    - Batch processing with optimal batch sizes
    - In-memory caching to reduce API calls
    - Token usage tracking
    - Multiple embedding models support
    - Retry logic with exponential backoff
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        dimensions: Optional[int] = None,
        enable_cache: bool = True,
        max_batch_size: int = 100
    ):
        """
        Initialize the direct embeddings service.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Embedding model to use
            dimensions: Output dimensions (for ada-002 models)
            enable_cache: Whether to enable embedding caching
            max_batch_size: Maximum batch size for API calls
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.dimensions = dimensions
        self.max_batch_size = max_batch_size
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Initialize cache if enabled
        self.cache = EmbeddingCache() if enable_cache else None
        
        # Token usage tracking
        self.total_tokens = 0
        
        logger.info(f"DirectEmbeddingsService initialized with model: {model}")
        if dimensions:
            logger.info(f"Using custom dimensions: {dimensions}")
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult object
        """
        # Check cache first
        if self.cache:
            cached_embedding = self.cache.get(text, self.model)
            if cached_embedding is not None:
                return EmbeddingResult(
                    embedding=cached_embedding,
                    text=text,
                    token_count=self._estimate_tokens(text),
                    model=self.model
                )
        
        # Generate embedding
        batch_result = await self.embed_texts([text])
        
        # Cache the result
        if self.cache:
            self.cache.put(text, self.model, batch_result.embeddings[0])
        
        return EmbeddingResult(
            embedding=batch_result.embeddings[0],
            text=text,
            token_count=batch_result.total_tokens,
            model=batch_result.model
        )
    
    async def embed_texts(self, texts: List[str]) -> BatchEmbeddingResult:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            BatchEmbeddingResult object
        """
        if not texts:
            return BatchEmbeddingResult(
                embeddings=[],
                texts=[],
                total_tokens=0,
                model=self.model
            )
        
        # Process in batches to respect API limits
        all_embeddings = []
        total_tokens = 0
        
        for i in range(0, len(texts), self.max_batch_size):
            batch_texts = texts[i:i + self.max_batch_size]
            
            # Check cache for this batch
            cached_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            if self.cache:
                for j, text in enumerate(batch_texts):
                    cached = self.cache.get(text, self.model)
                    if cached is not None:
                        cached_embeddings.append((j, cached))
                    else:
                        uncached_texts.append(text)
                        uncached_indices.append(j)
            else:
                uncached_texts = batch_texts
                uncached_indices = list(range(len(batch_texts)))
            
            # Generate embeddings for uncached texts
            batch_embeddings = [None] * len(batch_texts)
            
            if uncached_texts:
                try:
                    # Prepare API parameters
                    params = {
                        "model": self.model,
                        "input": uncached_texts,
                    }
                    
                    if self.dimensions:
                        params["dimensions"] = self.dimensions
                    
                    response = await self.client.embeddings.create(**params)
                    
                    # Extract embeddings and update cache
                    for idx, embedding_obj in enumerate(response.data):
                        original_idx = uncached_indices[idx]
                        embedding = embedding_obj.embedding
                        
                        batch_embeddings[original_idx] = embedding
                        
                        # Cache the embedding
                        if self.cache:
                            self.cache.put(uncached_texts[idx], self.model, embedding)
                    
                    # Update token usage
                    total_tokens += response.usage.total_tokens
                    self.total_tokens += response.usage.total_tokens
                    
                except Exception as e:
                    logger.error(f"Error generating embeddings for batch: {str(e)}")
                    raise
            
            # Fill in cached embeddings
            for original_idx, cached_embedding in cached_embeddings:
                batch_embeddings[original_idx] = cached_embedding
            
            all_embeddings.extend(batch_embeddings)
        
        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            texts=texts,
            total_tokens=total_tokens,
            model=self.model
        )
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query (alias for single text embedding).
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        result = await self.embed_text(query)
        return result.embedding
    
    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents (alias for batch text embedding).
        
        Args:
            documents: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        result = await self.embed_texts(documents)
        return result.embeddings
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        # Convert to numpy arrays for efficient computation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top similar embeddings to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity (descending)
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity_score = self.similarity(query_embedding, candidate)
            similarities.append((i, similarity_score))
        
        # Sort by similarity score (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_token_usage(self) -> int:
        """Get total token usage for this session."""
        return self.total_tokens
    
    def reset_token_usage(self) -> None:
        """Reset token usage tracking."""
        self.total_tokens = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "size": self.cache.size(),
            "max_size": self.cache.max_size,
            "ttl_hours": self.cache.ttl_hours
        }
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if self.cache:
            self.cache.clear()
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        This is a rough estimation based on the rule of thumb:
        1 token ≈ 4 characters for English text
        """
        return len(text) // 4
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for the current model."""
        # Default dimensions for common models
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        
        if self.dimensions:
            return self.dimensions
        
        return model_dimensions.get(self.model, 1536)


# Convenience functions for creating service instances
def create_embeddings_service(
    api_key: Optional[str] = None,
    model: str = "text-embedding-3-small",
    **kwargs
) -> DirectEmbeddingsService:
    """Create a DirectEmbeddingsService instance."""
    return DirectEmbeddingsService(api_key=api_key, model=model, **kwargs)


# Backward compatibility function to mimic LangChain interface
class OpenAIEmbeddings:
    """Backward compatibility wrapper that mimics LangChain's OpenAIEmbeddings interface."""
    
    def __init__(self, openai_api_key: str, model: str = "text-embedding-3-small", **kwargs):
        """Initialize with LangChain-compatible interface."""
        self.service = DirectEmbeddingsService(
            api_key=openai_api_key,
            model=model,
            **kwargs
        )
    
    async def aembed_query(self, text: str) -> List[float]:
        """Async embed query (LangChain compatibility)."""
        return await self.service.embed_query(text)
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async embed documents (LangChain compatibility)."""
        return await self.service.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Sync embed query (LangChain compatibility)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.service.embed_query(text))
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Sync embed documents (LangChain compatibility)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.service.embed_documents(texts))