import pytest
import redis
from services.cache_service import CacheService, cached
from services.logging_service import LoggingService
import asyncio
from datetime import datetime, timedelta
import logging
from unittest.mock import Mock, patch

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
test_logger = logging.getLogger(__name__)

def is_redis_available():
    """Check if Redis is available."""
    try:
        test_logger.debug("Attempting to connect to Redis...")
        client = redis.Redis(
            host='localhost', 
            port=6379, 
            db=15, 
            socket_timeout=0.1,
            socket_connect_timeout=0.1
        )
        client.ping()
        test_logger.debug("Successfully connected to Redis")
        return True
    except (redis.ConnectionError, redis.ResponseError) as e:
        test_logger.error(f"Failed to connect to Redis: {e}")
        return False

# Mark all tests in this module to skip if Redis is not available
pytestmark = pytest.mark.skipif(
    not is_redis_available(),
    reason="Redis is not available"
)

@pytest.fixture(scope="session")
def redis_client():
    """Create a Redis client for testing."""
    test_logger.debug("Setting up Redis client fixture")
    if not is_redis_available():
        test_logger.warning("Redis is not available, using mock client")
        mock_client = Mock()
        mock_client.ping = Mock(return_value=True)
        mock_client.flushdb = Mock(return_value=True)
        mock_client.set = Mock(return_value=True)
        mock_client.get = Mock(return_value=None)
        mock_client.delete = Mock(return_value=True)
        mock_client.exists = Mock(return_value=False)
        mock_client.hset = Mock(return_value=True)
        mock_client.hgetall = Mock(return_value={})
        mock_client.sadd = Mock(return_value=True)
        mock_client.smembers = Mock(return_value=set())
        mock_client.keys = Mock(return_value=[])
        return mock_client
    
    client = redis.Redis(
        host='localhost', 
        port=6379, 
        db=15, 
        socket_timeout=0.1,
        socket_connect_timeout=0.1
    )
    test_logger.debug("Redis client fixture created successfully")
    return client

@pytest.fixture
def service_logger():
    """Create a logger instance for testing."""
    return LoggingService(enable_console=False)

@pytest.fixture
def cache_service(redis_client, service_logger):
    """Create a cache service instance for testing."""
    test_logger.debug("Setting up cache service fixture")
    service = CacheService(
        redis_url="redis://localhost:6379/15",
        logger=service_logger,
        default_ttl=3600
    )
    # Replace the Redis client with our fixture
    service.redis = redis_client
    yield service
    # Clean up after tests
    try:
        test_logger.debug("Cleaning up Redis database")
        redis_client.flushdb()
    except redis.RedisError as e:
        test_logger.error(f"Error during Redis cleanup: {e}")
        pass  # Ignore cleanup errors

def test_set_get(cache_service):
    """Test setting and getting values from cache."""
    # Test simple value
    cache_service.set("test_key", "test_value")
    assert cache_service.get("test_key") == "test_value"
    
    # Test complex value
    test_data = {"name": "test", "value": 42}
    cache_service.set("test_complex", test_data)
    assert cache_service.get("test_complex") == test_data

def test_delete(cache_service):
    """Test deleting values from cache."""
    cache_service.set("test_key", "test_value")
    assert cache_service.exists("test_key")
    
    cache_service.delete("test_key")
    assert not cache_service.exists("test_key")

def test_ttl(cache_service, redis_client):
    """Test TTL functionality."""
    test_logger.debug("Starting TTL test")
    cache_service.set("test_key", "test_value", ttl=1)
    assert cache_service.exists("test_key")
    
    # Use asyncio.sleep instead of time.sleep for better test reliability
    test_logger.debug("Waiting for TTL to expire")
    asyncio.run(asyncio.sleep(1.1))
    
    assert not cache_service.exists("test_key")
    test_logger.debug("TTL test completed")

def test_increment_decrement(cache_service):
    """Test increment and decrement operations."""
    # Test increment
    assert cache_service.increment("counter") == 1
    assert cache_service.increment("counter", 5) == 6
    
    # Test decrement
    assert cache_service.decrement("counter") == 5
    assert cache_service.decrement("counter", 2) == 3

def test_hash_operations(cache_service):
    """Test hash operations."""
    test_data = {
        "field1": "value1",
        "field2": "value2"
    }
    
    # Test setting hash
    assert cache_service.set_hash("test_hash", test_data)
    
    # Test getting hash
    result = cache_service.get_hash("test_hash")
    assert result == test_data

def test_set_operations(cache_service):
    """Test set operations."""
    # Test adding to set
    assert cache_service.add_to_set("test_set", "value1", "value2")
    
    # Test getting set
    result = cache_service.get_set("test_set")
    assert isinstance(result, set)
    assert "value1" in result
    assert "value2" in result

def test_clear_pattern(cache_service):
    """Test clearing keys by pattern."""
    # Set some test keys
    cache_service.set("test:1", "value1")
    cache_service.set("test:2", "value2")
    cache_service.set("other:1", "value3")
    
    # Clear test:* pattern
    assert cache_service.clear_pattern("test:*")
    
    # Check results
    assert not cache_service.exists("test:1")
    assert not cache_service.exists("test:2")
    assert cache_service.exists("other:1")

def test_cached_decorator_sync(cache_service):
    """Test cached decorator with sync function."""
    class TestClass:
        def __init__(self):
            self.cache_service = cache_service
        
        @cached("test_prefix")
        def test_method(self, arg1, arg2):
            return f"{arg1}:{arg2}"
    
    test_instance = TestClass()
    
    # First call should compute value
    result1 = test_instance.test_method("a", "b")
    assert result1 == "a:b"
    
    # Second call should use cache
    result2 = test_instance.test_method("a", "b")
    assert result2 == "a:b"
    
    # Different arguments should compute new value
    result3 = test_instance.test_method("c", "d")
    assert result3 == "c:d"

@pytest.mark.asyncio
async def test_cached_decorator_async(cache_service):
    """Test cached decorator with async function."""
    class TestClass:
        def __init__(self):
            self.cache_service = cache_service
        
        @cached("test_prefix")
        async def test_method(self, arg1, arg2):
            await asyncio.sleep(0.1)
            return f"{arg1}:{arg2}"
    
    test_instance = TestClass()
    
    # First call should compute value
    result1 = await test_instance.test_method("a", "b")
    assert result1 == "a:b"
    
    # Second call should use cache
    result2 = await test_instance.test_method("a", "b")
    assert result2 == "a:b"
    
    # Different arguments should compute new value
    result3 = await test_instance.test_method("c", "d")
    assert result3 == "c:d"

def test_cached_decorator_custom_key(cache_service):
    """Test cached decorator with custom key builder."""
    def custom_key_builder(arg1, arg2):
        return f"custom:{arg1}:{arg2}"
    
    class TestClass:
        def __init__(self):
            self.cache_service = cache_service
        
        @cached("test_prefix", key_builder=custom_key_builder)
        def test_method(self, arg1, arg2):
            return f"{arg1}:{arg2}"
    
    test_instance = TestClass()
    
    # First call should compute value
    result1 = test_instance.test_method("a", "b")
    assert result1 == "a:b"
    
    # Check if custom key was used
    assert cache_service.exists("custom:a:b")
    
    # Second call should use cache
    result2 = test_instance.test_method("a", "b")
    assert result2 == "a:b" 