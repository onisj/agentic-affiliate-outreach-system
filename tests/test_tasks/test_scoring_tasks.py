import pytest
from unittest.mock import patch, MagicMock
from tasks.scoring_tasks import score_prospect
from database.models import AffiliateProspect

@pytest.fixture
def db_session():
    return MagicMock()

def test_score_prospect_success(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        with patch("services.scoring_service.LeadScoringService.calculate_score", return_value=85):
            prospect_id = str(uuid4())
            db_session.query.return_value.filter.return_value.first.return_value = AffiliateProspect(
                id=prospect_id, email="test@example.com"
            )
            result = score_prospect(prospect_id)
            assert result["success"] is True
            assert result["score"] == 85
            assert db_session.query.return_value.filter.return_value.first().status == "qualified"

def test_score_prospect_not_found(db_session):
    with patch("database.session.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.first.return_value = None
        result = score_prospect(str(uuid4()))
        assert result["success"] is False
        assert "Prospect not found" in result["error"]