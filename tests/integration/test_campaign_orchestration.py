"""
Integration Tests for Campaign Orchestration

This module tests the relationships and interactions between components
in the Multi-Channel Campaign Architecture.
"""

import pytest
from datetime import datetime, timedelta
from services.outreach.orchestration.campaign_orchestrator import CampaignOrchestrator
from services.monitoring import MonitoringService
from database.models import (
    Campaign,
    Prospect,
    MessageTemplate,
    MessageLog,
    EngagementMetric,
    ConversionMetric
)

@pytest.fixture
async def campaign_orchestrator():
    """Create campaign orchestrator instance."""
    return CampaignOrchestrator(user_id=123)

@pytest.fixture
def test_campaign():
    """Create test campaign."""
    return Campaign(
        id=1,
        name="Test Campaign",
        description="Test campaign for integration testing",
        target_audience={
            "industries": ["technology"],
            "titles": ["engineer", "developer"],
            "locations": ["San Francisco"]
        },
        status="active",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30)
    )

@pytest.fixture
def test_prospect():
    """Create test prospect."""
    return Prospect(
        id=1,
        name="Test Prospect",
        email="test@example.com",
        linkedin_url="https://linkedin.com/in/test",
        company="Test Company",
        title="Software Engineer",
        location="San Francisco",
        timezone="America/Los_Angeles",
        channel_preferences=["linkedin", "email"],
        content_preferences=["technical"],
        timing_preferences={
            "preferred_days": ["Monday", "Wednesday"],
            "preferred_hours": [10, 11, 15]
        }
    )

@pytest.fixture
def test_template():
    """Create test message template."""
    return MessageTemplate(
        id=1,
        name="Test Template",
        content="Hello {name}, I noticed you're a {title} at {company}.",
        channel="linkedin",
        type="connection_request",
        variables=["name", "title", "company"]
    )

@pytest.mark.asyncio
async def test_campaign_intelligence_flow(
    campaign_orchestrator,
    test_campaign,
    test_prospect,
    test_template
):
    """Test the Campaign Intelligence flow: Strategy -> Personalization -> TemplateEngine."""
    try:
        # Execute campaign
        result = await campaign_orchestrator.execute_campaign(
            campaign=test_campaign,
            prospect=test_prospect,
            template=test_template
        )
        
        # Verify strategy generation
        assert "strategy" in result
        assert "personalization" in result
        assert result["strategy"] is not None
        assert result["personalization"] is not None
        
        # Verify strategy -> personalization relationship
        assert result["personalization"]["strategy_id"] == result["strategy"]["id"]
        
        # Verify timing and channel selection
        assert "timing" in result
        assert "channel" in result
        assert result["timing"] is not None
        assert result["channel"] in test_prospect.channel_preferences
        
    except Exception as e:
        pytest.fail(f"Campaign Intelligence flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_message_generation_flow(
    campaign_orchestrator,
    test_campaign,
    test_prospect,
    test_template
):
    """Test the Message Generation flow: TemplateEngine -> ContentAI -> Localizer -> ABTester."""
    try:
        # Execute campaign
        result = await campaign_orchestrator.execute_campaign(
            campaign=test_campaign,
            prospect=test_prospect,
            template=test_template
        )
        
        # Verify message generation
        assert "message" in result
        message = result["message"]
        
        # Verify template content
        assert "content" in message
        assert "variables" in message
        assert all(var in message["content"] for var in test_template.variables)
        
        # Verify content generation
        assert "personalized_content" in message
        assert message["personalized_content"] is not None
        
        # Verify localization
        assert "localized_content" in message
        assert message["localized_content"] is not None
        
        # Verify A/B testing
        assert "test_variation" in message
        assert message["test_variation"] is not None
        
    except Exception as e:
        pytest.fail(f"Message Generation flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_delivery_channel_flow(
    campaign_orchestrator,
    test_campaign,
    test_prospect,
    test_template
):
    """Test the Delivery Channel flow: ChannelSelect -> Channel Services -> Trackers."""
    try:
        # Execute campaign
        result = await campaign_orchestrator.execute_campaign(
            campaign=test_campaign,
            prospect=test_prospect,
            template=test_template
        )
        
        # Verify delivery
        assert "delivery" in result
        delivery = result["delivery"]
        
        # Verify channel selection
        assert "channel" in result
        assert result["channel"] in test_prospect.channel_preferences
        
        # Verify message delivery
        assert "message_id" in delivery
        assert "status" in delivery
        assert delivery["status"] == "sent"
        
        # Verify tracking
        assert "tracking" in delivery
        tracking = delivery["tracking"]
        
        # Verify appropriate tracker based on channel
        if result["channel"] == "linkedin":
            assert "engagement" in tracking
        elif result["channel"] == "twitter":
            assert "response" in tracking
        elif result["channel"] == "instagram":
            assert "conversion" in tracking
        else:
            assert "delivery" in tracking
            
    except Exception as e:
        pytest.fail(f"Delivery Channel flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_tracking_analytics_flow(
    campaign_orchestrator,
    test_campaign,
    test_prospect,
    test_template
):
    """Test the Tracking & Analytics flow."""
    try:
        # Execute campaign
        result = await campaign_orchestrator.execute_campaign(
            campaign=test_campaign,
            prospect=test_prospect,
            template=test_template
        )
        
        # Get campaign metrics
        metrics = await campaign_orchestrator.get_campaign_metrics(test_campaign)
        
        # Verify metrics structure
        assert "delivery" in metrics
        assert "engagement" in metrics
        assert "response" in metrics
        assert "conversion" in metrics
        
        # Verify delivery metrics
        assert "sent" in metrics["delivery"]
        assert "delivered" in metrics["delivery"]
        assert "failed" in metrics["delivery"]
        
        # Verify engagement metrics
        assert "opens" in metrics["engagement"]
        assert "clicks" in metrics["engagement"]
        assert "reactions" in metrics["engagement"]
        
        # Verify response metrics
        assert "responses" in metrics["response"]
        assert "response_time" in metrics["response"]
        assert "response_rate" in metrics["response"]
        
        # Verify conversion metrics
        assert "conversions" in metrics["conversion"]
        assert "conversion_rate" in metrics["conversion"]
        assert "conversion_time" in metrics["conversion"]
        
    except Exception as e:
        pytest.fail(f"Tracking & Analytics flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_error_handling(
    campaign_orchestrator,
    test_campaign,
    test_prospect,
    test_template
):
    """Test error handling across all components."""
    try:
        # Test invalid channel
        test_prospect.channel_preferences = ["invalid_channel"]
        
        with pytest.raises(ValueError):
            await campaign_orchestrator.execute_campaign(
                campaign=test_campaign,
                prospect=test_prospect,
                template=test_template
            )
            
        # Test invalid template variables
        test_template.variables = ["invalid_variable"]
        
        with pytest.raises(ValueError):
            await campaign_orchestrator.execute_campaign(
                campaign=test_campaign,
                prospect=test_prospect,
                template=test_template
            )
            
        # Test invalid campaign status
        test_campaign.status = "invalid_status"
        
        with pytest.raises(ValueError):
            await campaign_orchestrator.execute_campaign(
                campaign=test_campaign,
                prospect=test_prospect,
                template=test_template
            )
            
    except Exception as e:
        pytest.fail(f"Error handling test failed: {str(e)}") 