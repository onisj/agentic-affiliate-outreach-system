import pytest
from unittest.mock import Mock, patch
from services.outreach import OutreachService
from tests.utils import TestData, mock_services, redis_client, db_session

@pytest.mark.unit
class TestOutreachService:
    """Unit tests for the OutreachService."""

    @pytest.fixture
    def outreach_service(self, db_session, redis_client):
        """Create an OutreachService instance for testing."""
        return OutreachService(db_session, redis_client)

    def test_create_prospect(self, outreach_service, db_session):
        """Test creating a new prospect."""
        # Arrange
        prospect_data = TestData.PROSPECT

        # Act
        prospect = outreach_service.create_prospect(prospect_data)

        # Assert
        assert prospect.email == prospect_data['email']
        assert prospect.name == prospect_data['name']
        assert prospect.company == prospect_data['company']

    @pytest.mark.twitter
    def test_fetch_twitter_data(self, outreach_service, mock_services):
        """Test fetching Twitter data for a prospect."""
        # Arrange
        twitter_handle = '@test_user'

        # Act
        twitter_data = outreach_service.fetch_twitter_data(twitter_handle)

        # Assert
        assert twitter_data['id'] == '123'
        assert twitter_data['username'] == 'test_user'

    @pytest.mark.linkedin
    def test_fetch_linkedin_data(self, outreach_service, mock_services):
        """Test fetching LinkedIn data for a prospect."""
        # Arrange
        linkedin_url = 'https://linkedin.com/in/test'

        # Act
        linkedin_data = outreach_service.fetch_linkedin_data(linkedin_url)

        # Assert
        assert linkedin_data['id'] == '456'
        assert linkedin_data['firstName'] == 'Test'

    @pytest.mark.email
    def test_send_outreach_email(self, outreach_service, mock_services):
        """Test sending an outreach email."""
        # Arrange
        prospect = outreach_service.create_prospect(TestData.PROSPECT)
        template = outreach_service.create_template(TestData.TEMPLATE)

        # Act
        result = outreach_service.send_outreach_email(prospect.id, template.id)

        # Assert
        assert result is True

    @pytest.mark.celery
    def test_schedule_outreach_task(self, outreach_service, celery_app):
        """Test scheduling an outreach task."""
        # Arrange
        prospect = outreach_service.create_prospect(TestData.PROSPECT)
        template = outreach_service.create_template(TestData.TEMPLATE)

        # Act
        task = outreach_service.schedule_outreach_task(prospect.id, template.id)

        # Assert
        assert task.status == 'SUCCESS'

    @pytest.mark.redis
    def test_cache_prospect_data(self, outreach_service, redis_client):
        """Test caching prospect data."""
        # Arrange
        prospect = outreach_service.create_prospect(TestData.PROSPECT)
        cache_key = f"prospect:{prospect.id}"

        # Act
        outreach_service.cache_prospect_data(prospect)

        # Assert
        cached_data = redis_client.get(cache_key)
        assert cached_data is not None

    @pytest.mark.integration
    def test_end_to_end_outreach_flow(self, outreach_service, mock_services):
        """Test the complete outreach flow."""
        # Arrange
        prospect = outreach_service.create_prospect(TestData.PROSPECT)
        template = outreach_service.create_template(TestData.TEMPLATE)
        campaign = outreach_service.create_campaign(TestData.CAMPAIGN)

        # Act
        outreach_service.add_prospect_to_campaign(prospect.id, campaign.id)
        task = outreach_service.schedule_outreach_task(prospect.id, template.id)

        # Assert
        assert task.status == 'SUCCESS'
        assert prospect.campaign_id == campaign.id 