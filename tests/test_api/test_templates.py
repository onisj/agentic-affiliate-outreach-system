from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from database.models import MessageTemplate, MessageType
from datetime import datetime, timezone

def test_create_template_success(client: TestClient, reset_db):
    with patch("api.routers.templates.get_db", return_value=iter([reset_db])):
        template_data = {
            "name": "Welcome Email",
            "subject": "Join Our Program",
            "content": "Hi {{first_name}}, ...",
            "message_type": "email"
        }
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = None  # No existing template
        response = client.post("/templates/", json=template_data)
        assert response.status_code == 201
        assert response.json()["name"] == template_data["name"]

def test_get_templates(client: TestClient, reset_db):
    with patch("api.routers.templates.get_db", return_value=iter([reset_db])):
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            MessageTemplate(
                id=str(uuid4()),
                name="Template 1",
                content="Content 1",
                message_type=MessageType.EMAIL,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_active=True
            ),
            MessageTemplate(
                id=str(uuid4()),
                name="Template 2",
                content="Content 2",
                message_type=MessageType.LINKEDIN,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_active=True
            )
        ]
        response = client.get("/templates/")
        assert response.status_code == 200
        assert len(response.json()) == 2

def test_update_template_success(client: TestClient, reset_db):
    with patch("api.routers.templates.get_db", return_value=iter([reset_db])):
        template_id = str(uuid4())
        mock_query = MagicMock()
        reset_db.query = mock_query
        template = MessageTemplate(
            id=template_id,
            name="Old Name",
            content="Old Content",
            message_type=MessageType.EMAIL,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True
        )
        reset_db.add(template)
        mock_query.return_value.filter.return_value.first.return_value = template
        update_data = {
            "name": "Updated Name",
            "subject": "Updated Subject",
            "content": "Updated Content",
            "message_type": "linkedin"
        }
        response = client.put(f"/templates/{template_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]

def test_delete_template_success(client: TestClient, reset_db):
    with patch("api.routers.templates.get_db", return_value=iter([reset_db])):
        template_id = str(uuid4())
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = MessageTemplate(
            id=template_id, name="Test Template", is_active=True, created_at=datetime.now(timezone.utc)
        )
        response = client.delete(f"/templates/{template_id}")
        assert response.status_code == 200

def test_create_template_invalid_message_type(client: TestClient, reset_db):
    with patch("api.routers.templates.get_db", return_value=iter([reset_db])):
        template_data = {
            "name": "Invalid Template",
            "subject": "Test",
            "content": "Content",
            "message_type": "invalid"
        }
        response = client.post("/templates/", json=template_data)
        assert response.status_code == 400