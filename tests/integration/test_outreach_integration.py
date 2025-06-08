"""
Outreach Module Integration Tests

This module contains integration tests for the outreach components.
"""

import pytest
from datetime import datetime, timedelta
from services.outreach.intelligence import (
    ContextEngine,
    ContentGenerator,
    CampaignIntelligence,
    TimingEngine,
    ResponseAnalyzer,
    PersonalizationEngine
)
from services.monitoring import MonitoringService
from database.models import Prospect, MessageTemplate

@pytest.fixture
async def outreach_components():
    """Initialize outreach components for testing."""
    monitoring = MonitoringService()
    user_id = 123
    
    return {
        "context_engine": ContextEngine(user_id),
        "content_generator": ContentGenerator(user_id),
        "campaign_intelligence": CampaignIntelligence(user_id),
        "timing_engine": TimingEngine(user_id),
        "response_analyzer": ResponseAnalyzer(user_id),
        "personalization_engine": PersonalizationEngine(user_id)
    }

@pytest.fixture
def test_prospect():
    """Create a test prospect."""
    return Prospect(
        id=1,
        name="Test Prospect",
        email="test@example.com",
        linkedin_url="https://linkedin.com/in/test",
        company="Test Company",
        title="Software Engineer",
        location="Test Location",
        timezone="UTC",
        channel_preferences=["linkedin", "email"],
        content_preferences=["technical", "industry_news"],
        timing_preferences={
            "preferred_days": ["Monday", "Wednesday", "Friday"],
            "preferred_hours": [9, 10, 11, 14, 15, 16]
        }
    )

@pytest.fixture
def test_template():
    """Create a test message template."""
    return MessageTemplate(
        id=1,
        name="Test Template",
        content="Hello {name}, I noticed you're a {title} at {company}.",
        channel="linkedin",
        type="connection_request",
        variables=["name", "title", "company"]
    )

@pytest.mark.asyncio
async def test_outreach_pipeline(outreach_components, test_prospect, test_template):
    """Test the complete outreach pipeline."""
    try:
        # 1. Get context
        context = await outreach_components["context_engine"].get_context(
            prospect=test_prospect,
            template=test_template
        )
        assert context is not None
        
        # 2. Get optimal timing
        timing = await outreach_components["timing_engine"].get_optimal_timing(
            prospect=test_prospect,
            channel="linkedin",
            message_type="connection_request"
        )
        assert timing is not None
        
        # 3. Generate content
        content = await outreach_components["content_generator"].generate_content(
            context=context,
            template=test_template
        )
        assert content is not None
        
        # 4. Personalize message
        personalized_message = await outreach_components["personalization_engine"].personalize_message(
            prospect=test_prospect,
            template=test_template,
            additional_context=context
        )
        assert personalized_message is not None
        
        # 5. Analyze response
        response_analysis = await outreach_components["response_analyzer"].analyze_responses(
            prospect=test_prospect,
            channel="linkedin"
        )
        assert response_analysis is not None
        
    except Exception as e:
        pytest.fail(f"Outreach pipeline test failed: {str(e)}")

@pytest.mark.asyncio
async def test_campaign_intelligence(outreach_components, test_prospect):
    """Test campaign intelligence capabilities."""
    try:
        # Test campaign analysis
        campaign_analysis = await outreach_components["campaign_intelligence"].analyze_campaign(
            campaign_id=1,
            prospect=test_prospect
        )
        assert campaign_analysis is not None
        
        # Test campaign optimization
        optimization = await outreach_components["campaign_intelligence"].optimize_campaign(
            campaign_id=1,
            analysis=campaign_analysis
        )
        assert optimization is not None
        
    except Exception as e:
        pytest.fail(f"Campaign intelligence test failed: {str(e)}")

@pytest.mark.asyncio
async def test_timing_optimization(outreach_components, test_prospect):
    """Test timing optimization capabilities."""
    try:
        # Test timing analysis
        timing = await outreach_components["timing_engine"].get_optimal_timing(
            prospect=test_prospect,
            channel="linkedin",
            message_type="connection_request"
        )
        assert timing is not None
        assert "optimal_times" in timing
        assert "confidence_score" in timing
        
        # Test timing recommendations
        recommendations = await outreach_components["timing_engine"].get_timing_recommendations(
            prospect=test_prospect,
            channel="linkedin"
        )
        assert recommendations is not None
        
    except Exception as e:
        pytest.fail(f"Timing optimization test failed: {str(e)}")

@pytest.mark.asyncio
async def test_response_analysis(outreach_components, test_prospect):
    """Test response analysis capabilities."""
    try:
        # Test response analysis
        analysis = await outreach_components["response_analyzer"].analyze_responses(
            prospect=test_prospect,
            channel="linkedin"
        )
        assert analysis is not None
        assert "patterns" in analysis
        assert "engagement" in analysis
        assert "sentiment" in analysis
        
        # Test response recommendations
        recommendations = await outreach_components["response_analyzer"].get_recommendations(
            prospect=test_prospect,
            analysis=analysis
        )
        assert recommendations is not None
        
    except Exception as e:
        pytest.fail(f"Response analysis test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization(outreach_components, test_prospect, test_template):
    """Test message personalization capabilities."""
    try:
        # Test personalization factors
        factors = await outreach_components["personalization_engine"].get_personalization_factors(
            prospect=test_prospect,
            template=test_template
        )
        assert factors is not None
        
        # Test message personalization
        personalized_message = await outreach_components["personalization_engine"].personalize_message(
            prospect=test_prospect,
            template=test_template
        )
        assert personalized_message is not None
        assert "message" in personalized_message
        assert "confidence_score" in personalized_message
        
    except Exception as e:
        pytest.fail(f"Personalization test failed: {str(e)}")

@pytest.mark.asyncio
async def test_error_handling(outreach_components, test_prospect, test_template):
    """Test error handling in outreach components."""
    try:
        # Test invalid prospect
        with pytest.raises(Exception):
            await outreach_components["context_engine"].get_context(
                prospect=None,
                template=test_template
            )
            
        # Test invalid template
        with pytest.raises(Exception):
            await outreach_components["personalization_engine"].personalize_message(
                prospect=test_prospect,
                template=None
            )
            
        # Test invalid channel
        with pytest.raises(Exception):
            await outreach_components["timing_engine"].get_optimal_timing(
                prospect=test_prospect,
                channel="invalid",
                message_type="connection_request"
            )
            
    except Exception as e:
        pytest.fail(f"Error handling test failed: {str(e)}") 