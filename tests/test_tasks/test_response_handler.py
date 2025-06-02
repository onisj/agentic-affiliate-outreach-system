import pytest
from unittest.mock import patch, MagicMock
from tasks.response_handler import handle_prospect_response
from database.models import MessageLog, AffiliateProspect, MessageTemplate, MessageStatus, ProspectStatus

@pytest.fixture
def db_session():
    return MagicMock()

def test_handle_positive_response(db_session):
    with patch("database.session.SessionLocal", return_value=db_session):
        with patch("services.email_service.EmailService.send_email", return_value=True):
            with patch("services.email_service.EmailService.personalize_message", return_value="Follow-up content"):
                with patch("textblob.TextBlob.sentiment", new_callable=MagicMock, return_value=MagicMock(polarity=0.5)):
                    message_id = str(uuid4())
                    prospect_id = str(uuid4())
                    template_id = str(uuid4())
                    db_session.query.return_value.filter.return_value.first.side_effect = [
                        MessageLog(id=message_id, prospect_id=prospect_id),
                        AffiliateProspect(id=prospect_id, email="test@example.com"),
                        MessageTemplate(id=template_id, content="Follow-up", subject="Follow-up")
                    ]
                    result = handle_prospect_response(message_id, "Looks great!")
                    assert result["success"] is True
                    assert "follow_up_message_id" in result
                    assert db_session.query.return_value.filter.return_value.first().status == ProspectStatus.INTERESTED

def test_handle_negative_response(db_session):
    with patch("database.session.SessionLocal", return_value=db_session):
        with patch("textblob.TextBlob.sentiment", new_callable=MagicMock, return_value=MagicMock(polarity=-0.5)):
            message_id = str(uuid4())
            prospect_id = str(uuid4())
            db_session.query.return_value.filter.return_value.first.side_effect = [
                MessageLog(id=message_id, prospect_id=prospect_id),
                AffiliateProspect(id=prospect_id, email="test@example.com")
            ]
            result = handle_prospect_response(message_id, "Not interested")
            assert result["success"] is True
            assert db_session.query.return_value.filter.return_value.first().status == ProspectStatus.DECLINED