import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from database.models import Content
from uuid import uuid4
from datetime import datetime

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    return MagicMock()

def test_create_content_success(client, db_session):
    with patch("api.routers.content.get_db", return_value=iter([db_session])):
        content_data = {
            "name": "default_signup",
            "content_type": "landing_page",
            "data": {
                "title": "Test Title",
                "headline": "Test Headline",
                "description": "Test Description",
                "cta": "Test CTA"
            }
        }
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add = MagicMock()
        db_session.commit = MagicMock()
        db_session.refresh = MagicMock()
        
        response = client.post("/content/", json=content_data)
        assert response.status_code == 200
        assert response.json()["name"] == "default_signup"
        assert response.json()["content_type"] == "landing_page"
        assert response.json()["data"]["title"] == "Test Title"

def test_create_content_duplicate(client, db_session):
    with patch("api.routers.content.get_db", return_value=iter([db_session])):
        content_data = {
            "name": "default_signup",
            "content_type": "landing_page",
            "data": {"title": "Test"}
        }
        db_session.query.return_value.filter.return_value.first.return_value = Content(
            id=uuid4(), name="default_signup", content_type="landing_page"
        )
        response = client.post("/content/", json=content_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

def test_get_content_success(client, db_session):
    with patch("api.routers.content.get_db", return_value=iter([db_session])):
        content_id = uuid4()
        db_session.query.return_value.filter.return_value.first.return_value = Content(
            id=content_id,
            name="default_signup",
            content_type="landing_page",
            data={"title": "Test Title"},
            created_at=datetime.utcnow()
        )
        response = client.get(f"/content/{content_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "default_signup"
        assert response.json()["data"]["title"] == "Test Title"

def test_get_content_not_found(client, db_session):
    with patch("api.routers.content.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.get(f"/content/{uuid4()}")
        assert response.status_code == 404
        assert "Content not found" in response.json()["detail"]