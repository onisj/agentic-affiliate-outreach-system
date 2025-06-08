"""
Test fixtures for integration tests.

This module provides fixtures for testing the Intelligent Personalization Engine
and related components.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from src.services.outreach.personalization.intelligent_engine import IntelligentPersonalizationEngine
from src.services.monitoring import MonitoringService
from src.database.models import Prospect, MessageTemplate, MessageLog, EngagementMetric

@pytest.fixture
def mock_monitoring_service():
    """Create a mock monitoring service."""
    return MonitoringService()

@pytest.fixture
def personalization_engine(mock_monitoring_service):
    """Create personalization engine instance with mock monitoring."""
    return IntelligentPersonalizationEngine(
        user_id=123,
        monitoring_service=mock_monitoring_service
    )

@pytest.fixture
def test_prospect():
    """Create a test prospect with complete profile data."""
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
def test_prospect_minimal():
    """Create a test prospect with minimal profile data."""
    return Prospect(
        id=2,
        name="Minimal Prospect",
        email="minimal@example.com"
    )

@pytest.fixture
def test_prospect_invalid():
    """Create a test prospect with invalid data."""
    return Prospect(
        id=3,
        name="Invalid Prospect",
        email="invalid@example.com",
        channel_preferences=["invalid_channel"],
        content_preferences=["invalid_content"],
        timing_preferences={
            "preferred_days": ["InvalidDay"],
            "preferred_hours": [25, 26]
        }
    )

@pytest.fixture
def test_template():
    """Create a test message template with variables."""
    return MessageTemplate(
        id=1,
        name="Test Template",
        content="Hello {name}, I noticed you're a {title} at {company}.",
        channel="linkedin",
        type="connection_request",
        variables=["name", "title", "company"]
    )

@pytest.fixture
def test_template_complex():
    """Create a test message template with complex variables."""
    return MessageTemplate(
        id=2,
        name="Complex Template",
        content="""
        Hi {name},
        
        I noticed your impressive work as a {title} at {company}.
        Your recent post about {topic} caught my attention.
        
        Would you be interested in discussing {value_proposition}?
        
        Best regards,
        {sender_name}
        """,
        channel="linkedin",
        type="value_proposition",
        variables=["name", "title", "company", "topic", "value_proposition", "sender_name"]
    )

@pytest.fixture
def test_template_invalid():
    """Create a test message template with invalid variables."""
    return MessageTemplate(
        id=3,
        name="Invalid Template",
        content="Hello {invalid_var}, I noticed you're a {missing_var} at {company}.",
        channel="invalid_channel",
        type="invalid_type",
        variables=["invalid_var", "missing_var", "company"]
    )

@pytest.fixture
def test_message_logs():
    """Create test message logs for interaction history."""
    return [
        MessageLog(
            id=1,
            prospect_id=1,
            template_id=1,
            channel="linkedin",
            status="sent",
            sent_at=datetime.now() - timedelta(days=1),
            content="Test message 1"
        ),
        MessageLog(
            id=2,
            prospect_id=1,
            template_id=1,
            channel="email",
            status="delivered",
            sent_at=datetime.now() - timedelta(hours=12),
            content="Test message 2"
        )
    ]

@pytest.fixture
def test_engagement_metrics():
    """Create test engagement metrics."""
    return [
        EngagementMetric(
            id=1,
            prospect_id=1,
            message_id=1,
            metric_type="open",
            value=1,
            recorded_at=datetime.now() - timedelta(hours=1)
        ),
        EngagementMetric(
            id=2,
            prospect_id=1,
            message_id=1,
            metric_type="click",
            value=1,
            recorded_at=datetime.now() - timedelta(minutes=30)
        )
    ]

@pytest.fixture
def test_platform_context():
    """Create test platform context data."""
    return {
        "channel": "linkedin",
        "template_type": "connection_request",
        "platform_rules": {
            "max_length": 300,
            "allowed_formats": ["text", "rich_text"],
            "required_fields": ["name", "title"]
        },
        "rate_limits": {
            "requests_per_day": 100,
            "requests_per_hour": 10
        }
    }

@pytest.fixture
def test_personalization_rules():
    """Create test personalization rules."""
    return {
        "tone_rules": {
            "professional": 0.8,
            "casual": 0.2
        },
        "content_rules": {
            "technical": 0.7,
            "industry_news": 0.3
        },
        "formatting_rules": {
            "paragraphs": True,
            "bullet_points": False,
            "emojis": False
        }
    }

@pytest.fixture
def test_variation_strategy():
    """Create test variation strategy."""
    return {
        "types": ["tone", "content", "format"],
        "selection_criteria": {
            "engagement_score": 0.7,
            "response_rate": 0.3
        },
        "variation_count": 3
    }

@pytest.fixture
def test_error_cases():
    """Create test error cases for edge case testing."""
    return {
        "invalid_prospect": {
            "id": None,
            "name": "",
            "email": "invalid-email",
            "channel_preferences": ["invalid_channel"],
            "content_preferences": None,
            "timing_preferences": {}
        },
        "invalid_template": {
            "id": None,
            "name": "",
            "content": "Hello {invalid_var}",
            "channel": "invalid_channel",
            "type": None,
            "variables": []
        },
        "invalid_strategy": {
            "tone_rules": {},
            "content_rules": None,
            "formatting_rules": {},
            "variation_strategy": {}
        }
    }
