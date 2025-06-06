import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from api.middleware.error_handler import ErrorHandlerMiddleware, RateLimitMiddleware
from app.services.logging_service import LoggingService
from sqlalchemy.exc import SQLAlchemyError

@pytest.fixture
def app():
    app = FastAPI()
    logger = LoggingService()
    
    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware, logger=logger)
    
    # Add rate limit middleware
    app.add_middleware(RateLimitMiddleware, logger=logger, rate_limit=100)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/error")
    async def error_endpoint():
        raise Exception("Test error")
    
    @app.get("/db-error")
    async def db_error_endpoint():
        raise SQLAlchemyError("Test database error")
    
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_successful_request(client):
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    assert "X-Request-ID" in response.headers

def test_error_handling(client):
    response = client.get("/error")
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "request_id" in data
    assert "timestamp" in data
    assert data["detail"] == "Test error"
    assert "X-Request-ID" in response.headers

def test_database_error_handling(client):
    response = client.get("/db-error")
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "request_id" in data
    assert "timestamp" in data
    assert "Test database error" in data["detail"]
    assert "X-Request-ID" in response.headers

def test_rate_limiting(client):
    # Make requests up to the rate limit
    for _ in range(100):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    data = response.json()
    assert "detail" in data
    assert "request_id" in data
    assert "timestamp" in data
    assert "Rate limit exceeded" in data["detail"]
    assert "X-Request-ID" in response.headers 