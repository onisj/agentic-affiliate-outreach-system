import pytest
from uuid import uuid4
from unittest.mock import patch
from database.models import (
    MessageTemplate, OutreachCampaign, AffiliateProspect, 
    MessageType, CampaignStatus, ProspectStatus
)

@pytest.fixture
def test_template(db_session):
    """Create a test template for campaigns to use"""
    template = MessageTemplate(
        id=uuid4(),
        name="Test Email Template",
        message_type=MessageType.EMAIL,
        subject="Test Subject",
        content="Test email content with {{first_name}} placeholder",
        is_active=True
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template

@pytest.fixture
def inactive_template(db_session):
    """Create an inactive template to test edge cases"""
    template = MessageTemplate(
        id=uuid4(),
        name="Inactive Template",
        message_type=MessageType.EMAIL,
        subject="Inactive Subject",
        content="Inactive content",
        is_active=False
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template

@pytest.fixture
def campaign_data(test_template):
    return {
        "name": "Spring Campaign",
        "template_id": str(test_template.id),
        "target_criteria": {"min_score": 70, "industry": "tech"}
    }

@pytest.fixture
def test_prospects(db_session):
    """Create multiple test prospects with different scores and consent status"""
    prospects = []
    
    # High-scoring prospect with consent
    prospect1 = AffiliateProspect(
        id=uuid4(),
        email="high.score@example.com",
        first_name="John",
        last_name="Doe",
        company="TechCorp",
        qualification_score=85,
        consent_given=True,
        status=ProspectStatus.NEW
    )
    
    # Low-scoring prospect with consent
    prospect2 = AffiliateProspect(
        id=uuid4(),
        email="low.score@example.com",
        first_name="Jane",
        last_name="Smith",
        qualification_score=45,
        consent_given=True,
        status=ProspectStatus.NEW
    )
    
    # High-scoring prospect without consent
    prospect3 = AffiliateProspect(
        id=uuid4(),
        email="no.consent@example.com",
        first_name="Bob",
        last_name="Wilson",
        qualification_score=90,
        consent_given=False,
        status=ProspectStatus.NEW
    )
    
    prospects.extend([prospect1, prospect2, prospect3])
    db_session.add_all(prospects)
    db_session.commit()
    
    for prospect in prospects:
        db_session.refresh(prospect)
    
    return prospects

class TestCampaignCreation:
    """Test campaign creation functionality"""
    
    def test_create_campaign_success(self, client, campaign_data):
        """Test successful campaign creation with proper serialization"""
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == campaign_data["name"]
        assert data["status"] == CampaignStatus.DRAFT.value  # Use enum value
        assert data["template_id"] == campaign_data["template_id"]
        assert data["target_criteria"] == campaign_data["target_criteria"]
        
        # Verify all required fields are present and properly serialized
        assert "id" in data
        assert isinstance(data["id"], str)  # UUID serialized as string
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_campaign_inactive_template(self, client, inactive_template):
        """Test campaign creation with inactive template"""
        campaign_data = {
            "name": "Inactive Template Campaign",
            "template_id": str(inactive_template.id),
            "target_criteria": {"min_score": 70}
        }
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 404
        assert "Template not found or is inactive" in response.json()["detail"]

    def test_create_campaign_invalid_template_id(self, client):
        """Test campaign creation with invalid template ID"""
        invalid_campaign_data = {
            "name": "Invalid Campaign",
            "template_id": str(uuid4()),  # Non-existent template
            "target_criteria": {"min_score": 70}
        }
        response = client.post("/campaigns/", json=invalid_campaign_data)
        assert response.status_code == 404
        assert "Template not found or is inactive" in response.json()["detail"]

    def test_create_campaign_malformed_template_id(self, client):
        """Test campaign creation with malformed template ID"""
        invalid_campaign_data = {
            "name": "Invalid Campaign",
            "template_id": "not-a-valid-uuid",
            "target_criteria": {"min_score": 70}
        }
        response = client.post("/campaigns/", json=invalid_campaign_data)
        assert response.status_code == 422

    def test_create_campaign_empty_name(self, client, test_template):
        """Test campaign creation with empty name"""
        campaign_data = {
            "name": "",  # Empty name
            "template_id": str(test_template.id),
            "target_criteria": {}
        }
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 422  # Validation error

    def test_create_campaign_whitespace_name(self, client, test_template):
        """Test campaign creation with whitespace-only name"""
        campaign_data = {
            "name": "   ",  # Whitespace only
            "template_id": str(test_template.id),
            "target_criteria": {}
        }
        response = client.post("/campaigns/", json=campaign_data)
        # Should either fail validation or strip whitespace
        # Implementation depends on your business rules
        assert response.status_code in [201, 422]

class TestCampaignRetrieval:
    """Test campaign retrieval functionality"""
    
    def test_get_campaigns_empty(self, client):
        """Test getting campaigns when none exist"""
        response = client.get("/campaigns/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_campaigns_with_data(self, client, db_session, test_template):
        """Test campaign retrieval with proper serialization"""
        # Create test campaigns
        campaign1 = OutreachCampaign(
            name="Campaign 1",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.DRAFT
        )
        campaign2 = OutreachCampaign(
            name="Campaign 2", 
            template_id=test_template.id,
            target_criteria={"min_score": 60},
            status=CampaignStatus.ACTIVE
        )
        db_session.add_all([campaign1, campaign2])
        db_session.commit()

        response = client.get("/campaigns/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify serialization
        for campaign in data:
            assert isinstance(campaign["id"], str)
            assert isinstance(campaign["status"], str)
            assert campaign["status"] in ["draft", "active", "paused", "completed"]
            if campaign["template_id"]:
                assert isinstance(campaign["template_id"], str)

    def test_get_campaigns_with_pagination(self, client, db_session, test_template):
        """Test campaign retrieval with pagination"""
        # Create multiple campaigns
        campaigns = []
        for i in range(5):
            campaign = OutreachCampaign(
                name=f"Campaign {i}",
                template_id=test_template.id,
                target_criteria={"min_score": 50 + i*10},
                status=CampaignStatus.DRAFT
            )
            campaigns.append(campaign)
        
        db_session.add_all(campaigns)
        db_session.commit()

        # Test pagination
        response = client.get("/campaigns/?skip=0&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        response = client.get("/campaigns/?skip=3&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_campaign_by_id(self, client, db_session, test_template):
        """Test retrieving a specific campaign by ID"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Test Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 70},
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.get(f"/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["id"] == str(campaign_id)
        assert data["status"] == "draft"

    def test_get_campaign_not_found(self, client):
        """Test retrieving non-existent campaign"""
        non_existent_id = uuid4()
        response = client.get(f"/campaigns/{non_existent_id}")
        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]

    def test_get_campaign_invalid_id_format(self, client):
        """Test retrieving campaign with invalid ID format"""
        response = client.get("/campaigns/not-a-valid-uuid")
        assert response.status_code == 400
        assert "Invalid campaign_id format" in response.json()["detail"]

class TestCampaignExecution:
    """Test campaign starting and execution functionality"""
    
    def test_start_campaign_success(self, client, db_session, test_template, test_prospects):
        """Test successful campaign start with qualified prospects"""
        # Create campaign
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Test Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 70},  # Only high-scoring prospects
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        # Mock the celery task
        with patch("api.routers.campaigns.process_sequence_step.delay") as mock_process:
            response = client.post(f"/campaigns/{campaign_id}/start")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            
            # Should be called once for the high-scoring prospect with consent
            assert mock_process.call_count == 1
            args = mock_process.call_args[0]
            assert args[1] == str(campaign_id)

    def test_start_campaign_no_qualified_prospects(self, client, db_session, test_template):
        """Test starting campaign when no prospects meet criteria"""
        # Create campaign with very high minimum score
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="High Bar Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 95},  # Very high score
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/start")
        assert response.status_code == 400
        assert "No qualified prospects found" in response.json()["detail"]

    def test_start_campaign_not_in_draft_status(self, client, db_session, test_template):
        """Test starting campaign that's not in draft status"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Active Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.ACTIVE  # Already active
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/start")
        assert response.status_code == 400
        assert "active status" in response.json()["detail"].lower()

    def test_start_campaign_inactive_template(self, client, db_session, inactive_template, test_prospects):
        """Test starting campaign with inactive template"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Inactive Template Campaign",
            template_id=inactive_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/start")
        assert response.status_code == 404
        assert "Template not found or is inactive" in response.json()["detail"]

class TestCampaignStatusTransitions:
    """Test campaign status transitions"""
    
    def test_pause_active_campaign(self, client, db_session, test_template):
        """Test pausing an active campaign"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Active Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.ACTIVE
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"

    def test_resume_paused_campaign(self, client, db_session, test_template):
        """Test resuming a paused campaign"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Paused Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.PAUSED
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_pause_non_active_campaign(self, client, db_session, test_template):
        """Test pausing a non-active campaign"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Draft Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/pause")
        assert response.status_code == 400
        assert "Only ACTIVE campaigns can be paused" in response.json()["detail"]

class TestSpecialCases:
    """Test special cases and edge conditions"""
    
    def test_resume_non_paused_campaign(self, client, db_session, test_template):
        """Test resuming a campaign that's not paused"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Active Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.ACTIVE
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.post(f"/campaigns/{campaign_id}/resume")
        assert response.status_code == 400
        assert "Only PAUSED campaigns can be resumed" in response.json()["detail"]

    def test_start_campaign_with_empty_target_criteria(self, client, db_session, test_template, test_prospects):
        """Test starting campaign with empty target criteria"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="No Criteria Campaign",
            template_id=test_template.id,
            target_criteria={},  # Empty criteria
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        # Mock the celery task
        with patch("api.routers.campaigns.process_sequence_step.delay") as mock_process:
            response = client.post(f"/campaigns/{campaign_id}/start")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            
            # Should be called for all prospects with consent (2 prospects)
            assert mock_process.call_count == 2

    def test_campaign_operations_with_invalid_uuid_format(self, client):
        """Test all campaign operations with invalid UUID formats"""
        invalid_id = "not-a-valid-uuid"
        
        # Test pause with invalid ID
        response = client.post(f"/campaigns/{invalid_id}/pause")
        assert response.status_code == 400
        assert "Invalid campaign_id format" in response.json()["detail"]
        
        # Test resume with invalid ID
        response = client.post(f"/campaigns/{invalid_id}/resume")
        assert response.status_code == 400
        assert "Invalid campaign_id format" in response.json()["detail"]
        
        # Test start with invalid ID
        response = client.post(f"/campaigns/{invalid_id}/start")
        assert response.status_code == 400
        assert "Invalid campaign_id format" in response.json()["detail"]

    def test_campaign_operations_with_nonexistent_campaigns(self, client):
        """Test all campaign operations with non-existent campaign IDs"""
        nonexistent_id = uuid4()
        
        # Test pause with non-existent ID
        response = client.post(f"/campaigns/{nonexistent_id}/pause")
        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]
        
        # Test resume with non-existent ID
        response = client.post(f"/campaigns/{nonexistent_id}/resume")
        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]
        
        # Test start with non-existent ID
        response = client.post(f"/campaigns/{nonexistent_id}/start")
        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]

class TestCampaignSerialization:
    """Test campaign data serialization edge cases"""
    
    def test_campaign_with_null_template_id(self, client, db_session):
        """Test campaign retrieval when template_id is null"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="No Template Campaign",
            template_id=None,  # Null template
            target_criteria={"min_score": 50},
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.get(f"/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] is None
        assert data["name"] == "No Template Campaign"

    def test_campaign_with_complex_target_criteria(self, client, campaign_data):
        """Test campaign creation with complex target criteria"""
        complex_criteria = {
            "min_score": 70,
            "industry": ["tech", "finance"],
            "company_size": {"min": 50, "max": 500},
            "location": {"country": "US", "excluded_states": ["CA", "NY"]},
            "tags": ["high_priority", "warm_lead"]
        }
        campaign_data["target_criteria"] = complex_criteria
        
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["target_criteria"] == complex_criteria

class TestCampaignConcurrency:
    """Test campaign operations under concurrent conditions"""
    
    def test_concurrent_campaign_status_changes(self, client, db_session, test_template):
        """Test handling concurrent status change requests"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Concurrent Test Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.ACTIVE
        )
        db_session.add(campaign)
        db_session.commit()

        # First pause should succeed
        response1 = client.post(f"/campaigns/{campaign_id}/pause")
        assert response1.status_code == 200
        assert response1.json()["status"] == "paused"
        
        # Second pause should fail since campaign is already paused
        response2 = client.post(f"/campaigns/{campaign_id}/pause")
        assert response2.status_code == 400
        assert "Only ACTIVE campaigns can be paused" in response2.json()["detail"]

class TestCampaignValidation:
    """Test comprehensive campaign validation"""
    
    def test_create_campaign_with_very_long_name(self, client, test_template):
        """Test campaign creation with name at maximum length"""
        long_name = "A" * 255  # Maximum allowed length
        campaign_data = {
            "name": long_name,
            "template_id": str(test_template.id),
            "target_criteria": {"min_score": 70}
        }
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 201
        assert response.json()["name"] == long_name

    def test_create_campaign_with_too_long_name(self, client, test_template):
        """Test campaign creation with name exceeding maximum length"""
        too_long_name = "A" * 256  # Exceeds maximum length
        campaign_data = {
            "name": too_long_name,
            "template_id": str(test_template.id),
            "target_criteria": {"min_score": 70}
        }
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 422  # Validation error

    def test_create_campaign_missing_required_fields(self, client):
        """Test campaign creation with missing required fields"""
        # Missing name
        response = client.post("/campaigns/", json={
            "template_id": str(uuid4()),
            "target_criteria": {}
        })
        assert response.status_code == 422
        
        # Missing template_id
        response = client.post("/campaigns/", json={
            "name": "Test Campaign",
            "target_criteria": {}
        })
        assert response.status_code == 422

class TestCampaignErrorHandling:
    """Test error handling in campaign operations"""
    
    def test_database_error_handling_on_creation(self, client, db_session, campaign_data):
        """Test handling of database errors during campaign creation"""
        # Patch the add method of the db_session to raise an exception
        with patch.object(db_session, 'add', side_effect=Exception("Database connection lost")):
            response = client.post("/campaigns/", json=campaign_data)
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_celery_task_failure_handling(self, client, db_session, test_template, test_prospects):
        """Test handling when Celery task queueing fails"""
        campaign_id = uuid4()
        campaign = OutreachCampaign(
            id=campaign_id,
            name="Task Failure Test",
            template_id=test_template.id,
            target_criteria={"min_score": 70},
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        # Mock celery task to raise exception
        with patch("api.routers.campaigns.process_sequence_step.delay") as mock_process:
            mock_process.side_effect = Exception("Celery broker unavailable")
            
            response = client.post(f"/campaigns/{campaign_id}/start")
            # Campaign should still be marked as ACTIVE even if some tasks fail
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"

class TestCampaignPagination:
    """Test pagination edge cases"""
    
    def test_pagination_with_large_skip_value(self, client, db_session, test_template):
        """Test pagination with skip value larger than total records"""
        # Create only 2 campaigns
        campaigns = []
        for i in range(2):
            campaign = OutreachCampaign(
                name=f"Campaign {i}",
                template_id=test_template.id,
                target_criteria={"min_score": 50},
                status=CampaignStatus.DRAFT
            )
            campaigns.append(campaign)
        
        db_session.add_all(campaigns)
        db_session.commit()

        # Request with skip=10 (larger than total records)
        response = client.get("/campaigns/?skip=10&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0  # Should return empty list

    def test_pagination_with_zero_limit(self, client, db_session, test_template):
        """Test pagination with limit=0"""
        campaign = OutreachCampaign(
            name="Test Campaign",
            template_id=test_template.id,
            target_criteria={"min_score": 50},
            status=CampaignStatus.DRAFT
        )
        db_session.add(campaign)
        db_session.commit()

        response = client.get("/campaigns/?skip=0&limit=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_pagination_with_negative_values(self, client):
        """Test pagination with negative skip/limit values"""
        # Test negative skip
        response = client.get("/campaigns/?skip=-1&limit=10")
        assert response.status_code == 422  # Should be validation error
        
        # Test negative limit
        response = client.get("/campaigns/?skip=0&limit=-1")
        assert response.status_code == 422  # Should be validation error