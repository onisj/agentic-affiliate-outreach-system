import pytest
from unittest.mock import patch, MagicMock
from tasks.sequence_tasks import process_sequence_step
from database.models import AffiliateProspect, Sequence, MessageLog, MessageTemplate, MessageType, MessageStatus
from uuid import uuid4

@pytest.fixture
def db_session():
    return MagicMock()

def test_process_sequence_step_success(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        with patch("services.email_service.EmailService.send_email", return_value=True):
            with patch("services.email_service.EmailService.personalize_message", return_value="Personalized content"):
                prospect_id = str(uuid4())
                campaign_id = str(uuid4())
                template_id = str(uuid4())
                
                db_session.query.return_value.filter.return_value.first.side_effect = [
                    AffiliateProspect(id=prospect_id, email="test@example.com", consent_given=True),
                    None,  # No previous message
                    Sequence(campaign_id=campaign_id, step_number=1, template_id=template_id, delay_days=0, condition={}),
                    MessageTemplate(id=template_id, content="Hi", subject="Test", message_type=MessageType.EMAIL)
                ]
                
                result = process_sequence_step(prospect_id, campaign_id)
                assert result["success"] is True
                assert "message_id" in result

def test_process_sequence_step_no_consent(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        prospect_id = str(uuid4())
        campaign_id = str(uuid4())
        db_session.query.return_value.filter.return_value.first.return_value = AffiliateProspect(
            id=prospect_id, consent_given=False
        )
        result = process_sequence_step(prospect_id, campaign_id)
        assert result["success"] is False
        assert "no consent" in result["error"]