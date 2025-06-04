from tasks.scoring_tasks import score_prospect
from unittest.mock import patch, MagicMock
from uuid import uuid4
from database.models import AffiliateProspect
from datetime import datetime, timezone

def test_score_prospect_success(reset_db):
    with patch("database.session.get_db", return_value=iter([reset_db])):
        with patch("services.scoring_service.LeadScoringService.calculate_score", return_value=85):
            prospect_id = str(uuid4())
            mock_query = MagicMock()
            reset_db.query = mock_query
            mock_query.return_value.filter.return_value.first.return_value = AffiliateProspect(
                id=prospect_id, email="test@example.com", created_at=datetime.now(timezone.utc)
            )
            result = score_prospect(prospect_id)
            assert result["success"] is True

def test_score_prospect_not_found(reset_db):
    with patch("database.session.get_db", return_value=iter([reset_db])):
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = None
        result = score_prospect(str(uuid4()))
        assert result["success"] is False