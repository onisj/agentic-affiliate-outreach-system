import pytest
from fastapi.testclient import TestClient
from api.main import app
import os

client = TestClient(app)

def test_app_health():
    """Test that the app is running and responding."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_version():
    """Test that the API version endpoint is working."""
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_database_connection():
    """Test that the database connection is working."""
    response = client.get("/db-status")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"

if __name__ == "__main__":
    # Run these tests directly with: python -m tests.test_smoke
    pytest.main([__file__, "-v"]) 