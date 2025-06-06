import pytest
from fastapi.testclient import TestClient
from tests.utils import (
    test_client, db_session, redis_client, mock_services,
    create_test_prospect, TestData, with_db_rollback, with_redis_cache
)

@pytest.mark.api
class TestProspectsAPI:
    """API tests for the prospects endpoints."""

    def test_create_prospect(self, test_client: TestClient, db_session):
        """Test creating a new prospect via API."""
        # Arrange
        prospect_data = TestData.PROSPECT

        # Act
        response = test_client.post("/api/prospects/", json=prospect_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == prospect_data["email"]
        assert data["name"] == prospect_data["name"]

    @with_db_rollback
    def test_get_prospect(self, test_client: TestClient, db_session):
        """Test getting a prospect via API."""
        # Arrange
        prospect = create_test_prospect(db_session)

        # Act
        response = test_client.get(f"/api/prospects/{prospect.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prospect.id
        assert data["email"] == prospect.email

    @with_db_rollback
    def test_update_prospect(self, test_client: TestClient, db_session):
        """Test updating a prospect via API."""
        # Arrange
        prospect = create_test_prospect(db_session)
        update_data = {"name": "Updated Name"}

        # Act
        response = test_client.patch(
            f"/api/prospects/{prospect.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]

    @with_db_rollback
    def test_delete_prospect(self, test_client: TestClient, db_session):
        """Test deleting a prospect via API."""
        # Arrange
        prospect = create_test_prospect(db_session)

        # Act
        response = test_client.delete(f"/api/prospects/{prospect.id}")

        # Assert
        assert response.status_code == 204

    @with_db_rollback
    @with_redis_cache
    def test_list_prospects(self, test_client: TestClient, db_session, redis_client):
        """Test listing prospects via API."""
        # Arrange
        create_test_prospect(db_session)
        create_test_prospect(db_session, {
            **TestData.PROSPECT,
            "email": "test2@example.com"
        })

        # Act
        response = test_client.get("/api/prospects/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.twitter
    def test_fetch_twitter_data(self, test_client: TestClient, mock_services):
        """Test fetching Twitter data via API."""
        # Arrange
        twitter_handle = "@test_user"

        # Act
        response = test_client.get(f"/api/prospects/twitter/{twitter_handle}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user"
        assert data["followers_count"] == 1000

    @pytest.mark.linkedin
    def test_fetch_linkedin_data(self, test_client: TestClient, mock_services):
        """Test fetching LinkedIn data via API."""
        # Arrange
        linkedin_url = "https://linkedin.com/in/test"

        # Act
        response = test_client.get(f"/api/prospects/linkedin/{linkedin_url}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["firstName"] == "Test"
        assert data["lastName"] == "User"

    @pytest.mark.integration
    def test_prospect_workflow(self, test_client: TestClient, db_session, mock_services):
        """Test the complete prospect workflow via API."""
        # Arrange
        prospect_data = TestData.PROSPECT

        # Act - Create prospect
        create_response = test_client.post("/api/prospects/", json=prospect_data)
        assert create_response.status_code == 201
        prospect_id = create_response.json()["id"]

        # Act - Fetch Twitter data
        twitter_response = test_client.get(f"/api/prospects/twitter/{prospect_data['twitter_handle']}")
        assert twitter_response.status_code == 200

        # Act - Fetch LinkedIn data
        linkedin_response = test_client.get(f"/api/prospects/linkedin/{prospect_data['linkedin_url']}")
        assert linkedin_response.status_code == 200

        # Act - Update prospect with social data
        update_response = test_client.patch(
            f"/api/prospects/{prospect_id}",
            json={
                "twitter_data": twitter_response.json(),
                "linkedin_data": linkedin_response.json()
            }
        )
        assert update_response.status_code == 200

        # Assert
        final_response = test_client.get(f"/api/prospects/{prospect_id}")
        assert final_response.status_code == 200
        data = final_response.json()
        assert data["twitter_data"]["username"] == "test_user"
        assert data["linkedin_data"]["firstName"] == "Test" 