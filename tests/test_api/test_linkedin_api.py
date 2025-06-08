import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from api.main import app
from database.models import MessageLog, MessageType, MessageStatus
from services.social_service import SocialService
from tests.utils import mock_linkedin_api, mock_linkedin_message, create_test_prospect, create_test_template

@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)

@pytest.fixture
def social_service() -> SocialService:
    return SocialService()

class TestLinkedInAPI:
    """Test cases for LinkedIn API integration."""

    def test_send_linkedin_message_success(self, test_client: TestClient, db_session: Session):
        """Test successful LinkedIn message sending."""
        # Create test data
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        
        with mock_linkedin_message():
            response = test_client.post(
                f"/social/linkedin/{prospect.id}",
                json={"template_id": str(template.id)}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message_id" in data
            assert "external_message_id" in data
            
            # Verify message log
            message_log = db_session.query(MessageLog).filter_by(prospect_id=prospect.id).first()
            assert message_log is not None
            assert message_log.message_type == MessageType.LINKEDIN.value
            assert message_log.status == MessageStatus.SENT.value

    def test_send_linkedin_message_invalid_urn(self, test_client: TestClient, db_session: Session):
        """Test LinkedIn message sending with invalid URN."""
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        
        # Update prospect with invalid URN
        prospect.linkedin_urn = "invalid-urn"
        db_session.commit()
        
        with mock_linkedin_message():
            response = test_client.post(
                f"/social/linkedin/{prospect.id}",
                json={"template_id": str(template.id)}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "Invalid LinkedIn URN format" in data["error"]

    def test_send_linkedin_message_rate_limit(self, test_client: TestClient, db_session: Session):
        """Test LinkedIn message sending with rate limit error."""
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.HTTPError(
                response=type('Response', (), {'status_code': 429, 'text': 'Rate limit exceeded'})()
            )
            
            response = test_client.post(
                f"/social/linkedin/{prospect.id}",
                json={"template_id": str(template.id)}
            )
            
            assert response.status_code == 429
            data = response.json()
            assert data["success"] is False
            assert "Rate limit exceeded" in data["error"]

    def test_send_linkedin_message_auth_error(self, test_client: TestClient, db_session: Session):
        """Test LinkedIn message sending with authentication error."""
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.HTTPError(
                response=type('Response', (), {'status_code': 401, 'text': 'Invalid access token'})()
            )
            
            response = test_client.post(
                f"/social/linkedin/{prospect.id}",
                json={"template_id": str(template.id)}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert "authentication failed" in data["error"].lower()

    def test_send_linkedin_message_permission_error(self, test_client: TestClient, db_session: Session):
        """Test LinkedIn message sending with permission error."""
        prospect = create_test_prospect(db_session)
        template = create_test_template(db_session)
        
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.HTTPError(
                response=type('Response', (), {'status_code': 403, 'text': 'Insufficient permissions'})()
            )
            
            response = test_client.post(
                f"/social/linkedin/{prospect.id}",
                json={"template_id": str(template.id)}
            )
            
            assert response.status_code == 403
            data = response.json()
            assert data["success"] is False
            assert "permission denied" in data["error"].lower()

    def test_refresh_linkedin_token_success(self, social_service: SocialService):
        """Test successful LinkedIn token refresh."""
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "access_token": "new_token",
                "expires_in": 5184000
            }
            mock_post.return_value.status_code = 200
            
            success = social_service.refresh_linkedin_token()
            assert success is True
            assert social_service.linkedin_access_token == "new_token"

    def test_refresh_linkedin_token_failure(self, social_service: SocialService):
        """Test LinkedIn token refresh failure."""
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            success = social_service.refresh_linkedin_token()
            assert success is False

    def test_linkedin_message_template_rendering(self, social_service: SocialService, db_session: Session):
        """Test LinkedIn message template rendering."""
        template = "Hi {{first_name}}, I noticed you work at {{company}}."
        prospect_data = {
            "first_name": "John",
            "company": "Tech Corp"
        }
        
        result = social_service.send_linkedin_message(
            prospect_id=str(uuid.uuid4()),
            urn="urn:li:person:123",
            template=template,
            prospect_data=prospect_data,
            db=db_session
        )
        
        assert result["success"] is False  # Should fail due to missing credentials
        assert "credentials not configured" in result["error"]

    def test_linkedin_message_length_limit(self, social_service: SocialService, db_session: Session):
        """Test LinkedIn message length limit."""
        # Create a template that exceeds LinkedIn's 1000 character limit
        long_template = "Hi {{first_name}}! " * 100  # Will be much longer than 1000 chars
        prospect_data = {
            "first_name": "John",
            "company": "Tech Corp"
        }
        
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"id": "msg_123"}
            mock_post.return_value.status_code = 201
            
            result = social_service.send_linkedin_message(
                prospect_id=str(uuid.uuid4()),
                urn="urn:li:person:123",
                template=long_template,
                prospect_data=prospect_data,
                db=db_session
            )
            
            # Verify that the message was truncated
            assert len(result.get("content", "")) <= 1000

    def test_linkedin_message_logging(self, social_service: SocialService, db_session: Session):
        """Test LinkedIn message logging."""
        prospect_id = str(uuid.uuid4())
        template = "Test message"
        
        with patch('services.social_service.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"id": "msg_123"}
            mock_post.return_value.status_code = 201
            
            result = social_service.send_linkedin_message(
                prospect_id=prospect_id,
                urn="urn:li:person:123",
                template=template,
                prospect_data={},
                db=db_session
            )
            
            # Verify message log
            message_log = db_session.query(MessageLog).filter_by(prospect_id=prospect_id).first()
            assert message_log is not None
            assert message_log.message_type == MessageType.LINKEDIN.value
            assert message_log.status == MessageStatus.SENT.value
            assert message_log.external_message_id == "msg_123" 