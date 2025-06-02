import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from database.models import AffiliateProspect
from api.schemas.prospect import ProspectCreate
from uuid import uuid4

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    return MagicMock()

def test_create_prospect_success(client, db_session):
    with patch("api.routers.prospects.get_db", return_value=iter([db_session])):
        with patch("services.validator.DataValidator.validate_email", return_value={"is_valid": True, "format_valid": True, "domain_valid": True, "errors": []}):
            with patch("services.validator.DataValidator.validate_website", return_value={"is_valid": True, "is_reachable": True, "status_code": 200, "errors": []}):
                db_session.query.return_value.filter.return_value.first.return_value = None
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
                assert response.json()["email"] == "test@example.com"

def test_create_prospect_duplicate_email(client, db_session):
    with patch("api.routers.prospects.get_db", return_value=iter([db_session])):
        with patch("services.validator.DataValidator.validate_email", return_value={"is_valid": True, "format_valid": True, "domain_valid": True, "errors": []}):
            db_session.query.return_value.filter.return_value.first.return_value = AffiliateProspect(id=uuid4(), email="test@example.com")
            response = client.post("/prospects/", json={"email": "test@example.com", "consent_given": True})
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

def test_get_prospects(client, db_session):
    with patch("api.routers.prospects.get_db", return_value=iter([db_session])):
        db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            AffiliateProspect(id=uuid4(), email="test1@example.com", status="new"),
            AffiliateProspect(id=uuid4(), email="test2@example.com", status="qualified")
        ]
        response = client.get("/prospects/")
        assert response.status_code == 200
        assert len(response.json()) == 2

def test_get_prospect_not_found(client, db_session):
    with patch("api.routers.prospects.get_db", return_value=iter([db_session])):
        db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.get(f"/prospects/{uuid4()}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]