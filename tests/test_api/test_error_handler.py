import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from api.middleware.error_handler import ErrorHandlerMiddleware, DatabaseErrorHandler, RateLimitMiddleware
from services.logging_service import LoggingService
import time
from sqlalchemy.exc import SQLAlchemyError

@pytest.fixture
def logger():
    """Create a logger instance for testing."""
    return LoggingService(enable_console=False)

@pytest.fixture
def app(logger):
    """Create a FastAPI application with middleware for testing."""
    app = FastAPI()
    
    # Add error handler middleware
    app.add_middleware(
        ErrorHandlerMiddleware,
        logger=logger,
        exclude_paths=["/health"]
    )
    
    # Add database error handler
    app.add_middleware(
        DatabaseErrorHandler,
        logger=logger
    )
    
    # Add rate limit middleware
    app.add_middleware(
        RateLimitMiddleware,
        logger=logger,
        rate_limit=2,  # 2 requests per second
        exclude_paths=["/health"]
    )
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/error")
    async def error_endpoint():
        raise HTTPException(status_code=400, detail="Bad Request")
    
    @app.get("/db-error")
    async def db_error_endpoint():
        raise SQLAlchemyError("Database error")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app

@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)

def test_successful_request(client):
    """Test successful request handling."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}

def test_error_handling(client):
    """Test error handling middleware."""
    response = client.get("/error")
    assert response.status_code == 400
    assert "detail" in response.json()
    assert response.json()["detail"] == "Bad Request"

def test_database_error_handling(client):
    """Test database error handling middleware."""
    response = client.get("/db-error")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Database error" in response.json()["detail"]

def test_excluded_path(client):
    """Test that excluded paths bypass error handling."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_rate_limiting(client):
    """Test rate limiting middleware."""
    # First request should succeed
    response1 = client.get("/test")
    assert response1.status_code == 200
    
    # Second request should succeed
    response2 = client.get("/test")
    assert response2.status_code == 200
    
    # Third request should be rate limited
    response3 = client.get("/test")
    assert response3.status_code == 429
    assert "detail" in response3.json()
    assert "Rate limit exceeded" in response3.json()["detail"]

def test_rate_limit_reset(client):
    """Test that rate limit resets after the time window."""
    # Make two requests
    client.get("/test")
    client.get("/test")
    
    # Wait for rate limit window to reset
    time.sleep(1.1)
    
    # Next request should succeed
    response = client.get("/test")
    assert response.status_code == 200

def test_rate_limit_excluded_path(client):
    """Test that excluded paths bypass rate limiting."""
    # Make multiple requests to excluded path
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200

def test_request_id_generation(client):
    """Test that request IDs are generated and included in responses."""
    response = client.get("/test")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]

def test_error_response_format(client):
    """Test the format of error responses."""
    response = client.get("/error")
    assert response.status_code == 400
    error_data = response.json()
    
    assert "detail" in error_data
    assert "request_id" in error_data
    assert "timestamp" in error_data

def test_database_error_response_format(client):
    """Test the format of database error responses."""
    response = client.get("/db-error")
    assert response.status_code == 500
    error_data = response.json()
    
    assert "detail" in error_data
    assert "request_id" in error_data
    assert "timestamp" in error_data
    assert "Database error" in error_data["detail"] 