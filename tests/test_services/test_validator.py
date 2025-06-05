from services.validator import DataValidator
from unittest.mock import patch, MagicMock

def test_validate_email_success():
    validator = DataValidator()
    result = validator.validate_email("test@example.com")
    assert result["is_valid"] is True

def test_validate_email_invalid_format():
    validator = DataValidator()
    result = validator.validate_email("invalid")
    assert result["is_valid"] is False

def test_validate_website_success():
    validator = DataValidator()
    with patch("requests.head", return_value=MagicMock(status_code=200)):
        result = validator.validate_website("https://example.com")
        assert result["is_valid"] is True

def test_validate_website_invalid():
    validator = DataValidator()
    result = validator.validate_website("invalid-url")
    assert result["is_valid"] is False
    assert "Invalid URL format" in result["errors"]

def test_validate_social_profile_twitter_success():
    validator = DataValidator()
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        result = validator.validate_social_profile("twitter", {"username": "testuser"})
        assert result["is_valid"] is True

def test_validate_social_profile_unsupported_platform():
    validator = DataValidator()
    result = validator.validate_social_profile("instagram", {"username": "testuser"})
    assert result["is_valid"] is False
    assert any("Unsupported platform" in error for error in result["errors"])