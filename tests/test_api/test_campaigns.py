import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from database.models import OutreachCampaign, MessageTemplate, CampaignStatus
from uuid import uuid4

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    return MagicMock()

def test_create_campaign_success(client, db_session):
    with patch("api.routers.campaigns.get_db", return_value=iter([db_session])):
        template_id = str(uuid4())
        db_session.query.return_value.filter.return_value.first.return_value = MessageTemplate(id=template_id)
        campaign_data = {
            "name": "Spring Campaign",
            "template_id": template_id,
            "target_criteria": {"min_score": 70}
        }
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Spring Campaign"
        assert response.json()["status"] == "draft"

def test_create_campaign_template_not_found(client, db_session):
    with patch("api.routers.campaigns.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.first.return_value = None
        campaign_data = {
            "name": "Invalid Campaign",
            "template_id": str(uuid4())
        }
        response = client.post("/campaigns/", json=campaign_data)
        assert response.status_code == 404
        assert "Template not found" in response.json()["detail"]

def test_get_campaigns(client, db_session):
    with patch("api.routers.campaigns.get_db", return_value=iter([db_session])):
        db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            OutreachCampaign(id=uuid4(), name="Campaign 1", status=CampaignStatus.DRAFT),
            OutreachCampaign(id=uuid4(), name="Campaign 2", status=CampaignStatus.ACTIVE)
        ]
        response = client.get("/campaigns/")
        assert response.status_code == 200
        assert len(response.json()) == 2

def test_get_campaign_not_found(client, db_session):
    with patch("api.routers.campaigns.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.get(f"/campaigns/{uuid4()}")
        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]

def test_start_campaign_success(client, db_session):
    with patch("api.routers.campaigns.get_db", return_value=iter([db_session])):
        with patch("tasks.outreach_tasks.send_outreach_message.delay", return_value=MagicMock(id="task_id")):
            campaign_id = uuid4()
            template_id = uuid4()
            db_session.query.return_value.filter.return_value.first.side_effect = [
                OutreachCampaign(id=campaign_id, status=CampaignStatus.DRAFT, template_id=template_id),
                MessageTemplate(id=template_id, message_type="email")
            ]
            db_session.query.return_value.filter.return_value.all.return_value = [
                MagicMock(id=uuid4(), consent_given=True, qualification_score=80)
            ]
            response = client.post(f"/campaigns/{campaign_id}/start")
            assert response.status_code == 200
            assert "Campaign started" in response.json()["message"]