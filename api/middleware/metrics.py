from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Request metrics with proper namespacing
REQUEST_COUNT = Counter(
    'affiliate_outreach_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'affiliate_outreach_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# Database metrics
DB_QUERY_COUNT = Counter(
    'affiliate_outreach_db_queries_total',
    'Total number of database queries',
    ['operation']
)

DB_QUERY_LATENCY = Histogram(
    'affiliate_outreach_db_query_duration_seconds',
    'Database query latency in seconds',
    ['operation']
)

# Cache metrics
CACHE_HITS = Counter(
    'affiliate_outreach_cache_hits_total',
    'Total number of cache hits',
    ['cache_name', 'cache_level', 'key_pattern']
)

CACHE_MISSES = Counter(
    'affiliate_outreach_cache_misses_total',
    'Total number of cache misses',
    ['cache_name', 'cache_level', 'key_pattern']
)

CACHE_WARMING_DURATION = Histogram(
    'affiliate_outreach_cache_warming_duration_seconds',
    'Time taken to warm cache entries',
    ['cache_name', 'key_pattern']
)

CACHE_WARMING_ERRORS = Counter(
    'affiliate_outreach_cache_warming_errors_total',
    'Total number of cache warming errors',
    ['cache_name', 'key_pattern', 'error_type']
)

CACHE_SIZE = Gauge(
    'affiliate_outreach_cache_size_bytes',
    'Current size of cache in bytes',
    ['cache_name', 'cache_level']
)

CACHE_KEYS = Gauge(
    'affiliate_outreach_cache_keys_total',
    'Total number of keys in cache',
    ['cache_name', 'cache_level']
)

CACHE_TTL = Gauge(
    'affiliate_outreach_cache_ttl_seconds',
    'Time to live for cache entries',
    ['cache_name', 'key_pattern']
)

async def metrics_middleware(request: Request, call_next: Callable):
    """Middleware to record request metrics."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        raise e
    finally:
        duration = time.time() - start_time
        
        # Record request metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
    
    return response

def record_db_operation(operation: str, duration: float):
    """Record database operation metrics."""
    DB_QUERY_COUNT.labels(operation=operation).inc()
    DB_QUERY_LATENCY.labels(operation=operation).observe(duration)

def record_cache_operation(cache_name: str, cache_level: str, key_pattern: str, is_hit: bool):
    """Record cache operation metrics."""
    if is_hit:
        CACHE_HITS.labels(
            cache_name=cache_name,
            cache_level=cache_level,
            key_pattern=key_pattern
        ).inc()
    else:
        CACHE_MISSES.labels(
            cache_name=cache_name,
            cache_level=cache_level,
            key_pattern=key_pattern
        ).inc()

def record_cache_warming(cache_name: str, key_pattern: str, duration: float, error: Exception = None):
    """Record cache warming metrics."""
    CACHE_WARMING_DURATION.labels(
        cache_name=cache_name,
        key_pattern=key_pattern
    ).observe(duration)
    
    if error:
        CACHE_WARMING_ERRORS.labels(
            cache_name=cache_name,
            key_pattern=key_pattern,
            error_type=type(error).__name__
        ).inc()

def update_cache_size(cache_name: str, cache_level: str, size_bytes: int):
    """Update cache size metric."""
    CACHE_SIZE.labels(
        cache_name=cache_name,
        cache_level=cache_level
    ).set(size_bytes)

def update_cache_keys(cache_name: str, cache_level: str, num_keys: int):
    """Update cache keys metric."""
    CACHE_KEYS.labels(
        cache_name=cache_name,
        cache_level=cache_level
    ).set(num_keys)

def update_cache_ttl(cache_name: str, key_pattern: str, ttl_seconds: int):
    """Update cache TTL metric."""
    CACHE_TTL.labels(
        cache_name=cache_name,
        key_pattern=key_pattern
    ).set(ttl_seconds) 