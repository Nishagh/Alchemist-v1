"""
Story Context Caching System

Provides intelligent caching of agent story contexts for high-performance
access while maintaining consistency with the narrative spine.
"""

import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
import hashlib

# Redis for caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logging.warning("Redis not available - story context caching will use in-memory fallback")
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CachedStoryContext:
    """
    Cached representation of an agent's story context
    
    Contains essential narrative information for fast access by services
    """
    agent_id: str
    last_updated: datetime
    cache_version: str
    coherence_score: float
    recent_events: List[Dict[str, Any]]
    narrative_threads: List[Dict[str, Any]]
    current_objectives: List[str]
    worldview_summary: str
    key_beliefs: List[str]
    capability_context: Dict[str, Any]
    service_specific_context: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedStoryContext':
        """Create from dictionary"""
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)
    
    def is_stale(self, max_age_minutes: int = 30) -> bool:
        """Check if the cached context is stale"""
        age = datetime.now(timezone.utc) - self.last_updated
        return age > timedelta(minutes=max_age_minutes)
    
    def get_service_context(self, service_name: str) -> Dict[str, Any]:
        """Get service-specific context"""
        return self.service_specific_context.get(service_name, {})
    
    def set_service_context(self, service_name: str, context: Dict[str, Any]):
        """Set service-specific context"""
        self.service_specific_context[service_name] = context

class StoryContextCache:
    """
    High-performance caching layer for agent story contexts
    
    Provides fast access to agent narrative information while maintaining
    consistency with the centralized narrative spine (Spanner Graph).
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl_minutes: int = 30,
        max_memory_cache_size: int = 1000
    ):
        self.default_ttl_minutes = default_ttl_minutes
        self.max_memory_cache_size = max_memory_cache_size
        
        # Redis client
        self.redis_client: Optional[redis.Redis] = None
        self.redis_available = False
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_connect_timeout=5
                )
                self.redis_available = True
                logger.info("Story context cache initialized with Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using memory cache: {e}")
                self.redis_available = False
        
        # In-memory fallback cache
        self.memory_cache: Dict[str, CachedStoryContext] = {}
        self.cache_access_order: List[str] = []  # For LRU eviction
        
        # Cache invalidation tracking
        self.invalidated_agents: Set[str] = set()
        
        logger.info(f"Story context cache initialized (Redis: {self.redis_available})")
    
    def _get_cache_key(self, agent_id: str, service_name: Optional[str] = None) -> str:
        """Generate cache key for agent story context"""
        if service_name:
            return f"story_context:{agent_id}:{service_name}"
        return f"story_context:{agent_id}"
    
    def _get_invalidation_key(self, agent_id: str) -> str:
        """Generate cache invalidation tracking key"""
        return f"story_invalidation:{agent_id}"
    
    async def get_context(
        self,
        agent_id: str,
        service_name: Optional[str] = None,
        max_age_minutes: Optional[int] = None
    ) -> Optional[CachedStoryContext]:
        """
        Get cached story context for an agent
        
        Returns None if not cached or if cache is stale
        """
        max_age = max_age_minutes or self.default_ttl_minutes
        
        try:
            # Check Redis first
            if self.redis_available:
                context = await self._get_from_redis(agent_id, service_name)
                if context and not context.is_stale(max_age):
                    logger.debug(f"Cache hit (Redis): {agent_id}")
                    return context
            
            # Fallback to memory cache
            context = await self._get_from_memory(agent_id, service_name)
            if context and not context.is_stale(max_age):
                logger.debug(f"Cache hit (memory): {agent_id}")
                return context
            
            logger.debug(f"Cache miss: {agent_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get story context from cache: {e}")
            return None
    
    async def set_context(
        self,
        context: CachedStoryContext,
        service_name: Optional[str] = None,
        ttl_minutes: Optional[int] = None
    ) -> bool:
        """
        Cache story context for an agent
        
        Returns True if successfully cached
        """
        ttl = ttl_minutes or self.default_ttl_minutes
        
        try:
            # Store in Redis
            if self.redis_available:
                await self._set_in_redis(context, service_name, ttl)
            
            # Store in memory cache
            await self._set_in_memory(context, service_name)
            
            # Remove from invalidation set
            self.invalidated_agents.discard(context.agent_id)
            
            logger.debug(f"Cached story context: {context.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache story context: {e}")
            return False
    
    async def invalidate_agent(self, agent_id: str) -> bool:
        """
        Invalidate all cached contexts for an agent
        
        Called when agent's story is updated in the narrative spine
        """
        try:
            # Mark as invalidated
            self.invalidated_agents.add(agent_id)
            
            # Remove from Redis
            if self.redis_available:
                pattern = f"story_context:{agent_id}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            # Remove from memory cache
            keys_to_remove = [
                key for key in self.memory_cache.keys()
                if key.startswith(f"story_context:{agent_id}")
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]
                if key in self.cache_access_order:
                    self.cache_access_order.remove(key)
            
            # Set invalidation marker
            if self.redis_available:
                await self.redis_client.setex(
                    self._get_invalidation_key(agent_id),
                    300,  # 5 minute TTL
                    datetime.now(timezone.utc).isoformat()
                )
            
            logger.info(f"Invalidated story context cache for agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate story context cache: {e}")
            return False
    
    async def warm_cache(
        self,
        agent_id: str,
        context: CachedStoryContext,
        service_name: Optional[str] = None
    ) -> bool:
        """
        Warm the cache with fresh context from narrative spine
        
        Used after story updates to proactively update cache
        """
        # Update cache version to indicate freshness
        context.cache_version = self._generate_cache_version(context)
        context.last_updated = datetime.now(timezone.utc)
        
        return await self.set_context(context, service_name)
    
    async def _get_from_redis(
        self,
        agent_id: str,
        service_name: Optional[str] = None
    ) -> Optional[CachedStoryContext]:
        """Get context from Redis cache"""
        if not self.redis_available:
            return None
        
        try:
            cache_key = self._get_cache_key(agent_id, service_name)
            data = await self.redis_client.get(cache_key)
            
            if not data:
                return None
            
            context_dict = json.loads(data)
            return CachedStoryContext.from_dict(context_dict)
            
        except Exception as e:
            logger.warning(f"Redis cache get failed: {e}")
            return None
    
    async def _set_in_redis(
        self,
        context: CachedStoryContext,
        service_name: Optional[str] = None,
        ttl_minutes: int = 30
    ):
        """Store context in Redis cache"""
        if not self.redis_available:
            return
        
        try:
            cache_key = self._get_cache_key(context.agent_id, service_name)
            data = json.dumps(context.to_dict())
            
            await self.redis_client.setex(
                cache_key,
                ttl_minutes * 60,  # Convert to seconds
                data
            )
            
        except Exception as e:
            logger.warning(f"Redis cache set failed: {e}")
    
    async def _get_from_memory(
        self,
        agent_id: str,
        service_name: Optional[str] = None
    ) -> Optional[CachedStoryContext]:
        """Get context from memory cache"""
        cache_key = self._get_cache_key(agent_id, service_name)
        
        if cache_key in self.memory_cache:
            # Update LRU order
            if cache_key in self.cache_access_order:
                self.cache_access_order.remove(cache_key)
            self.cache_access_order.append(cache_key)
            
            return self.memory_cache[cache_key]
        
        return None
    
    async def _set_in_memory(
        self,
        context: CachedStoryContext,
        service_name: Optional[str] = None
    ):
        """Store context in memory cache"""
        cache_key = self._get_cache_key(context.agent_id, service_name)
        
        # Evict oldest entries if cache is full
        while len(self.memory_cache) >= self.max_memory_cache_size:
            if self.cache_access_order:
                oldest_key = self.cache_access_order.pop(0)
                del self.memory_cache[oldest_key]
            else:
                break
        
        self.memory_cache[cache_key] = context
        
        # Update LRU order
        if cache_key in self.cache_access_order:
            self.cache_access_order.remove(cache_key)
        self.cache_access_order.append(cache_key)
    
    def _generate_cache_version(self, context: CachedStoryContext) -> str:
        """Generate a version hash for cache consistency"""
        # Create hash based on key context elements
        content = f"{context.agent_id}:{len(context.recent_events)}:{context.coherence_score}:{context.last_updated.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        redis_info = {}
        if self.redis_available:
            try:
                redis_info = await self.redis_client.info("memory")
            except Exception:
                redis_info = {"error": "Redis info unavailable"}
        
        return {
            "redis_available": self.redis_available,
            "memory_cache_size": len(self.memory_cache),
            "max_memory_cache_size": self.max_memory_cache_size,
            "invalidated_agents": len(self.invalidated_agents),
            "redis_info": redis_info
        }
    
    async def cleanup(self):
        """Clean up cache resources"""
        if self.redis_available and self.redis_client:
            await self.redis_client.close()
        
        self.memory_cache.clear()
        self.cache_access_order.clear()

# Global cache instance
_global_story_cache: Optional[StoryContextCache] = None

def get_story_context_cache() -> Optional[StoryContextCache]:
    """Get the global story context cache instance"""
    return _global_story_cache

def init_story_context_cache(
    redis_url: Optional[str] = None,
    default_ttl_minutes: int = 30
) -> StoryContextCache:
    """Initialize the global story context cache"""
    global _global_story_cache
    _global_story_cache = StoryContextCache(redis_url, default_ttl_minutes)
    return _global_story_cache