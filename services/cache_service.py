from typing import Any, Optional, Union, List, Dict
import json
import pickle
from datetime import datetime, timedelta
import redis
from services.logging_service import LoggingService
from functools import wraps
import hashlib
import asyncio

class CacheService:
    """Service for handling caching operations using Redis."""
    
    def __init__(
        self,
        redis_url: str,
        logger: LoggingService,
        default_ttl: int = 3600  # 1 hour
    ):
        self.redis = redis.from_url(redis_url)
        self.logger = logger
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments."""
        # Convert args and kwargs to a string
        key_parts = [prefix]
        if args:
            key_parts.extend([str(arg) for arg in args])
        if kwargs:
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        
        # Create a hash of the key parts
        key_string = ":".join(key_parts)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}", exc_info=e)
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            serialized_value = pickle.dumps(value)
            if ttl is None:
                ttl = self.default_ttl
            return self.redis.setex(key, ttl, serialized_value)
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}", exc_info=e)
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}", exc_info=e)
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}", exc_info=e)
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache."""
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            self.logger.error(f"Error incrementing cache key {key}", exc_info=e)
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a counter in cache."""
        try:
            return self.redis.decr(key, amount)
        except Exception as e:
            self.logger.error(f"Error decrementing cache key {key}", exc_info=e)
            return None
    
    def set_hash(
        self,
        key: str,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set a hash in cache."""
        try:
            if ttl is None:
                ttl = self.default_ttl
            pipe = self.redis.pipeline()
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, ttl)
            return all(pipe.execute())
        except Exception as e:
            self.logger.error(f"Error setting hash cache key {key}", exc_info=e)
            return False
    
    def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a hash from cache."""
        try:
            result = self.redis.hgetall(key)
            return {k.decode(): v.decode() for k, v in result.items()}
        except Exception as e:
            self.logger.error(f"Error getting hash cache key {key}", exc_info=e)
            return None
    
    def add_to_set(
        self,
        key: str,
        *values: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Add values to a set in cache."""
        try:
            if ttl is None:
                ttl = self.default_ttl
            pipe = self.redis.pipeline()
            pipe.sadd(key, *values)
            pipe.expire(key, ttl)
            return all(pipe.execute())
        except Exception as e:
            self.logger.error(f"Error adding to set cache key {key}", exc_info=e)
            return False
    
    def get_set(self, key: str) -> Optional[set]:
        """Get a set from cache."""
        try:
            result = self.redis.smembers(key)
            return {v.decode() for v in result}
        except Exception as e:
            self.logger.error(f"Error getting set cache key {key}", exc_info=e)
            return None
    
    def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching a pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache pattern {pattern}", exc_info=e)
            return False

def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[callable] = None
):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            cache_service = getattr(self, 'cache_service', None)
            if not cache_service:
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_service.get(key)
            if cached_value is not None:
                return cached_value
            
            # Get fresh value
            value = await func(self, *args, **kwargs)
            
            # Cache the value
            cache_service.set(key, value, ttl)
            
            return value
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            cache_service = getattr(self, 'cache_service', None)
            if not cache_service:
                return func(self, *args, **kwargs)
            
            # Generate cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_service.get(key)
            if cached_value is not None:
                return cached_value
            
            # Get fresh value
            value = func(self, *args, **kwargs)
            
            # Cache the value
            cache_service.set(key, value, ttl)
            
            return value
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 