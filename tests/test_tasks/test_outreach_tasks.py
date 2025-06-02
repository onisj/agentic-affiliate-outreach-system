import pytest
from unittest.mock import patch, MagicMock
from tasks.outreach_tasks import send_outreach_message
from database.models import AffiliateProspect, MessageTemplate, MessageType

@pytest.fixture
def db_session():
    return MagicMock()

def test_send_outreach_message_email_success(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        with patch("services.email_service.EmailService.send_email", return_value=True):
            with patch("services.email_service.EmailService.personalize_message", return_value="Personalized content"):
                prospect_id = str(uuid4())
                template_id = str(uuid4())
                db_session.query.return_value.filter.return_value.first.side_effect = [
                    AffiliateProspect(id=prospect_id, email="test@example.com", consent_given=True),
                    MessageTemplate(id=template_id, content="Hi {{first_name}}", subject="Test", message_type=MessageType.EMAIL)
                ]
                result = send_outreach_message(prospect_id, template_id, "email")
                assert result["success"] is True
                assert "message_id" in result

def test_send_outreach_message_no_consent(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        prospect_id = str(uuid4())
        template_id = str(uuid4())
        db_session.query.return_value.filter.return_value.first.return_value = AffiliateProspect(
            id=prospect_id, email="test@example.com", consent_given=False
        )
        result = send_outreach_message(prospect_id, template_id, "email")
        assert result["success"] is False
        assert "No consent given" in result["error"]

def test_send_outreach_message_twitter_missing_user_id(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        prospect_id = str(uuid4())
        template_id = str(uuid4())
        db_session.query.return_value.filter.return_value.first.side_effect = [
            AffiliateProspect(id=prospect_id, consent_given=True, social_profiles={}),
            MessageTemplate(id=template_id, content="Hi", message_type=MessageType.TWITTER)
        ]
        result = send_outreach_message(prospect_id, template_id, "twitter")
        assert result["success"] is False
        assert "Twitter user ID not found" in result["error"]