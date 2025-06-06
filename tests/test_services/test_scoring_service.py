import pytest
from unittest.mock import patch, MagicMock
from app.services.prospect_scoring import ProspectScoringService
from database.models import AffiliateProspect

@pytest.fixture
def scoring_service():
    return ProspectScoringService()

def test_calculate_score_full_data(scoring_service):
    """Test scoring with complete prospect data."""
    with patch("app.services.validator.DataValidator.validate_email", return_value={"is_valid": True}):
        prospect = AffiliateProspect(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            company="Test Corp",
            social_profiles={"linkedin": "https://linkedin.com/in/johndoe"}
        )
        
        score_data = scoring_service.calculate_prospect_score(prospect, MagicMock())
        
        assert score_data["overall_score"] >= 0
        assert score_data["overall_score"] <= 1
        assert "features" in score_data
        assert "timestamp" in score_data

def test_calculate_score_minimal_data(scoring_service):
    """Test scoring with minimal prospect data."""
    with patch("app.services.validator.DataValidator.validate_email", return_value={"is_valid": True}):
        prospect = AffiliateProspect(
            email="test@example.com"
        )
        
        score_data = scoring_service.calculate_prospect_score(prospect, MagicMock())
        
        assert score_data["overall_score"] >= 0
        assert score_data["overall_score"] <= 1
        assert "features" in score_data
        assert "timestamp" in score_data

def test_calculate_score_invalid_data(scoring_service):
    """Test scoring with invalid prospect data."""
    with patch("app.services.validator.DataValidator.validate_email", return_value={"is_valid": False}):
        prospect = AffiliateProspect(
            email="invalid@example.com"
        )
        
        score_data = scoring_service.calculate_prospect_score(prospect, MagicMock())
        
        assert score_data["overall_score"] >= 0
        assert score_data["overall_score"] <= 1
        assert "features" in score_data
        assert "timestamp" in score_data