from tasks.response_handler import handle_prospect_response
from unittest.mock import patch, MagicMock
from uuid import uuid4
from database.models import MessageLog, AffiliateProspect, MessageTemplate
from datetime import datetime, timezone

def test_handle_positive_response(reset_db):
    with patch("database.session.SessionLocal", return_value=reset_db):
        with patch("services.email_service.EmailService.send_email", return_value=True):
            with patch("services.email_service.EmailService.personalize_message", return_value="Follow-up content"):
                with patch("textblob.TextBlob.sentiment", new_callable=MagicMock, return_value=MagicMock(polarity=0.5)):
                    message_id = str(uuid4())
                    prospect_id = str(uuid4())
                    template_id = str(uuid4())
                    reset_db.query.return_value.filter.return_value.first.side_effect = [
                        MessageLog(id=message_id, prospect_id=prospect_id, created_at=datetime.now(timezone.utc)),
                        AffiliateProspect(id=prospect_id, email="test@example.com", created_at=datetime.now(timezone.utc)),
                        MessageTemplate(id=template_id, content="Follow-up", subject="Follow-up", created_at=datetime.now(timezone.utc))
                    ]
                    result = handle_prospect_response(message_id, "Looks great!")
                    assert result["success"] is True

def test_handle_negative_response(reset_db):
    with patch("database.session.SessionLocal", return_value=reset_db):
        with patch("textblob.TextBlob.sentiment", new_callable=MagicMock, return_value=MagicMock(polarity=-0.5)):
            message_id = str(uuid4())
            prospect_id = str(uuid4())
            reset_db.query.return_value.filter.return_value.first.side_effect = [
                MessageLog(id=message_id, prospect_id=prospect_id, created_at=datetime.now(timezone.utc)),
                AffiliateProspect(id=prospect_id, email="test@example.com", created_at=datetime.now(timezone.utc))
            ]
            result = handle_prospect_response(message_id, "Not interested")
            assert result["success"] is True