# tests/test_tasks/test_outreach_tasks.py
from unittest.mock import patch, MagicMock
from app.tasks.outreach_tasks import send_outreach_message
from database.models import AffiliateProspect, MessageTemplate, MessageType, MessageLog, MessageStatus, OutreachCampaign, CampaignStatus, ProspectStatus
from uuid import uuid4
from uuid import UUID
from datetime import datetime
import pytz
import pytest
from tests.utils import (
    db_session, redis_client, mock_services,
    create_test_prospect, create_test_template, create_test_campaign,
    TestData, with_db_rollback, with_redis_cache
)

def test_send_outreach_message_email_success(reset_db):
    """Test successful email outreach with logging."""
    prospect_id = str(uuid4())
    template_id = str(uuid4())
    prospect = AffiliateProspect(
        id=prospect_id,
        email="test@example.com",
        first_name="John",
        consent_given=True,
        status=ProspectStatus.NEW.value,
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
        
        result = send_outreach_message(prospect_id, template_id, MessageType.EMAIL.value)
        
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
        status=ProspectStatus.NEW.value,
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
                result = send_outreach_message(prospect_id, template_id, MessageType.EMAIL.value)
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
        status=ProspectStatus.NEW.value,
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
        result = send_outreach_message(prospect_id, template_id, MessageType.TWITTER.value)
        assert result["success"] is False
        assert "Twitter user ID not found" in result["error"]

@pytest.mark.celery
class TestOutreachTasks:
    """Tests for outreach Celery tasks."""

    @with_db_rollback
    def test_send_outreach_email(self, db_session, mock_services):
        """Test sending an outreach email task."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        campaign = create_test_campaign(db_session)
        campaign.prospects.append(prospect)
        campaign.templates.append(template)
        db_session.commit()

        # Act
        from app.tasks.outreach_tasks import send_outreach_message
        result = send_outreach_message.delay(prospect.id, template.id, campaign.id)

        # Assert
        assert result.status == "SUCCESS"
        assert result.get() is True

    @with_db_rollback
    def test_schedule_campaign_emails(self, db_session, mock_services):
        """Test scheduling campaign emails task."""
        # Arrange
        campaign = create_test_campaign(db_session)
        template = create_test_template(db_session)
        prospect1 = create_test_prospect(db_session)
        prospect2 = create_test_prospect(db_session, {
            **TestData.PROSPECT,
            "email": "test2@example.com"
        })
        campaign.prospects.extend([prospect1, prospect2])
        campaign.templates.append(template)
        db_session.commit()

        # Act
        from app.tasks.outreach_tasks import schedule_campaign_emails
        result = schedule_campaign_emails.delay(campaign.id)

        # Assert
        assert result.status == "SUCCESS"
        assert result.get() == 2  # Number of emails scheduled

    @with_db_rollback
    def test_process_campaign_queue(self, db_session, mock_services):
        """Test processing campaign queue task."""
        # Arrange
        campaign = create_test_campaign(db_session)
        template = create_test_template(db_session)
        prospect = create_test_prospect(db_session)
        campaign.prospects.append(prospect)
        campaign.templates.append(template)
        db_session.commit()

        # Act
        from app.tasks.outreach_tasks import process_campaign_queue
        result = process_campaign_queue.delay(campaign.id)

        # Assert
        assert result.status == "SUCCESS"
        assert result.get() is True

    @with_db_rollback
    def test_retry_failed_emails(self, db_session, mock_services):
        """Test retrying failed emails task."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        campaign = create_test_campaign(db_session)
        campaign.prospects.append(prospect)
        campaign.templates.append(template)
        db_session.commit()

        # Mock a failed email
        redis_client.hset(
            f"failed_email:{prospect.id}:{template.id}",
            mapping={
                "attempts": "1",
                "last_error": "Connection timeout"
            }
        )

        # Act
        from app.tasks.outreach_tasks import retry_failed_emails
        result = retry_failed_emails.delay()

        # Assert
        assert result.status == "SUCCESS"
        assert result.get() == 1  # Number of emails retried

    @pytest.mark.integration
    def test_campaign_workflow_tasks(self, db_session, mock_services):
        """Test the complete campaign workflow tasks."""
        # Arrange
        campaign = create_test_campaign(db_session)
        template = create_test_template(db_session)
        prospect = create_test_prospect(db_session)
        campaign.prospects.append(prospect)
        campaign.templates.append(template)
        db_session.commit()

        # Act - Schedule campaign emails
        from app.tasks.outreach_tasks import schedule_campaign_emails, process_campaign_queue
        schedule_result = schedule_campaign_emails.delay(campaign.id)
        assert schedule_result.status == "SUCCESS"
        assert schedule_result.get() == 1

        # Act - Process campaign queue
        process_result = process_campaign_queue.delay(campaign.id)
        assert process_result.status == "SUCCESS"
        assert process_result.get() is True

        # Assert - Check Redis for campaign status
        campaign_status = redis_client.get(f"campaign_status:{campaign.id}")
        assert campaign_status == b"completed"

    @with_db_rollback
    def test_task_error_handling(self, db_session, mock_services):
        """Test error handling in outreach tasks."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        campaign = create_test_campaign(db_session)
        campaign.prospects.append(prospect)
        campaign.templates.append(template)
        db_session.commit()

        # Mock email service to raise an exception
        with patch("services.email.send_email", side_effect=Exception("Email service error")):
            # Act
            from app.tasks.outreach_tasks import send_outreach_email
            result = send_outreach_email.delay(prospect.id, template.id, campaign.id)

            # Assert
            assert result.status == "FAILURE"
            assert "Email service error" in str(result.get())