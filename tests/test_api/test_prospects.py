from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from database.models import AffiliateProspect
from datetime import datetime, timezone

def test_create_prospect_success(client: TestClient, reset_db):
    with patch("api.routers.prospects.get_db", return_value=iter([reset_db])):
        with patch("services.validator.DataValidator.validate_email", return_value={"is_valid": True, "format_valid": True, "domain_valid": True, "errors": []}):
            with patch("services.validator.DataValidator.validate_website", return_value={"is_valid": True, "is_reachable": True, "status_code": 200, "errors": []}):
                mock_query = MagicMock()
                reset_db.query = mock_query
                mock_query.return_value.filter.return_value.first.return_value = None  # No existing prospect
                prospect_data = {
                    "email": "test@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "company": "Acme Corp",
                    "website": "https://example.com",
                    "lead_source": "linkedin",
                    "consent_given": True
                }
                response = client.post("/prospects/", json=prospect_data)
                assert response.status_code == 200
                assert response.json()["email"] == prospect_data["email"]

def test_get_prospects(client: TestClient, reset_db):
    with patch("api.routers.prospects.get_db", return_value=iter([reset_db])):
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.offset.return_value.limit.return_value.all.return_value = [
            AffiliateProspect(id=str(uuid4()), email="test1@example.com", status="new", created_at=datetime.now(timezone.utc)),
            AffiliateProspect(id=str(uuid4()), email="test2@example.com", status="qualified", created_at=datetime.now(timezone.utc))
        ]
        response = client.get("/prospects/")
        assert response.status_code == 200
        assert len(response.json()) == 2

def test_get_prospect_not_found(client: TestClient, reset_db):
    with patch("api.routers.prospects.get_db", return_value=iter([reset_db])):
        mock_query = MagicMock()
        reset_db.query = mock_query
        mock_query.return_value.filter.return_value.first.return_value = None
        response = client.get(f"/prospects/{str(uuid4())}")
        assert response.status_code == 404