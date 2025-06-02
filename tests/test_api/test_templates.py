import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from database.models import MessageTemplate, MessageType
from uuid import uuid4

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    return MagicMock()

def test_create_template_success(client, db_session):
    with patch("api.routers.templates.get_db", return_value=iter([db_session])):
        template_data = {
            "name": "Welcome Email",
            "subject": "Join Our Program",
            "content": "Hi {{first_name}}, ...",
            "message_type": "email"
        }
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add = MagicMock()
        db_session.commit = MagicMock()
        db_session.refresh = MagicMock()
        
        response = client.post("/templates/", json=template_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Welcome Email"
        assert response.json()["message_type"] == "email"

def test_create_template_invalid_message_type(client, db_session):
    with patch("api.routers.templates.get_db", return_value=iter([db_session])):
        template_data = {
            "name": "Invalid Template",
            "content": "Test content",
            "message_type": "invalid"
        }
        response = client.post("/templates/", json=template_data)
        assert response.status_code == 400
        assert "Invalid message type" in response.json()["detail"]

def test_get_templates(client, db_session):
    with patch("api.routers.templates.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            MessageTemplate(id=uuid4(), name="Template 1", content="Content 1", message_type=MessageType.EMAIL, is_active=True),
            MessageTemplate(id=uuid4(), name="Template 2", content="Content 2", message_type=MessageType.LINKEDIN, is_active=True)
        ]
        response = client.get("/templates/")
        assert response.status_code == 200
        assert len(response.json()) == 2

def test_get_template_not_found(client, db_session):
    with patch("api.routers.templates.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.get(f"/templates/{uuid4()}")
        assert response.status_code == 404
        assert "Template not found" in response.json()["detail"]

def test_update_template_success(client, db_session):
    with patch("api.routers.templates.get_db", return_value=iter([db_session])):
        template_id = uuid4()
        db_session.query.return_value.filter.return_value.first.return_value = MessageTemplate(
            id=template_id, name="Old Name", content="Old Content", message_type=MessageType.EMAIL
        )
        update_data = {
            "name": "Updated Name",
            "subject": "Updated Subject",
            "content": "Updated Content",
            "message_type": "linkedin"
        }
        response = client.put(f"/templates/{template_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["message_type"] == "linkedin"

def test_delete_template_success(client, db_session):
    with patch("api.routers.templates.get_db", return_value=iter([db_session])):
        template_id = uuid4()
        db_session.query.return_value.filter.return_value.first.return_value = MessageTemplate(
            id=template_id, name="Test Template", is_active=True
        )
        response = client.delete(f"/templates/{template_id}")
        assert response.status_code == 200
        assert "Template deactivated" in response.json()["message"]