import pytest
from services.validator import DataValidator
from unittest.mock import patch

@pytest.fixture
def validator():
    return DataValidator()

def test_validate_email_success(validator):
    with patch("dns.resolver.resolve", return_value=["mx.example.com"]):
        result = validator.validate_email("test@example.com")
        assert result["is_valid"] is True
        assert result["format_valid"] is True
        assert result["domain_valid"] is True
        assert not result["errors"]

def test_validate_email_invalid_format(validator):
    result = validator.validate_email("invalid-email")
    assert result["is_valid"] is False
    assert result["format_valid"] is False
    assert "Invalid email format" in result["errors"]

def test_validate_website_success(validator):
    with patch("requests.head", return_value=MagicMock(status_code=200)):
        result = validator.validate_website("https://example.com")
        assert result["is_valid"] is True
        assert result["is_reachable"] is True
        assert result["status_code"] == 200

def test_validate_website_invalid(validator):
    result = validator.validate_website("invalid-url")
    assert result["is_valid"] is False
    assert "Invalid URL format" in result["errors"]

def test_validate_social_profile_twitter_success(validator):
    with patch("requests.get", return_value=MagicMock(status_code=200)):
        result = validator.validate_social_profile("twitter", {"username": "testuser"})
        assert result["is_valid"] is True
        assert not result["errors"]

def test_validate_social_profile_unsupported_platform(validator):
    result = validator.validate_social_profile("instagram", {"username": "testuser"})
    assert result["is_valid"] is False
    assert "Unsupported platform" in result["errors"]