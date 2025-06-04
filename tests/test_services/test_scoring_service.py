from services.scoring_service import LeadScoringService
from unittest.mock import patch

def test_calculate_score_full_data():
    scoring_service = LeadScoringService()
    prospect_data = {
        "email": "john@acmecorp.com",
        "website": "https://acmecorp.com",
        "social_profiles": {"twitter": {"followers": 2000}, "linkedin": {"urn": "123"}},
        "company": "Acme Corp"
    }
    with patch("services.validator.DataValidator.validate_email", return_value={"is_valid": True}):
        with patch("services.validator.DataValidator.validate_website", return_value={"is_valid": True, "is_reachable": True}):
            score = scoring_service.calculate_score(prospect_data)
            assert score == 85  # 20 (email) + 20 (website) + 30 (social) + 30 (company) - 15 (business email)

def test_calculate_score_minimal_data():
    scoring_service = LeadScoringService()
    prospect_data = {"email": "test@gmail.com"}
    with patch("services.validator.DataValidator.validate_email", return_value={"is_valid": True}):
        score = scoring_service.calculate_score(prospect_data)
        assert score == 20

def test_calculate_score_invalid_data():
    scoring_service = LeadScoringService()
    prospect_data = {"email": "invalid"}
    with patch("services.validator.DataValidator.validate_email", return_value={"is_valid": False}):
        score = scoring_service.calculate_score(prospect_data)
        assert score == 0