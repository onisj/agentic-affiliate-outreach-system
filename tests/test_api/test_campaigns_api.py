import pytest
from fastapi.testclient import TestClient
from tests.utils import (
    test_client, db_session, redis_client, mock_services,
    create_test_campaign, create_test_template, create_test_prospect,
    TestData, with_db_rollback, with_redis_cache
)

@pytest.mark.api
class TestCampaignsAPI:
    """API tests for the campaigns endpoints."""

    def test_create_campaign(self, test_client: TestClient, db_session):
        """Test creating a new campaign via API."""
        # Arrange
        campaign_data = TestData.CAMPAIGN

        # Act
        response = test_client.post("/api/campaigns/", json=campaign_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == campaign_data["name"]
        assert data["status"] == campaign_data["status"]

    @with_db_rollback
    def test_get_campaign(self, test_client: TestClient, db_session):
        """Test getting a campaign by ID via API."""
        # Arrange
        campaign = create_test_campaign(db_session)
        assert campaign is not None, "Failed to create campaign for test_get_campaign"

        # Act
        response = test_client.get(f"/api/campaigns/{campaign.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign.id
        assert data["name"] == campaign.name

    @with_db_rollback
    def test_update_campaign(self, test_client: TestClient, db_session):
        """Test updating a campaign via API."""
        # Arrange
        campaign = create_test_campaign(db_session)
        update_data = {
            "name": "Updated Campaign",
            "status": "active"
        }

        # Act
        response = test_client.patch(
            f"/api/campaigns/{campaign.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["status"] == update_data["status"]

    @with_db_rollback
    def test_delete_campaign(self, test_client: TestClient, db_session):
        """Test deleting a campaign via API."""
        # Arrange
        campaign = create_test_campaign(db_session)

        # Act
        response = test_client.delete(f"/api/campaigns/{campaign.id}")

        # Assert
        assert response.status_code == 204

    @with_db_rollback
    @with_redis_cache
    def test_list_campaigns(self, test_client: TestClient, db_session, redis_client):
        """Test listing campaigns via API."""
        # Arrange
        create_test_campaign(db_session)
        create_test_campaign(db_session, {
            **TestData.CAMPAIGN,
            "name": "Campaign 2"
        })

        # Act
        response = test_client.get("/api/campaigns/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @with_db_rollback
    def test_add_prospect_to_campaign(self, test_client: TestClient, db_session):
        """Test adding a prospect to a campaign via API."""
        # Arrange
        campaign = create_test_campaign(db_session)
        prospect = create_test_prospect(db_session)

        # Act
        response = test_client.post(
            f"/api/campaigns/{campaign.id}/prospects/{prospect.id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert prospect.id in data["prospect_ids"]

    @with_db_rollback
    def test_remove_prospect_from_campaign(self, test_client: TestClient, db_session):
        """Test removing a prospect from a campaign via API."""
        # Arrange
        campaign = create_test_campaign(db_session)
        prospect = create_test_prospect(db_session)
        assert campaign is not None, "Failed to create campaign for test_remove_prospect_from_campaign"
        assert prospect is not None, "Failed to create prospect for test_remove_prospect_from_campaign"
        campaign.prospects.append(prospect)
        db_session.commit()

        # Act
        response = test_client.delete(
            f"/api/campaigns/{campaign.id}/prospects/{prospect.id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert prospect.id not in data["prospect_ids"]

    @pytest.mark.integration
    def test_campaign_workflow(self, test_client: TestClient, db_session):
        """Test the complete campaign workflow via API."""
        # Arrange
        campaign_data = TestData.CAMPAIGN
        template = create_test_template(db_session)
        prospect = create_test_prospect(db_session)

        # Act - Create campaign
        create_response = test_client.post("/api/campaigns/", json=campaign_data)
        assert create_response.status_code == 201
        campaign_id = create_response.json()["id"]

        # Act - Add template to campaign
        template_response = test_client.post(
            f"/api/campaigns/{campaign_id}/templates/{template.id}"
        )
        assert template_response.status_code == 200

        # Act - Add prospect to campaign
        prospect_response = test_client.post(
            f"/api/campaigns/{campaign_id}/prospects/{prospect.id}"
        )
        assert prospect_response.status_code == 200

        # Act - Start campaign
        start_response = test_client.post(f"/api/campaigns/{campaign_id}/start")
        assert start_response.status_code == 200

        # Assert
        final_response = test_client.get(f"/api/campaigns/{campaign_id}")
        assert final_response.status_code == 200
        data = final_response.json()
        assert data["status"] == "active"
        assert template.id in data["template_ids"]
        assert prospect.id in data["prospect_ids"] 