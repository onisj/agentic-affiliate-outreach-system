# test_social_service.py
from app.services.social_service import SocialService
from database.session import SessionLocal
from sqlalchemy.orm import Session
import uuid
import pytest
from unittest.mock import patch, MagicMock
from tests.utils import (
    db_session, redis_client, mock_services,
    create_test_prospect, TestData, with_db_rollback, with_redis_cache
)

def test_twitter_dm():
    db: Session = SessionLocal()
    try:
        social_service = SocialService()
        result = social_service.send_twitter_dm(
            prospect_id=str(uuid.uuid4()),
            user_id="12345",  # Replace with a valid Twitter user ID
            template="Hi {{first_name}}, welcome to {{company}}!",
            prospect_data={"first_name": "John", "company": "Acme Corp"},
            campaign_id=str(uuid.uuid4()),
            db=db
        )
        print(result)
    finally:
        db.close()

@pytest.mark.social
class TestSocialService:
    """Tests for the social media integration service."""

    @with_db_rollback
    def test_fetch_twitter_profile(self, db_session, mock_services):
        """Test fetching Twitter profile data."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Act
        profile_data = social_service.fetch_twitter_profile(prospect.twitter_handle)

        # Assert
        assert profile_data is not None
        assert "username" in profile_data
        assert "followers_count" in profile_data
        assert "tweet_count" in profile_data

    @with_db_rollback
    def test_fetch_linkedin_profile(self, db_session, mock_services):
        """Test fetching LinkedIn profile data."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Act
        profile_data = social_service.fetch_linkedin_profile(prospect.linkedin_url)

        # Assert
        assert profile_data is not None
        assert "firstName" in profile_data
        assert "lastName" in profile_data
        assert "headline" in profile_data

    @with_db_rollback
    def test_send_twitter_message(self, db_session, mock_services):
        """Test sending Twitter direct message."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()
        message = "Hello! Would you be interested in our affiliate program?"

        # Act
        result = social_service.send_twitter_message(
            prospect.twitter_handle,
            message
        )

        # Assert
        assert result is True

    @with_db_rollback
    def test_send_linkedin_message(self, db_session, mock_services):
        """Test sending LinkedIn message."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()
        message = "Hello! Would you be interested in our affiliate program?"

        # Act
        result = social_service.send_linkedin_message(
            prospect.linkedin_url,
            message
        )

        # Assert
        assert result is True

    @with_db_rollback
    def test_analyze_social_engagement(self, db_session, mock_services):
        """Test analyzing social media engagement."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Act
        engagement_data = social_service.analyze_social_engagement(prospect)

        # Assert
        assert engagement_data is not None
        assert "twitter_engagement" in engagement_data
        assert "linkedin_engagement" in engagement_data
        assert "overall_score" in engagement_data

    @with_db_rollback
    def test_cache_social_data(self, db_session, redis_client):
        """Test caching social media data."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()
        profile_data = {
            "username": "test_user",
            "followers_count": 1000,
            "tweet_count": 500
        }

        # Act
        social_service.cache_social_data(
            prospect.id,
            "twitter",
            profile_data
        )

        # Assert
        cached_data = redis_client.get(f"social_data:{prospect.id}:twitter")
        assert cached_data is not None

    @with_db_rollback
    def test_rate_limiting(self, db_session, redis_client):
        """Test social media API rate limiting."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Act - Make multiple API calls
        results = []
        for _ in range(5):
            result = social_service.fetch_twitter_profile(prospect.twitter_handle)
            results.append(result)

        # Assert
        assert all(result is not None for result in results)
        assert redis_client.get(f"twitter_rate:{prospect.twitter_handle}") is not None

    @with_db_rollback
    def test_error_handling(self, db_session, mock_services):
        """Test error handling for social media API calls."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Mock API errors
        with patch("services.social_service.SocialService.fetch_twitter_profile") as mock_twitter:
            mock_twitter.side_effect = Exception("Rate limit exceeded")

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                social_service.fetch_twitter_profile(prospect.twitter_handle)
            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.integration
    def test_complete_social_workflow(self, db_session, mock_services):
        """Test complete social media workflow."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Act - Fetch profiles
        twitter_data = social_service.fetch_twitter_profile(prospect.twitter_handle)
        linkedin_data = social_service.fetch_linkedin_profile(prospect.linkedin_url)

        # Act - Analyze engagement
        engagement = social_service.analyze_social_engagement(prospect)

        # Act - Send messages
        twitter_result = social_service.send_twitter_message(
            prospect.twitter_handle,
            "Hello! Would you be interested in our affiliate program?"
        )
        linkedin_result = social_service.send_linkedin_message(
            prospect.linkedin_url,
            "Hello! Would you be interested in our affiliate program?"
        )

        # Assert
        assert twitter_data is not None
        assert linkedin_data is not None
        assert engagement is not None
        assert twitter_result is True
        assert linkedin_result is True

    @with_db_rollback
    def test_social_data_validation(self, db_session):
        """Test validation of social media data."""
        # Arrange
        social_service = SocialService()

        # Act & Assert
        assert social_service.validate_twitter_handle("@valid_handle") is True
        assert social_service.validate_twitter_handle("invalid_handle") is False
        assert social_service.validate_linkedin_url("https://linkedin.com/in/valid") is True
        assert social_service.validate_linkedin_url("https://invalid.com") is False

    @with_db_rollback
    def test_social_data_merging(self, db_session, mock_services):
        """Test merging social media data from multiple platforms."""
        # Arrange
        prospect = create_test_prospect(db_session)
        social_service = SocialService()

        # Act
        twitter_data = social_service.fetch_twitter_profile(prospect.twitter_handle)
        linkedin_data = social_service.fetch_linkedin_profile(prospect.linkedin_url)
        merged_data = social_service.merge_social_data(twitter_data, linkedin_data)

        # Assert
        assert merged_data is not None
        assert "twitter" in merged_data
        assert "linkedin" in merged_data
        assert merged_data["twitter"]["username"] == twitter_data["username"]
        assert merged_data["linkedin"]["firstName"] == linkedin_data["firstName"]

if __name__ == "__main__":
    test_twitter_dm()