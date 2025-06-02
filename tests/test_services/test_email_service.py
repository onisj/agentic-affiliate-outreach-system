import pytest
from unittest.mock import patch, MagicMock
from services.email_service import EmailService

@pytest.fixture
def email_service():
    return EmailService()

def test_personalize_message_success(email_service):
    content = "Hello {{first_name}}, welcome to {{company}}!"
    prospect_data = {
        "first_name": "John",
        "company": "Acme Corp",
        "email": "john@example.com"
    }
    result = email_service.personalize_message(content, prospect_data)
    assert result == "Hello John, welcome to Acme Corp!"

def test_personalize_message_missing_data(email_service):
    content = "Hello {{first_name}}, welcome to {{company}}!"
    prospect_data = {"email": "john@example.com"}
    result = email_service.personalize_message(content, prospect_data)
    assert result == "Hello there, welcome to your company!"

def test_send_email_success(email_service):
    with patch("sendgrid.SendGridAPIClient.send", return_value=MagicMock(status_code=202)):
        success = email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            content="<p>Test Content</p>"
        )
        assert success is True

def test_send_email_failure(email_service):
    with patch("sendgrid.SendGridAPIClient.send", side_effect=Exception("SendGrid error")):
        success = email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            content="<p>Test Content</p>"
        )
        assert success is False