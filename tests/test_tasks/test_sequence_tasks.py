from app.tasks.sequence_tasks import process_sequence_step
from unittest.mock import patch, MagicMock
from uuid import uuid4
from database.models import AffiliateProspect, Sequence, MessageTemplate, MessageType
from datetime import datetime, timezone

def test_process_sequence_step_success(reset_db):
    with patch("database.session.get_db", return_value=iter([reset_db])):
        with patch("services.email_service.EmailService.send_email", return_value=True):
            with patch("services.email_service.EmailService.personalize_message", return_value="Personalized content"):
                prospect_id = str(uuid4())
                campaign_id = str(uuid4())
                template_id = str(uuid4())
                mock_query = MagicMock()
                reset_db.query = mock_query
                mock_query.return_value.filter.return_value.first.side_effect = [
                    AffiliateProspect(id=prospect_id, email="test@example.com", consent_given=True, created_at=datetime.now(timezone.utc)),
                    None,  # No previous message
                    Sequence(campaign_id=campaign_id, step_number=1, template_id=template_id, delay_days=0, condition={}),
                    MessageTemplate(id=template_id, content="Hi", subject="Test", message_type=MessageType.EMAIL, created_at=datetime.now(timezone.utc))
                ]
                result = process_sequence_step(prospect_id, campaign_id)
                assert result["success"] is True

def test_process_sequence_step_no_consent(reset_db):
    with patch("database.session.get_db", return_value=iter([reset_db])):
        prospect_id = str(uuid4())
        campaign_id = str(uuid4())
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = AffiliateProspect(
            id=prospect_id, email="test@example.com", consent_given=False, created_at=datetime.now(timezone.utc)
        )
        result = process_sequence_step(prospect_id, campaign_id)
        assert result["success"] is False