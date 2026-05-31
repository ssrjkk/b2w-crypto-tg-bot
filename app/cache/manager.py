"""Enhanced Redis cache manager with optimized operations."""

import json
import logging
from typing import Any, Optional
from functools import wraps
import hashlib

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def cache_key(*args, **kwargs):
    """Generate cache key from arguments."""
    key_parts = [str(a) for a in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


class CacheManager:
    """Optimized async Redis cache manager."""

    _instance: Optional["CacheManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._redis: Optional[Redis] = None
        self._initialized = False
        self._pipeline_enabled = False
        self._pending_commands = []

    @property
    def redis(self) -> Redis:
        if not self._redis:
            redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            self._redis = redis.from_url(
                redis_url,
                decode_responses=True,
                encoding="utf-8",
                max_connections=50,
            )
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            return await self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str),
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def get_or_set(self, key: str, factory, ttl: int = 300) -> Any:
        """Get from cache or set with factory result."""
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await factory() if callable(factory) else factory
        await self.set(key, value, ttl)
        return value

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache delete pattern error: {e}")
        return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error: {e}")
            return False

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Cache incr error: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on key."""
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.warning(f"Cache expire error: {e}")
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values at once."""
        result = {}
        try:
            values = await self.redis.mget(keys)
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get_many error: {e}")
        return result

    async def set_many(self, data: dict[str, Any], ttl: int = 300) -> bool:
        """Set multiple values at once."""
        try:
            pipeline = self.redis.pipeline()
            for key, value in data.items():
                pipeline.setex(key, ttl, json.dumps(value, default=str))
            await pipeline.execute()
            return True
        except Exception as e:
            logger.warning(f"Cache set_many error: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._initialized = False


class QueryCache:
    """Cache helper for database queries."""

    def __init__(self, cache: CacheManager):
        self.cache = cache
        self._prefix = "query"

    def _make_key(self, prefix: str, *args) -> str:
        key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_cached_query(self, key: str, factory, ttl: int = 60) -> Any:
        """Get cached query result or execute factory."""
        return await self.cache.get_or_set(f"{self._prefix}:{key}", factory, ttl)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache by pattern."""
        return await self.cache.delete_pattern(f"{self._prefix}:{pattern}*")


_cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get cache manager singleton."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_query_cache() -> QueryCache:
    """Get query cache helper."""
    return QueryCache(get_cache())


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching async function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            cache_key = f"{key_prefix or func.__name__}:{cache_key(*args, **kwargs)}"
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator