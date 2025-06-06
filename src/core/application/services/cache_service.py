"""
Cache Service

This module provides functionality for:
1. Redis-based caching
2. Cache key management
3. Cache expiration handling
4. Cache statistics and monitoring
"""

import json
from typing import Any, Dict, Optional, Union
import logging
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError
from functools import wraps

from config.settings import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Service for handling Redis caching operations."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour in seconds
        self.cache = {}

    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string."""
        try:
            return json.dumps(value)
        except Exception as e:
            logger.error(f"Error serializing value: {str(e)}")
            raise

    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to Python object."""
        try:
            return json.loads(value)
        except Exception as e:
            logger.error(f"Error deserializing value: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            return self._deserialize(value) if value else None
        except RedisError as e:
            logger.error(f"Error getting value from cache: {str(e)}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        try:
            serialized_value = self._serialize(value)
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, serialized_value)
        except RedisError as e:
            logger.error(f"Error setting value in cache: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            logger.error(f"Error deleting value from cache: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.error(f"Error checking key existence: {str(e)}")
            return False

    def ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds."""
        try:
            return self.redis_client.ttl(key)
        except RedisError as e:
            logger.error(f"Error getting TTL: {str(e)}")
            return -1

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value for key."""
        try:
            return self.redis_client.incr(key, amount)
        except RedisError as e:
            logger.error(f"Error incrementing value: {str(e)}")
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value for key."""
        try:
            return self.redis_client.decr(key, amount)
        except RedisError as e:
            logger.error(f"Error decrementing value: {str(e)}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info["used_memory"],
                "used_memory_peak": info["used_memory_peak"],
                "connected_clients": info["connected_clients"],
                "total_keys": self.redis_client.dbsize(),
                "uptime": info["uptime_in_seconds"]
            }
        except RedisError as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}

    def clear(self) -> bool:
        """Clear all keys from cache."""
        try:
            return self.redis_client.flushdb()
        except RedisError as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    async def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
        except RedisError as e:
            logger.error(f"Error closing Redis connection: {str(e)}")

    def cached(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in self.cache:
                return self.cache[key]
            result = func(*args, **kwargs)
            self.cache[key] = result
            return result
        return wrapper

# Export the cached decorator
cached = CacheService().cached 