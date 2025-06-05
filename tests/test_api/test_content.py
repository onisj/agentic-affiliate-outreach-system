from fastapi.testclient import TestClient
from uuid import uuid4
from database.models import Content
from datetime import datetime, timezone

def test_create_content_success(client: TestClient, reset_db):
    content_data = {
        "name": "default_signup",
        "content_type": "landing_page",
        "data": {"title": "Test Title", "headline": "Test Headline", "content": "Test Description", "cta": "Sign Up"}
    }
    response = client.post("/content/", json=content_data)
    assert response.status_code == 200
    assert response.json()["name"] == content_data["name"]

def test_get_content_success(client: TestClient, reset_db):
    # First, create the content
    content_data = {
        "name": "default_signup",
        "content_type": "landing_page",
        "data": {"title": "Test Title"}
    }
    post_response = client.post("/content/", json=content_data)
    if post_response.status_code != 200:
        print("POST response:", post_response.json())
    assert post_response.status_code == 200
    content_id = post_response.json()["id"]
    # Now, retrieve it
    get_response = client.get(f"/content/{content_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == content_id