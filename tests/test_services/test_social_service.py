import pytest
from unittest.mock import patch
from services.social_service import SocialService
from database.models import MessageLog, MessageType, MessageStatus
from sqlalchemy.orm import Session
import uuid

@pytest.fixture
def db_session(mocker):
    return mocker.MagicMock(spec=Session)

def test_send_twitter_dm_success(db_session):
    social_service = SocialService()
    prospect_id = str(uuid.uuid4())
    user_id = "123456789"
    template = "Hi {{first_name}}, join our affiliate program!"
    prospect_data = {"first_name": "John", "company": "Acme"}
    campaign_id = str(uuid.uuid4())
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        
        result = social_service.send_twitter_dm(prospect_id, user_id, template, 
                                              prospect_data, campaign_id, db_session)
        
        assert result["success"] is True
        assert "message_id" in result
        db_session.add.assert_called()
        db_session.commit.assert_called()

def test_send_twitter_dm_failure(db_session):
    social_service = SocialService()
    prospect_id = str(uuid.uuid4())
    user_id = "123456789"
    template = "Hi {{first_name}}, join our affiliate program!"
    prospect_data = {"first_name": "John", "company": "Acme"}
    
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("API error")
        
        result = social_service.send_twitter_dm(prospect_id, user_id, template, 
                                              prospect_data, None, db_session)
        
        assert result["success"] is False
        assert "error" in result
        db_session.rollback.assert_called()