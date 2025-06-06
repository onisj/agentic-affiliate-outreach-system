import pytest
from fastapi.testclient import TestClient
from tests.utils import (
    test_client, db_session, redis_client, mock_services,
    create_test_template, TestData, with_db_rollback, with_redis_cache
)

@pytest.mark.api
class TestTemplatesAPI:
    """API tests for the templates endpoints."""

    def test_create_template(self, test_client: TestClient, db_session):
        """Test creating a new template via API."""
        # Arrange
        template_data = TestData.TEMPLATE

        # Act
        response = test_client.post("/api/templates/", json=template_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["subject"] == template_data["subject"]
        assert data["body"] == template_data["body"]

    @with_db_rollback
    def test_get_template(self, test_client: TestClient, db_session):
        """Test getting a template via API."""
        # Arrange
        template = create_test_template(db_session)

        # Act
        response = test_client.get(f"/api/templates/{template.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template.id
        assert data["name"] == template.name

    @with_db_rollback
    def test_update_template(self, test_client: TestClient, db_session):
        """Test updating a template via API."""
        # Arrange
        template = create_test_template(db_session)
        update_data = {
            "name": "Updated Template",
            "subject": "Updated Subject"
        }

        # Act
        response = test_client.patch(
            f"/api/templates/{template.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["subject"] == update_data["subject"]

    @with_db_rollback
    def test_delete_template(self, test_client: TestClient, db_session):
        """Test deleting a template via API."""
        # Arrange
        template = create_test_template(db_session)

        # Act
        response = test_client.delete(f"/api/templates/{template.id}")

        # Assert
        assert response.status_code == 204

    @with_db_rollback
    @with_redis_cache
    def test_list_templates(self, test_client: TestClient, db_session, redis_client):
        """Test listing templates via API."""
        # Arrange
        create_test_template(db_session)
        create_test_template(db_session, {
            **TestData.TEMPLATE,
            "name": "Template 2"
        })

        # Act
        response = test_client.get("/api/templates/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.integration
    def test_template_workflow(self, test_client: TestClient, db_session):
        """Test the complete template workflow via API."""
        # Arrange
        template_data = TestData.TEMPLATE

        # Act - Create template
        create_response = test_client.post("/api/templates/", json=template_data)
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Act - Update template
        update_data = {
            "name": "Updated Template",
            "subject": "Updated Subject",
            "body": "Updated body content"
        }
        update_response = test_client.patch(
            f"/api/templates/{template_id}",
            json=update_data
        )
        assert update_response.status_code == 200

        # Act - Get updated template
        get_response = test_client.get(f"/api/templates/{template_id}")
        assert get_response.status_code == 200

        # Assert
        data = get_response.json()
        assert data["name"] == update_data["name"]
        assert data["subject"] == update_data["subject"]
        assert data["body"] == update_data["body"] 