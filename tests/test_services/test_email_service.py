from app.services.email_service import EmailService
from unittest.mock import patch
import pytest
from tests.utils import (
    db_session, redis_client, mock_services,
    create_test_prospect, create_test_template,
    TestData, with_db_rollback, with_redis_cache
)
from database.models import MessageStatus
from config.settings import settings

@pytest.mark.email
class TestEmailService:
    """Tests for the email service."""

    @with_db_rollback
    def test_personalize_message_success(self, mock_services):
        """Test successful message personalization."""
        email_service = EmailService()
        template = "Hi {{first_name}}, welcome to {{company}}!"
        data = {"first_name": "John", "company": "Acme Corp"}
        result = email_service.personalize_message(template, data)
        assert result == "Hi John, welcome to Acme Corp!"

    @with_db_rollback
    def test_personalize_message_missing_data(self, mock_services):
        """Test message personalization with missing data."""
        email_service = EmailService()
        template = "Hi {{first_name}}, welcome!"
        data = {}
        result = email_service.personalize_message(template, data)
        assert result == "Hi there, welcome!"

    @with_db_rollback
    def test_send_email_success(self, db_session, mock_services):
        """Test successful email sending."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        email_service = EmailService()

        # Act
        result = email_service.send_email(
            to_email=prospect.email,
            subject=template.subject,
            template_name=template.name,
            context={"first_name": prospect.first_name},
            prospect_id=str(prospect.id),
            db=db_session,
            track=True
        )

        # Assert
        assert result["success"] is True
        assert "message_id" in result
        assert "tracking_id" in result

    @with_db_rollback
    def test_send_email_failure(self, db_session, mock_services):
        """Test email sending failure."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        email_service = EmailService()

        # Act - Simulate SendGrid error
        with patch("sendgrid.SendGridAPIClient.send", side_effect=Exception("SendGrid error")):
            result = email_service.send_email(
                to_email=prospect.email,
                subject=template.subject,
                template_name=template.name,
                context={"first_name": prospect.first_name},
                prospect_id=str(prospect.id),
                db=db_session
            )

        # Assert
        assert result["success"] is False
        assert "error" in result

    @with_db_rollback
    def test_send_email_invalid_address(self, db_session, mock_services):
        """Test email sending with invalid address."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        email_service = EmailService()

        # Act
        result = email_service.send_email(
            to_email="invalid-email",
            subject=template.subject,
            template_name=template.name,
            context={"first_name": prospect.first_name},
            prospect_id=str(prospect.id),
            db=db_session
        )

        # Assert
        assert result["success"] is False
        assert "Invalid email address" in result["error"]

    @with_db_rollback
    def test_send_email_rate_limited(self, db_session, mock_services):
        """Test email sending with rate limiting."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        email_service = EmailService()

        # Set rate limit
        redis_client.set(f"email_rate:{prospect.email}", settings.RATE_LIMIT_PER_MINUTE)
        redis_client.expire(f"email_rate:{prospect.email}", 60)

        # Act
        result = email_service.send_email(
            to_email=prospect.email,
            subject=template.subject,
            template_name=template.name,
            context={"first_name": prospect.first_name},
            prospect_id=str(prospect.id),
            db=db_session
        )

        # Assert
        assert result["success"] is False
        assert "Rate limit exceeded" in result["error"]

    @with_db_rollback
    def test_send_bulk_emails(self, db_session, mock_services):
        """Test sending bulk emails."""
        # Arrange
        prospects = [
            create_test_prospect(db_session, {
                **TestData.PROSPECT,
                "email": f"test{i}@example.com"
            })
            for i in range(3)
        ]
        template = create_test_template(db_session)
        email_service = EmailService()

        # Act
        results = email_service.send_bulk_emails(
            emails=[
                {
                    "to_email": p.email,
                    "context": {"first_name": p.first_name},
                    "prospect_id": str(p.id)
                }
                for p in prospects
            ],
            template_name=template.name,
            subject=template.subject,
            track=True
        )

        # Assert
        assert results["total"] == 3
        assert results["successful"] == 3
        assert results["failed"] == 0
        assert len(results["errors"]) == 0

    @with_db_rollback
    def test_email_tracking(self, db_session, mock_services):
        """Test email tracking functionality."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        email_service = EmailService()

        # Act - Send email with tracking
        result = email_service.send_email(
            to_email=prospect.email,
            subject=template.subject,
            template_name=template.name,
            context={"first_name": prospect.first_name},
            prospect_id=str(prospect.id),
            db=db_session,
            track=True
        )

        # Act - Track open and click
        email_service.track_email_open(result["tracking_id"])
        email_service.track_email_click(result["tracking_id"], "https://example.com")

        # Assert
        tracking_data = redis_client.hgetall(f"email_tracking:{result['tracking_id']}")
        assert tracking_data[b"status"] == b"delivered"
        assert tracking_data[b"opens"] == b"1"
        assert tracking_data[b"clicks"] == b"1"
        assert b"last_open" in tracking_data
        assert b"last_click" in tracking_data
        assert b"last_click_url" in tracking_data

    @with_db_rollback
    def test_email_retry_mechanism(self, db_session, mock_services):
        """Test email retry mechanism."""
        # Arrange
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        email_service = EmailService()

        # Act - First attempt fails
        with patch("sendgrid.SendGridAPIClient.send", side_effect=Exception("SendGrid error")):
            result = email_service.send_email(
                to_email=prospect.email,
                subject=template.subject,
                template_name=template.name,
                context={"first_name": prospect.first_name},
                prospect_id=str(prospect.id),
                db=db_session,
                retry=True
            )

        # Assert
        assert result["success"] is False
        assert "error" in result

        # Act - Retry succeeds
        result = email_service.send_email(
            to_email=prospect.email,
            subject=template.subject,
            template_name=template.name,
            context={"first_name": prospect.first_name},
            prospect_id=str(prospect.id),
            db=db_session,
            retry=True
        )

        # Assert
        assert result["success"] is True
        assert "message_id" in result 