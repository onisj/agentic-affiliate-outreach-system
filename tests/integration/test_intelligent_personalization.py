"""
Integration Tests for Intelligent Personalization Engine

This module tests the sequence of interactions in the Intelligent Personalization Engine.
"""

import pytest
from datetime import datetime, timedelta
from services.outreach.personalization.intelligent_engine import IntelligentPersonalizationEngine
from services.monitoring import MonitoringService
from database.models import Prospect, MessageTemplate, MessageLog, EngagementMetric

@pytest.fixture
async def personalization_engine():
    """Create personalization engine instance."""
    return IntelligentPersonalizationEngine(user_id=123)

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
        content_preferences=["technical", "industry_news"],
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
async def test_personalization_sequence(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test the complete personalization sequence."""
    try:
        # Execute personalization
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template
        )
        
        # Verify profile information
        assert "profile_info" in result
        profile_info = result["profile_info"]
        assert profile_info["id"] == test_prospect.id
        assert profile_info["name"] == test_prospect.name
        assert profile_info["title"] == test_prospect.title
        assert profile_info["company"] == test_prospect.company
        
        # Verify context data
        assert "context_data" in result
        context_data = result["context_data"]
        assert "platform_context" in context_data
        assert "history" in context_data
        assert "preferences" in context_data
        
        # Verify personalization strategy
        assert "strategy" in result
        strategy = result["strategy"]
        assert "tone" in strategy
        assert "topics" in strategy
        assert "personalization_rules" in strategy
        assert "variation_strategy" in strategy
        
        # Verify message variations
        assert "variations" in result
        variations = result["variations"]
        assert len(variations) > 0
        for variation in variations:
            assert "content" in variation
            assert "variables" in variation
            
        # Verify final message
        assert "final_message" in result
        final_message = result["final_message"]
        assert "content" in final_message
        assert "personalization" in final_message
        assert "variation_id" in final_message
        
    except Exception as e:
        pytest.fail(f"Personalization sequence test failed: {str(e)}")

@pytest.mark.asyncio
async def test_profile_information_flow(
    personalization_engine,
    test_prospect
):
    """Test the profile information flow."""
    try:
        # Get profile information
        profile_info = await personalization_engine._get_profile_information(test_prospect)
        
        # Verify basic profile data
        assert profile_info["id"] == test_prospect.id
        assert profile_info["name"] == test_prospect.name
        assert profile_info["title"] == test_prospect.title
        assert profile_info["company"] == test_prospect.company
        
        # Verify preferences
        assert "preferences" in profile_info
        preferences = profile_info["preferences"]
        assert "channels" in preferences
        assert "content" in preferences
        assert "timing" in preferences
        
        # Verify additional profile data
        assert "additional_data" in profile_info
        
    except Exception as e:
        pytest.fail(f"Profile information flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_context_data_flow(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test the context data flow."""
    try:
        # Get context data
        context_data = await personalization_engine._get_context_data(
            prospect=test_prospect,
            template=test_template
        )
        
        # Verify platform context
        assert "platform_context" in context_data
        platform_context = context_data["platform_context"]
        assert "channel" in platform_context
        assert "template_type" in platform_context
        
        # Verify interaction history
        assert "history" in context_data
        history = context_data["history"]
        assert "previous_messages" in history
        assert "responses" in history
        
        # Verify preferences
        assert "preferences" in context_data
        preferences = context_data["preferences"]
        assert "channels" in preferences
        assert "content" in preferences
        assert "timing" in preferences
        
    except Exception as e:
        pytest.fail(f"Context data flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_strategy_generation_flow(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test the strategy generation flow."""
    try:
        # Get profile information and context data
        profile_info = await personalization_engine._get_profile_information(test_prospect)
        context_data = await personalization_engine._get_context_data(
            prospect=test_prospect,
            template=test_template
        )
        
        # Generate strategy
        strategy = await personalization_engine._generate_personalization_strategy(
            profile_info=profile_info,
            context_data=context_data
        )
        
        # Verify strategy components
        assert "tone" in strategy
        assert "topics" in strategy
        assert "personalization_rules" in strategy
        assert "variation_strategy" in strategy
        
        # Verify personalization rules
        rules = strategy["personalization_rules"]
        assert "tone_rules" in rules
        assert "content_rules" in rules
        assert "formatting_rules" in rules
        
        # Verify variation strategy
        variation_strategy = strategy["variation_strategy"]
        assert "types" in variation_strategy
        assert "selection_criteria" in variation_strategy
        
    except Exception as e:
        pytest.fail(f"Strategy generation flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_message_variation_flow(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test the message variation flow."""
    try:
        # Get profile information and context data
        profile_info = await personalization_engine._get_profile_information(test_prospect)
        context_data = await personalization_engine._get_context_data(
            prospect=test_prospect,
            template=test_template
        )
        
        # Generate strategy
        strategy = await personalization_engine._generate_personalization_strategy(
            profile_info=profile_info,
            context_data=context_data
        )
        
        # Generate variations
        variations = await personalization_engine._generate_message_variations(
            template=test_template,
            strategy=strategy
        )
        
        # Verify variations
        assert len(variations) > 0
        for variation in variations:
            assert "content" in variation
            assert "variables" in variation
            assert "personalization" in variation
            assert "variation_type" in variation
            
    except Exception as e:
        pytest.fail(f"Message variation flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_final_message_flow(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test the final message flow."""
    try:
        # Get profile information and context data
        profile_info = await personalization_engine._get_profile_information(test_prospect)
        context_data = await personalization_engine._get_context_data(
            prospect=test_prospect,
            template=test_template
        )
        
        # Generate strategy
        strategy = await personalization_engine._generate_personalization_strategy(
            profile_info=profile_info,
            context_data=context_data
        )
        
        # Generate variations
        variations = await personalization_engine._generate_message_variations(
            template=test_template,
            strategy=strategy
        )
        
        # Create final message
        final_message = await personalization_engine._create_final_message(
            variations=variations,
            strategy=strategy
        )
        
        # Verify final message
        assert "content" in final_message
        assert "personalization" in final_message
        assert "variation_id" in final_message
        assert "strategy_id" in final_message
        
    except Exception as e:
        pytest.fail(f"Final message flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_feedback_loop_flow(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test the feedback loop flow."""
    try:
        # Execute personalization
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template
        )
        
        # Get final message
        final_message = result["final_message"]
        strategy = result["strategy"]
        
        # Update personalization model
        await personalization_engine._update_personalization_model(
            message=final_message,
            strategy=strategy
        )
        
        # Verify feedback loop
        # Note: This would typically involve checking the updated model
        # and verifying that the changes were applied correctly
        
    except Exception as e:
        pytest.fail(f"Feedback loop flow test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_minimal_data(
    personalization_engine,
    test_prospect_minimal,
    test_template
):
    """Test personalization with minimal prospect data."""
    try:
        result = await personalization_engine.personalize_message(
            prospect=test_prospect_minimal,
            template=test_template
        )
        
        # Verify basic personalization
        assert "final_message" in result
        assert "content" in result["final_message"]
        assert test_prospect_minimal.name in result["final_message"]["content"]
        
        # Verify strategy adaptation
        assert "strategy" in result
        strategy = result["strategy"]
        assert "tone_rules" in strategy
        assert "content_rules" in strategy
        
    except Exception as e:
        pytest.fail(f"Minimal data test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_invalid_data(
    personalization_engine,
    test_prospect_invalid,
    test_template_invalid
):
    """Test personalization with invalid data."""
    try:
        result = await personalization_engine.personalize_message(
            prospect=test_prospect_invalid,
            template=test_template_invalid
        )
        
        # Verify error handling
        assert "errors" in result
        assert len(result["errors"]) > 0
        
        # Verify fallback behavior
        assert "final_message" in result
        assert "content" in result["final_message"]
        
    except Exception as e:
        pytest.fail(f"Invalid data test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_complex_template(
    personalization_engine,
    test_prospect,
    test_template_complex
):
    """Test personalization with complex template."""
    try:
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template_complex
        )
        
        # Verify complex variable handling
        final_message = result["final_message"]
        assert "content" in final_message
        content = final_message["content"]
        
        # Check all variables are replaced
        assert "{name}" not in content
        assert "{title}" not in content
        assert "{company}" not in content
        assert "{topic}" not in content
        assert "{value_proposition}" not in content
        assert "{sender_name}" not in content
        
        # Verify formatting
        assert "\n" in content
        assert "Best regards" in content
        
    except Exception as e:
        pytest.fail(f"Complex template test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_engagement_history(
    personalization_engine,
    test_prospect,
    test_template,
    test_message_logs,
    test_engagement_metrics
):
    """Test personalization with engagement history."""
    try:
        # Add engagement history
        test_prospect.message_logs = test_message_logs
        test_prospect.engagement_metrics = test_engagement_metrics
        
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template
        )
        
        # Verify history consideration
        assert "context_data" in result
        context_data = result["context_data"]
        assert "history" in context_data
        assert "previous_messages" in context_data["history"]
        assert "responses" in context_data["history"]
        
        # Verify strategy adaptation
        strategy = result["strategy"]
        assert "history_based_rules" in strategy
        
    except Exception as e:
        pytest.fail(f"Engagement history test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_platform_rules(
    personalization_engine,
    test_prospect,
    test_template,
    test_platform_context
):
    """Test personalization with platform rules."""
    try:
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template,
            platform_context=test_platform_context
        )
        
        # Verify platform compliance
        final_message = result["final_message"]
        assert "content" in final_message
        content = final_message["content"]
        
        # Check length compliance
        assert len(content) <= test_platform_context["platform_rules"]["max_length"]
        
        # Verify required fields
        assert test_prospect.name in content
        assert test_prospect.title in content
        
    except Exception as e:
        pytest.fail(f"Platform rules test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_custom_rules(
    personalization_engine,
    test_prospect,
    test_template,
    test_personalization_rules
):
    """Test personalization with custom rules."""
    try:
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template,
            personalization_rules=test_personalization_rules
        )
        
        # Verify rule application
        strategy = result["strategy"]
        assert strategy["tone_rules"] == test_personalization_rules["tone_rules"]
        assert strategy["content_rules"] == test_personalization_rules["content_rules"]
        assert strategy["formatting_rules"] == test_personalization_rules["formatting_rules"]
        
        # Verify variation generation
        assert "variations" in result
        variations = result["variations"]
        assert len(variations) > 0
        
        # Check variation compliance
        for variation in variations:
            assert "content" in variation
            assert "personalization" in variation
            assert "variation_type" in variation
            
    except Exception as e:
        pytest.fail(f"Custom rules test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_with_variation_strategy(
    personalization_engine,
    test_prospect,
    test_template,
    test_variation_strategy
):
    """Test personalization with variation strategy."""
    try:
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template,
            variation_strategy=test_variation_strategy
        )
        
        # Verify variation generation
        assert "variations" in result
        variations = result["variations"]
        assert len(variations) == test_variation_strategy["variation_count"]
        
        # Check variation types
        variation_types = set(v["variation_type"] for v in variations)
        assert variation_types.issubset(set(test_variation_strategy["types"]))
        
        # Verify selection criteria
        for variation in variations:
            assert "engagement_score" in variation
            assert "response_rate" in variation
            
    except Exception as e:
        pytest.fail(f"Variation strategy test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_error_handling(
    personalization_engine,
    test_error_cases
):
    """Test personalization error handling."""
    try:
        # Test invalid prospect
        result = await personalization_engine.personalize_message(
            prospect=test_error_cases["invalid_prospect"],
            template=test_error_cases["invalid_template"]
        )
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        
        # Test invalid template
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_error_cases["invalid_template"]
        )
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        
        # Test invalid strategy
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template,
            personalization_rules=test_error_cases["invalid_strategy"]
        )
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        
    except Exception as e:
        pytest.fail(f"Error handling test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_performance(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test personalization performance."""
    try:
        start_time = datetime.now()
        
        result = await personalization_engine.personalize_message(
            prospect=test_prospect,
            template=test_template
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Verify performance
        assert duration < 1.0  # Should complete within 1 second
        
        # Verify result structure
        assert "final_message" in result
        assert "strategy" in result
        assert "variations" in result
        
    except Exception as e:
        pytest.fail(f"Performance test failed: {str(e)}")

@pytest.mark.asyncio
async def test_personalization_concurrent_requests(
    personalization_engine,
    test_prospect,
    test_template
):
    """Test personalization with concurrent requests."""
    try:
        import asyncio
        
        # Create multiple concurrent requests
        tasks = [
            personalization_engine.personalize_message(
                prospect=test_prospect,
                template=test_template
            )
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all requests completed
        assert len(results) == 5
        
        # Verify each result
        for result in results:
            assert "final_message" in result
            assert "strategy" in result
            assert "variations" in result
            
    except Exception as e:
        pytest.fail(f"Concurrent requests test failed: {str(e)}") 