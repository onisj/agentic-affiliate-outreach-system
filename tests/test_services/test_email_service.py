from services.email_service import EmailService
from unittest.mock import patch
from unittest.mock import MagicMock

def test_personalize_message_success():
    email_service = EmailService()
    template = "Hi {{first_name}}, welcome to {{company}}!"
    data = {"first_name": "John", "company": "Acme Corp"}
    result = email_service.personalize_message(template, data)
    assert result == "Hi John, welcome to Acme Corp!"

def test_personalize_message_missing_data():
    email_service = EmailService()
    template = "Hi {{first_name}}, welcome!"
    data = {}
    result = email_service.personalize_message(template, data)
    assert result == "Hi there, welcome!"

def test_send_email_success():
    email_service = EmailService()
    with patch("sendgrid.SendGridAPIClient.send", return_value=MagicMock(status_code=202)):
        result = email_service.send_email("test@example.com", "Subject", "Content")
        assert result is True

def test_send_email_failure():
    email_service = EmailService()
    with patch("sendgrid.SendGridAPIClient.send", side_effect=Exception("SendGrid error")):
        result = email_service.send_email("test@example.com", "Subject", "Content")
        assert result is False