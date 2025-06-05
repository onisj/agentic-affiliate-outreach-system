# tests/test_tasks/test_outreach_tasks.py
from unittest.mock import patch, MagicMock
from tasks.outreach_tasks import send_outreach_message
from database.models import AffiliateProspect, MessageTemplate, MessageType, MessageLog, MessageStatus
from uuid import uuid4
from datetime import datetime
import pytz

def test_send_outreach_message_email_success(reset_db):
    """Test successful email outreach with logging."""
    prospect_id = str(uuid4())
    template_id = str(uuid4())
    prospect = AffiliateProspect(
        id=prospect_id,
        email="test@example.com",
        first_name="John",
        consent_given=True,
        status="NEW",
        created_at=datetime.now(pytz.UTC),
        updated_at=datetime.now(pytz.UTC)
    )
    template = MessageTemplate(
        id=template_id,
        name="Email Outreach",
        subject="Test Subject",
        content="Hello {{first_name}}, join our program!",
        message_type=MessageType.EMAIL,
        is_active=True,
        created_at=datetime.now(pytz.UTC),
        updated_at=datetime.now(pytz.UTC)
    )
    
    # Mock database queries
    mock_query = MagicMock()
    reset_db.query = mock_query
    mock_query.return_value.filter.return_value.first.side_effect = [prospect, template]
    
    # Mock EmailService
    with patch("services.email_service.EmailService") as mock_email_service:
        mock_email_instance = MagicMock()
        mock_email_service.return_value = mock_email_instance
        mock_email_instance.personalize_message.return_value = "Hello John, join our program!"
        mock_email_instance.send_email.return_value = True
        
        result = send_outreach_message(prospect_id, template_id, "EMAIL")
        
        # Assertions
        assert result["success"] is True
        assert "message_id" in result
        # Verify MessageLog entry
        message_log_query = reset_db.query(MessageLog).filter(
            MessageLog.prospect_id == UUID(prospect_id),
            MessageLog.template_id == UUID(template_id),
            MessageLog.message_type == MessageType.EMAIL,
            MessageLog.status == MessageStatus.SENT
        ).first()
        assert message_log_query is not None
        assert message_log_query.subject == "Test Subject"
        assert message_log_query.content == "Hello John, join our program!"
        assert message_log_query.sent_at is not None

def test_send_outreach_message_no_consent(reset_db):
    """Test outreach failure due to lack of consent."""
    prospect_id = str(uuid4())
    template_id = str(uuid4())
    prospect = AffiliateProspect(
        id=prospect_id,
        email="test@example.com",
        consent_given=False,
        status="NEW",
        created_at=datetime.now(pytz.UTC),
        updated_at=datetime.now(pytz.UTC)
    )
    template = MessageTemplate(
        id=template_id,
        name="Email Outreach",
        content="Hello {{first_name}}",
        message_type=MessageType.EMAIL,
        is_active=True,
        created_at=datetime.now(pytz.UTC),
        updated_at=datetime.now(pytz.UTC)
    )

    # Mock the entire database session
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_session.query = mock_query
    mock_query.return_value.filter.return_value.first.side_effect = [prospect, template]
    mock_session.commit = MagicMock()
    mock_session.add = MagicMock()

    # Mock get_db to return our mock session
    with patch("database.session.get_db", return_value=iter([mock_session])):
        with patch("services.social_service.SocialService", return_value=MagicMock()):
            with patch("services.email_service.EmailService", return_value=MagicMock()):
                result = send_outreach_message(prospect_id, template_id, "EMAIL")
                assert result["success"] is False
                assert "Consent not given" in result["error"]

def test_send_outreach_message_twitter_missing_user_id(reset_db):
    """Test Twitter outreach failure due to missing user ID."""
    prospect_id = str(uuid4())
    template_id = str(uuid4())
    prospect = AffiliateProspect(
        id=prospect_id,
        email="test@example.com",
        consent_given=True,
        social_profiles={},
        status="NEW",
        created_at=datetime.now(pytz.UTC),
        updated_at=datetime.now(pytz.UTC)
    )
    template = MessageTemplate(
        id=template_id,
        name="Twitter Outreach",
        content="Hi",
        message_type=MessageType.TWITTER,
        is_active=True,
        created_at=datetime.now(pytz.UTC),
        updated_at=datetime.now(pytz.UTC)
    )
    mock_query = MagicMock()
    reset_db.query = mock_query
    mock_query.return_value.filter.return_value.first.side_effect = [prospect, template]
    with patch("services.social_service.SocialService", return_value=MagicMock()):
        result = send_outreach_message(prospect_id, template_id, "TWITTER")
        assert result["success"] is False
        assert "Twitter user ID not found" in result["error"]