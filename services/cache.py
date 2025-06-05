import redis
import json
from typing import Any, Optional, Union, Dict, List, Callable, Pattern
from functools import wraps
import logging
from config.settings import settings
import time
from threading import Lock
from api.middleware.metrics import (
    record_cache_operation, record_cache_warming,
    update_cache_size, update_cache_keys, update_cache_ttl
)
import asyncio
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class CacheWarmer:
    """Handles warming up the cache with frequently accessed data."""
    def __init__(self, cache: 'RedisCache'):
        self.cache = cache
        self.warming_tasks: Dict[str, asyncio.Task] = {}
    
    async def warm_cache(self, key: str, data_func: Callable, ttl: int, interval: int):
        """Warm cache with data from a function at regular intervals."""
        while True:
            start_time = time.time()
            try:
                data = await data_func()
                if data is not None:
                    self.cache.set(key, data, ttl)
                    logger.info(f"Warmed cache for key: {key}")
                duration = time.time() - start_time
                record_cache_warming(self.cache.name, key, duration)
            except Exception as e:
                duration = time.time() - start_time
                record_cache_warming(self.cache.name, key, duration, error=e)
                logger.error(f"Error warming cache for key {key}: {e}")
            await asyncio.sleep(interval)
    
    def start_warming(self, key: str, data_func: Callable, ttl: int = 3600, interval: int = 300):
        """Start warming cache for a specific key."""
        if key in self.warming_tasks:
            self.warming_tasks[key].cancel()
        
        self.warming_tasks[key] = asyncio.create_task(
            self.warm_cache(key, data_func, ttl, interval)
        )
        update_cache_ttl(self.cache.name, key, ttl)
    
    def stop_warming(self, key: str):
        """Stop warming cache for a specific key."""
        if key in self.warming_tasks:
            self.warming_tasks[key].cancel()
            del self.warming_tasks[key]

class MemoryCache:
    """Simple in-memory cache with TTL support."""
    def __init__(self, name: str = "memory"):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.name = name
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry['expires_at'] > time.time():
                    record_cache_operation(self.name, "memory", key, True)
                    return entry['value']
                else:
                    del self._cache[key]
            record_cache_operation(self.name, "memory", key, False)
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in memory cache with TTL."""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            update_cache_keys(self.name, "memory", len(self._cache))
            return True
    
    def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                update_cache_keys(self.name, "memory", len(self._cache))
                return True
            return False
    
    def clear(self) -> None:
        """Clear all values from memory cache."""
        with self._lock:
            self._cache.clear()
            update_cache_keys(self.name, "memory", 0)

class RedisCache:
    def __init__(self, name: str = "redis"):
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL or "redis://localhost:6379/0",
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour default TTL
        self.memory_cache = MemoryCache(name)
        self.warmer = CacheWarmer(self)
        self.name = name
        self._update_metrics()

    def _update_metrics(self):
        """Update cache metrics."""
        try:
            info = self.redis_client.info()
            update_cache_size(self.name, "redis", info['used_memory'])
            update_cache_keys(self.name, "redis", info['db0']['keys'])
        except Exception as e:
            logger.error(f"Error updating Redis metrics: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache, trying memory first then Redis."""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # If not in memory, try Redis
        try:
            value = self.redis_client.get(key)
            if value:
                # Cache in memory for faster subsequent access
                self.memory_cache.set(key, json.loads(value), 300)  # 5 minutes in memory
                record_cache_operation(self.name, "redis", key, True)
                return json.loads(value)
            record_cache_operation(self.name, "redis", key, False)
            return None
        except Exception as e:
            logger.error(f"Error retrieving from Redis: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in both memory and Redis cache."""
        try:
            serialized_value = json.dumps(value)
            # Set in Redis
            result = self.redis_client.setex(
                key,
                ttl or self.default_ttl,
                serialized_value
            )
            # Also set in memory with shorter TTL
            self.memory_cache.set(key, value, min(ttl or self.default_ttl, 300))
            self._update_metrics()
            return result
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from both memory and Redis cache."""
        try:
            # Delete from both caches
            self.memory_cache.delete(key)
            result = bool(self.redis_client.delete(key))
            self._update_metrics()
            return result
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching a pattern from both caches."""
        try:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace('*', '.*')
            compiled_pattern = re.compile(f"^{regex_pattern}$")
            
            # Clear matching keys from Redis
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # Clear matching keys from memory cache
            with self.memory_cache._lock:
                keys_to_delete = [
                    key for key in self.memory_cache._cache.keys()
                    if compiled_pattern.match(key)
                ]
                for key in keys_to_delete:
                    del self.memory_cache._cache[key]
            
            self._update_metrics()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return False

    def invalidate_on_update(self, pattern: str):
        """Decorator to invalidate cache entries when data is updated."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                self.clear_pattern(pattern)
                return result
            return wrapper
        return decorator

def cache_result(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cache = RedisCache()
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # If not in cache, execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                cache.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator

# Initialize global cache instance
cache = RedisCache() 