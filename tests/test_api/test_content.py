from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from database.models import Content
from datetime import datetime, timezone

def test_create_content_success(client: TestClient, reset_db):
    with patch("api.routers.content.get_db", return_value=iter([reset_db])):
        content_data = {
            "name": "default_signup",
            "content_type": "landing_page",
            "data": {"title": "Test Title", "headline": "Test Headline", "content": "Test Description", "cta": "Sign Up"}
        }
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = None  # No existing content
        response = client.post("/content/", json=content_data)
        assert response.status_code == 200
        assert response.json()["name"] == content_data["name"]

def test_get_content_success(client: TestClient, reset_db):
    with patch("api.routers.content.get_db", return_value=iter([reset_db])):
        content_id = str(uuid4())
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = Content(
            id=content_id,
            name="default_signup",
            content_type="landing_page",
            data={"title": "Test Title"},
            created_at=datetime.now(timezone.utc)
        )
        response = client.get(f"/content/{content_id}")
        assert response.status_code == 200
        assert response.json()["id"] == content_id