"""
Integration Tests for Advanced Outreach Features

This module tests the integration of Conversation Flow Manager, Timing Optimizer,
and Message Quality Assurance components.
"""

import pytest
from datetime import datetime, timedelta
import pytz
from services.outreach.conversation.flow_manager import ConversationFlowManager, ConversationState
from services.outreach.timing.timing_optimizer import TimingOptimizer
from services.outreach.quality.message_qa import MessageQualityAssurance
from services.monitoring import MonitoringService
from services.analytics import AnalyticsService
from services.outreach.personalization import IntelligentPersonalizationEngine

@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    monitoring_service = MonitoringService()
    analytics_service = AnalyticsService()
    personalization_engine = IntelligentPersonalizationEngine(
        user_id=123,
        monitoring_service=monitoring_service
    )
    return {
        "monitoring": monitoring_service,
        "analytics": analytics_service,
        "personalization": personalization_engine
    }

@pytest.fixture
def flow_manager(mock_services):
    """Create Conversation Flow Manager instance."""
    return ConversationFlowManager(
        monitoring_service=mock_services["monitoring"],
        personalization_engine=mock_services["personalization"],
        timing_optimizer=TimingOptimizer(
            monitoring_service=mock_services["monitoring"],
            analytics_service=mock_services["analytics"]
        )
    )

@pytest.fixture
def timing_optimizer(mock_services):
    """Create Timing Optimizer instance."""
    return TimingOptimizer(
        monitoring_service=mock_services["monitoring"],
        analytics_service=mock_services["analytics"]
    )

@pytest.fixture
def message_qa(mock_services):
    """Create Message Quality Assurance instance."""
    return MessageQualityAssurance(
        monitoring_service=mock_services["monitoring"],
        analytics_service=mock_services["analytics"]
    )

@pytest.mark.asyncio
async def test_conversation_flow_integration(
    flow_manager,
    mock_services
):
    """Test the complete conversation flow integration."""
    try:
        # Start conversation
        conversation = await flow_manager.start_conversation(
            prospect_id="test_prospect",
            initial_message="Hello, I'm interested in connecting.",
            channel="linkedin"
        )
        
        # Verify initial state
        assert conversation["state"] == ConversationState.INITIAL_OUTREACH
        assert len(conversation["messages"]) == 1
        
        # Simulate no response after 3 days
        conversation["last_updated"] = datetime.now() - timedelta(days=3)
        updated_conversations = await flow_manager.check_conversation_timeouts()
        
        # Verify follow-up
        assert len(updated_conversations) > 0
        updated = updated_conversations[0]
        assert updated["state"] == ConversationState.FOLLOW_UP_1
        assert len(updated["messages"]) == 2
        
        # Simulate positive response
        await flow_manager.update_conversation_state(
            conversation["id"],
            ConversationState.POSITIVE_RESPONSE,
            response_data={
                "content": "Yes, I'd be interested in connecting.",
                "sentiment": "positive",
                "intent": "accept"
            }
        )
        
        # Verify nurturing sequence
        conversation = await flow_manager.get_conversation_status(conversation["id"])
        assert conversation["state"] == ConversationState.NURTURING_SEQUENCE
        
    except Exception as e:
        pytest.fail(f"Conversation flow integration test failed: {str(e)}")

@pytest.mark.asyncio
async def test_timing_optimization_integration(
    timing_optimizer,
    mock_services
):
    """Test the timing optimization integration."""
    try:
        # Test optimal time calculation
        optimal_time = await timing_optimizer.get_optimal_send_time(
            prospect_id="test_prospect",
            channel="linkedin",
            timezone="America/New_York"
        )
        
        # Verify time is in correct timezone
        assert optimal_time.tzinfo == pytz.timezone("America/New_York")
        
        # Verify time is within optimal hours
        assert optimal_time.hour in [9, 10, 11, 14, 15, 16]
        
        # Test preference learning
        await timing_optimizer.update_preferences(
            prospect_id="test_prospect",
            engagement_data={
                "best_days": ["Monday", "Wednesday"],
                "best_hours": [10, 11],
                "response_times": [30, 45]  # minutes
            }
        )
        
        # Verify updated preferences
        new_optimal_time = await timing_optimizer.get_optimal_send_time(
            prospect_id="test_prospect",
            channel="linkedin"
        )
        assert new_optimal_time.hour in [10, 11]
        
    except Exception as e:
        pytest.fail(f"Timing optimization integration test failed: {str(e)}")

@pytest.mark.asyncio
async def test_message_quality_integration(
    message_qa,
    mock_services
):
    """Test the message quality assurance integration."""
    try:
        # Test message quality check
        message = """
        Hi there!
        
        I noticed your impressive work at Company XYZ. Would you be interested
        in discussing potential collaboration opportunities?
        
        Best regards,
        John
        """
        
        quality_report = await message_qa.check_message_quality(
            message=message,
            channel="linkedin",
            brand_voice={
                "tone": "professional",
                "formality": "high",
                "personality": "friendly"
            }
        )
        
        # Verify quality checks
        assert "grammar" in quality_report
        assert "tone" in quality_report
        assert "cultural_sensitivity" in quality_report
        assert "spam_check" in quality_report
        
        # Test message optimization
        optimized_message = await message_qa.optimize_message(
            message=message,
            quality_report=quality_report
        )
        
        # Verify optimization
        assert len(optimized_message) > 0
        assert "Hi there!" in optimized_message
        
    except Exception as e:
        pytest.fail(f"Message quality integration test failed: {str(e)}")

@pytest.mark.asyncio
async def test_edge_cases_conversation_flow(
    flow_manager,
    mock_services
):
    """Test conversation flow edge cases."""
    try:
        # Test invalid conversation ID
        with pytest.raises(ValueError):
            await flow_manager.get_conversation_status("invalid_id")
        
        # Test multiple rapid state changes
        conversation = await flow_manager.start_conversation(
            prospect_id="test_prospect",
            initial_message="Test message",
            channel="linkedin"
        )
        
        states = [
            ConversationState.POSITIVE_RESPONSE,
            ConversationState.NEGATIVE_RESPONSE,
            ConversationState.NEUTRAL_RESPONSE
        ]
        
        for state in states:
            await flow_manager.update_conversation_state(
                conversation["id"],
                state
            )
        
        # Test cleanup
        await flow_manager.cleanup()
        
    except Exception as e:
        pytest.fail(f"Conversation flow edge cases test failed: {str(e)}")

@pytest.mark.asyncio
async def test_edge_cases_timing_optimizer(
    timing_optimizer,
    mock_services
):
    """Test timing optimizer edge cases."""
    try:
        # Test invalid timezone
        with pytest.raises(pytz.exceptions.UnknownTimeZoneError):
            await timing_optimizer.get_optimal_send_time(
                prospect_id="test_prospect",
                channel="linkedin",
                timezone="Invalid/Timezone"
            )
        
        # Test invalid channel
        with pytest.raises(ValueError):
            await timing_optimizer.get_platform_optimal_times("invalid_channel")
        
        # Test empty preferences
        await timing_optimizer.update_preferences(
            prospect_id="test_prospect",
            engagement_data={}
        )
        
    except Exception as e:
        pytest.fail(f"Timing optimizer edge cases test failed: {str(e)}")

@pytest.mark.asyncio
async def test_edge_cases_message_quality(
    message_qa,
    mock_services
):
    """Test message quality assurance edge cases."""
    try:
        # Test empty message
        quality_report = await message_qa.check_message_quality(
            message="",
            channel="linkedin"
        )
        assert quality_report["overall_score"] == 0.0
        
        # Test very long message
        long_message = "Test " * 1000
        quality_report = await message_qa.check_message_quality(
            message=long_message,
            channel="linkedin"
        )
        assert "spam_check" in quality_report
        
        # Test message with special characters
        special_message = "Hello! @#$%^&*()_+"
        quality_report = await message_qa.check_message_quality(
            message=special_message,
            channel="linkedin"
        )
        assert "cultural_sensitivity" in quality_report
        
    except Exception as e:
        pytest.fail(f"Message quality edge cases test failed: {str(e)}")

@pytest.mark.asyncio
async def test_integration_scenarios(
    flow_manager,
    timing_optimizer,
    message_qa,
    mock_services
):
    """Test complex integration scenarios."""
    try:
        # Scenario 1: Complete conversation flow with timing and quality
        conversation = await flow_manager.start_conversation(
            prospect_id="test_prospect",
            initial_message="Hello, I'm interested in connecting.",
            channel="linkedin"
        )
        
        # Check message quality
        quality_report = await message_qa.check_message_quality(
            message=conversation["messages"][0]["content"],
            channel="linkedin"
        )
        
        # Get optimal time for follow-up
        optimal_time = await timing_optimizer.get_optimal_send_time(
            prospect_id="test_prospect",
            channel="linkedin"
        )
        
        # Update conversation with quality-checked message at optimal time
        await flow_manager.update_conversation_state(
            conversation["id"],
            ConversationState.FOLLOW_UP_1,
            response_data={
                "content": await message_qa.optimize_message(
                    message="Follow-up message",
                    quality_report=quality_report
                ),
                "sent_at": optimal_time
            }
        )
        
        # Verify final state
        conversation = await flow_manager.get_conversation_status(conversation["id"])
        assert conversation["state"] == ConversationState.FOLLOW_UP_1
        
    except Exception as e:
        pytest.fail(f"Integration scenarios test failed: {str(e)}") 