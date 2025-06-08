import os
import pytest
import logging
import subprocess
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from fastapi.testclient import TestClient
from api.main import app
from app.tasks.celery_app import celery_app
from src.database.session import get_db
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from src.services.monitoring import MonitoringService
from src.services.discovery.intelligence import AIAgent
from src.services.discovery.adapters import (
    LinkedInScraper,
    TwitterScraper,
    YouTubeScraper,
    TikTokScraper,
    InstagramScraper,
    RedditScraper,
    GenericWebScraper
)
from src.services.discovery.pipeline import (
    DataCleaner,
    DataValidator,
    DataEnricher,
    ProspectScorer
)
from src.services.discovery.orchestrator import (
    SmartScheduler,
    TaskManager
)
from src.services.outreach.intelligence import (
    ContextEngine,
    TimingEngine,
    ResponseAnalyzer,
    PersonalizationEngine
)
from src.database.models import (
    Prospect,
    MessageTemplate,
    Campaign,
    MessageLog,
    EngagementMetric
)

@pytest.fixture
def monitoring_service():
    """Create a monitoring service instance."""
    return MonitoringService()

@pytest.fixture
def test_config():
    """Create test configuration."""
    return {
        "max_concurrent_tasks": 5,
        "task_timeout": 300,
        "retry_attempts": 3,
        "retry_delay": 5,
        "rate_limits": {
            "linkedin": {"requests_per_minute": 30},
            "twitter": {"requests_per_minute": 50},
            "youtube": {"requests_per_minute": 100},
            "tiktok": {"requests_per_minute": 60},
            "instagram": {"requests_per_minute": 40},
            "reddit": {"requests_per_minute": 30}
        }
    }

@pytest.fixture
def test_prospects():
    """Create a list of test prospects."""
    return [
        Prospect(
            id=1,
            name="John Doe",
            email="john@example.com",
            linkedin_url="https://linkedin.com/in/johndoe",
            company="Tech Corp",
            title="Software Engineer",
            location="San Francisco",
            timezone="America/Los_Angeles",
            channel_preferences=["linkedin", "email"],
            content_preferences=["technical", "industry_news"],
            timing_preferences={
                "preferred_days": ["Monday", "Wednesday", "Friday"],
                "preferred_hours": [9, 10, 11, 14, 15, 16]
            }
        ),
        Prospect(
            id=2,
            name="Jane Smith",
            email="jane@example.com",
            linkedin_url="https://linkedin.com/in/janesmith",
            company="Data Inc",
            title="Data Scientist",
            location="New York",
            timezone="America/New_York",
            channel_preferences=["linkedin", "twitter"],
            content_preferences=["data_science", "ai"],
            timing_preferences={
                "preferred_days": ["Tuesday", "Thursday"],
                "preferred_hours": [10, 11, 12, 15, 16, 17]
            }
        )
    ]

@pytest.fixture
def test_templates():
    """Create a list of test message templates."""
    return [
        MessageTemplate(
            id=1,
            name="Connection Request",
            content="Hello {name}, I noticed you're a {title} at {company}.",
            channel="linkedin",
            type="connection_request",
            variables=["name", "title", "company"]
        ),
        MessageTemplate(
            id=2,
            name="Follow-up Message",
            content="Hi {name}, I'd love to discuss {topic} with you.",
            channel="linkedin",
            type="follow_up",
            variables=["name", "topic"]
        )
    ]

@pytest.fixture
def test_campaigns():
    """Create a list of test campaigns."""
    return [
        Campaign(
            id=1,
            name="Tech Outreach",
            description="Outreach to tech professionals",
            target_audience={
                "industries": ["technology", "software"],
                "titles": ["engineer", "developer", "architect"],
                "locations": ["San Francisco", "New York"]
            },
            status="active",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        ),
        Campaign(
            id=2,
            name="Data Science Outreach",
            description="Outreach to data scientists",
            target_audience={
                "industries": ["data", "ai", "machine_learning"],
                "titles": ["data_scientist", "ml_engineer"],
                "locations": ["San Francisco", "New York", "Boston"]
            },
            status="active",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
    ]

@pytest.fixture
def test_message_logs():
    """Create a list of test message logs."""
    return [
        MessageLog(
            id=1,
            prospect_id=1,
            campaign_id=1,
            template_id=1,
            channel="linkedin",
            message_type="connection_request",
            status="sent",
            sent_at=datetime.now() - timedelta(days=1),
            response_received_at=datetime.now() - timedelta(hours=12),
            response_type="accepted"
        ),
        MessageLog(
            id=2,
            prospect_id=2,
            campaign_id=2,
            template_id=2,
            channel="linkedin",
            message_type="follow_up",
            status="sent",
            sent_at=datetime.now() - timedelta(days=2),
            response_received_at=None,
            response_type=None
        )
    ]

@pytest.fixture
def test_engagement_metrics():
    """Create a list of test engagement metrics."""
    return [
        EngagementMetric(
            id=1,
            prospect_id=1,
            campaign_id=1,
            metric_type="response_time",
            value=3600,  # 1 hour in seconds
            recorded_at=datetime.now()
        ),
        EngagementMetric(
            id=2,
            prospect_id=2,
            campaign_id=2,
            metric_type="open_rate",
            value=0.75,  # 75%
            recorded_at=datetime.now()
        )
    ]

@pytest.fixture
def test_scraped_data():
    """Create test scraped data."""
    return {
        "linkedin": {
            "profile": {
                "name": "John Doe",
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco",
                "summary": "Experienced software engineer...",
                "skills": ["Python", "JavaScript", "AWS"],
                "experience": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "duration": "2 years"
                    }
                ]
            }
        },
        "twitter": {
            "profile": {
                "username": "@johndoe",
                "bio": "Software engineer and tech enthusiast",
                "followers": 1000,
                "following": 500,
                "tweets": [
                    {
                        "text": "Excited about new tech!",
                        "created_at": "2024-01-01T12:00:00Z",
                        "likes": 50
                    }
                ]
            }
        }
    }

@pytest.fixture
def test_ai_analysis():
    """Create test AI analysis results."""
    return {
        "prospect_analysis": {
            "relevance_score": 0.85,
            "engagement_potential": 0.75,
            "interests": ["technology", "software_development", "cloud_computing"],
            "communication_style": "professional",
            "recommended_topics": ["AI", "Cloud Architecture", "DevOps"]
        },
        "content_recommendations": {
            "tone": "professional",
            "topics": ["cloud computing", "software architecture"],
            "key_points": ["experience", "industry trends", "technical expertise"],
            "personalization_factors": ["company size", "tech stack", "industry"]
        }
    }

@pytest.fixture
def test_campaign_analysis():
    """Create test campaign analysis results."""
    return {
        "performance_metrics": {
            "response_rate": 0.35,
            "acceptance_rate": 0.25,
            "average_response_time": 3600,
            "engagement_score": 0.75
        },
        "optimization_recommendations": {
            "timing": {
                "best_days": ["Monday", "Wednesday"],
                "best_hours": [10, 11, 15]
            },
            "content": {
                "topics": ["technical", "industry_news"],
                "tone": "professional"
            },
            "channels": ["linkedin", "email"]
        }
    }

@pytest.fixture
def test_timing_analysis():
    """Create test timing analysis results."""
    return {
        "optimal_times": [
            {
                "day": "Monday",
                "hour": 10,
                "confidence_score": 0.85
            },
            {
                "day": "Wednesday",
                "hour": 15,
                "confidence_score": 0.80
            }
        ],
        "timezone_considerations": {
            "prospect_timezone": "America/Los_Angeles",
            "optimal_windows": [
                {
                    "start": "09:00",
                    "end": "11:00",
                    "confidence_score": 0.90
                }
            ]
        }
    }

@pytest.fixture
def test_response_analysis():
    """Create test response analysis results."""
    return {
        "patterns": {
            "response_times": {
                "average": 3600,
                "distribution": {
                    "0-1h": 0.3,
                    "1-4h": 0.4,
                    "4-24h": 0.3
                }
            },
            "engagement_levels": {
                "high": 0.4,
                "medium": 0.4,
                "low": 0.2
            }
        },
        "sentiment": {
            "positive": 0.6,
            "neutral": 0.3,
            "negative": 0.1
        },
        "recommendations": {
            "timing": "Send messages in the morning",
            "content": "Focus on technical topics",
            "follow_up": "Wait 2-3 days before following up"
        }
    } 



logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
def setup_env():
    logger.debug("Setting up environment")
    os.environ["SENDGRID_API_KEY"] = "SG.test_key"
    os.environ["TWITTER_CONSUMER_KEY"] = "test_broadcast_key"
    os.environ["TWITTER_BEARER_TOKEN"] = "test_bearer"
    yield
    logger.debug("Cleaning up environment")
    for key in ["SENDGRID_API_KEY", "TWITTER_CONSUMER_KEY", "TWITTER_BEARER_TOKEN"]:
        os.environ.pop(key, None)

@pytest.fixture
def db_session():
    # Use PostgreSQL for testing
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url, echo=False)
    # Base.metadata.create_all(bind=engine)  # Commented out to avoid duplicate table/index errors
    Session = sessionmaker(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()
        # Clean up the test database file
        if os.path.exists("test.db"):
            os.remove("test.db")

@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        except Exception as e:
            db_session.rollback()
            raise
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield TestClient(app)
    finally:
        # Clean up the override
        app.dependency_overrides.clear()

# For backward compatibility, keep the reset_db fixture
@pytest.fixture
def reset_db(db_session):
    """Alias for db_session for backward compatibility"""
    return db_session

@pytest.fixture(autouse=True)
def setup_celery():
    logger.debug("Configuring Celery for synchronous task execution")
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = False
    logger.debug("Reset Celery task_always_eager to False")

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Run Alembic migrations before any tests."""
    logger.debug("Running Alembic migrations...")
    result = subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)
    logger.debug(f"Alembic migration output: {result.stdout}")
    if result.stderr:
        logger.error(f"Alembic migration errors: {result.stderr}")
    yield