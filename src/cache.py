"""Cache layer for Trinity Eyes."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import json


class Cache:
    """
    Simple cache with TTL support.
    
    Backends: memory (default), redis (for distributed)
    """
    
    def __init__(self, config: dict):
        self.backend = config.get("backend", "memory")
        self.ttl_config = config.get("ttl", {
            "indices": 300,
            "futures": 60,
            "forex": 60,
            "quotes": 60,
            "yields": 3600,
            "economic": 86400,
        })
        
        # Memory cache
        self._store: Dict[str, Dict[str, Any]] = {}
        self._expires: Dict[str, Dict[str, datetime]] = {}
        
        # Redis client (lazy init)
        self._redis = None
    
    async def get(self, category: str, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if self.backend == "memory":
            return await self._memory_get(category, key)
        elif self.backend == "redis":
            return await self._redis_get(category, key)
        return None
    
    async def set(self, category: str, key: str, value: Any) -> None:
        """Cache value with category-specific TTL."""
        ttl = self.ttl_config.get(category, 300)
        
        if self.backend == "memory":
            await self._memory_set(category, key, value, ttl)
        elif self.backend == "redis":
            await self._redis_set(category, key, value, ttl)
    
    async def _memory_get(self, category: str, key: str) -> Optional[Any]:
        """Get from memory cache."""
        cache_key = f"{category}:{key}"
        
        # Check expiry
        expires = self._expires.get(category, {}).get(key)
        if expires and datetime.now() > expires:
            # Expired
            self._store.get(category, {}).pop(key, None)
            self._expires.get(category, {}).pop(key, None)
            return None
        
        return self._store.get(category, {}).get(key)
    
    async def _memory_set(self, category: str, key: str, value: Any, ttl: int) -> None:
        """Set in memory cache."""
        if category not in self._store:
            self._store[category] = {}
            self._expires[category] = {}
        
        self._store[category][key] = value
        self._expires[category][key] = datetime.now() + timedelta(seconds=ttl)
    
    async def _redis_get(self, category: str, key: str) -> Optional[Any]:
        """Get from Redis."""
        redis = await self._get_redis()
        cache_key = f"trinity_eyes:{category}:{key}"
        
        data = await redis.get(cache_key)
        if data:
            return json.loads(data)
        return None
    
    async def _redis_set(self, category: str, key: str, value: Any, ttl: int) -> None:
        """Set in Redis with TTL."""
        redis = await self._get_redis()
        cache_key = f"trinity_eyes:{category}:{key}"
        
        # Serialize dataclass to dict
        if hasattr(value, "__dataclass_fields__"):
            from dataclasses import asdict
            value = asdict(value)
        
        await redis.setex(cache_key, ttl, json.dumps(value, default=str))
    
    async def _get_redis(self):
        """Lazy init Redis connection."""
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = redis.from_url("redis://localhost:6379")
        return self._redis
    
    async def close(self):
        """Clean up."""
        if self._redis:
            await self._redis.close()
