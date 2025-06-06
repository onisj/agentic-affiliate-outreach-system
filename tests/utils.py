import pytest
from typing import Generator, Any, Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from redis import Redis
from celery import Celery
import functools
import inspect
import tweepy
import requests
import random
import uuid
from unittest.mock import patch

from api.main import app
from database.session import get_db
from config.settings import settings
from app.tasks.celery_app import celery_app
from database.models import (
    AffiliateProspect, MessageTemplate, OutreachCampaign,
    ProspectStatus, MessageType, CampaignStatus
)

@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a database session for testing."""
    session = next(get_db())
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def redis_client() -> Generator[Redis, None, None]:
    """Create a Redis client for testing."""
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        client.flushdb()
        client.close()

@pytest.fixture
def celery_app() -> Celery:
    """Create a Celery app for testing."""
    celery_app.conf.update({
        'task_always_eager': True,
        'task_eager_propagates': True,
    })
    return celery_app

def mock_redis_response(redis_client: Redis, key: str, value: Any) -> None:
    """Mock a Redis response for testing."""
    redis_client.set(key, value)

def mock_twitter_api(mocker) -> None:
    """Mock Twitter API responses for testing."""
    # Mock the tweepy Client for both authentication methods
    mock_client = mocker.MagicMock()
    
    # Mock successful DM sending
    mock_dm_response = mocker.MagicMock()
    mock_dm_response.data = True
    mock_client.create_direct_message.return_value = mock_dm_response
    
    # Mock user profile fetch
    mock_user_response = mocker.MagicMock()
    mock_user_response.data = {
        'id': '123',
        'username': 'test_user',
        'name': 'Test User',
        'followers_count': 1000,
        'tweet_count': 500
    }
    mock_client.get_user.return_value = mock_user_response
    
    # Mock both authentication methods
    mocker.patch('services.social_service.tweepy.Client', return_value=mock_client)
    
    # Mock rate limit errors
    def mock_rate_limit(*args, **kwargs):
        raise tweepy.TooManyRequests("Rate limit exceeded")
    
    # Mock authentication errors
    def mock_auth_error(*args, **kwargs):
        raise tweepy.Unauthorized("Invalid or expired token")
    
    # Add error mocks to the client
    mock_client.create_direct_message.side_effect = None  # Reset side effect
    mock_client.get_user.side_effect = None  # Reset side effect
    
    # Store the error mocks for use in tests
    mock_client.mock_rate_limit = mock_rate_limit
    mock_client.mock_auth_error = mock_auth_error

def mock_linkedin_api():
    """Mock LinkedIn API responses."""
    return patch('services.social_service.LinkedInAPI.get_profile', side_effect=mock_linkedin_profile)

def mock_linkedin_profile(urn: str) -> Dict[str, Any]:
    """Mock LinkedIn profile data."""
    if not urn.startswith('urn:li:person:'):
        raise ValueError("Invalid LinkedIn URN format")
    
    # Simulate rate limiting
    if random.random() < 0.1:  # 10% chance of rate limit
        raise requests.exceptions.HTTPError(
            response=type('Response', (), {'status_code': 429, 'text': 'Rate limit exceeded'})()
        )
    
    # Simulate authentication errors
    if random.random() < 0.05:  # 5% chance of auth error
        raise requests.exceptions.HTTPError(
            response=type('Response', (), {'status_code': 401, 'text': 'Invalid access token'})()
        )
    
    return {
        "id": urn,
        "firstName": "John",
        "lastName": "Doe",
        "headline": "Software Engineer",
        "industry": "Technology",
        "location": {"name": "San Francisco Bay Area"},
        "positions": {
            "values": [{
                "title": "Software Engineer",
                "company": "Tech Corp",
                "startDate": {"year": 2020},
                "isCurrent": True
            }]
        }
    }

def mock_linkedin_message():
    """Mock LinkedIn message sending."""
    return patch('services.social_service.LinkedInAPI.send_message', side_effect=mock_send_linkedin_message)

def mock_send_linkedin_message(urn: str, message: str) -> Dict[str, Any]:
    """Mock sending a LinkedIn message."""
    if not urn.startswith('urn:li:person:'):
        raise ValueError("Invalid LinkedIn URN format")
    
    # Simulate various error cases
    if random.random() < 0.1:  # 10% chance of rate limit
        raise requests.exceptions.HTTPError(
            response=type('Response', (), {'status_code': 429, 'text': 'Rate limit exceeded'})()
        )
    
    if random.random() < 0.05:  # 5% chance of auth error
        raise requests.exceptions.HTTPError(
            response=type('Response', (), {'status_code': 401, 'text': 'Invalid access token'})()
        )
    
    if random.random() < 0.05:  # 5% chance of permission error
        raise requests.exceptions.HTTPError(
            response=type('Response', (), {'status_code': 403, 'text': 'Insufficient permissions'})()
        )
    
    return {
        "id": f"msg_{uuid.uuid4()}",
        "status": "SENT"
    }

def mock_sendgrid_email(mocker) -> None:
    """Mock SendGrid email sending for testing."""
    mocker.patch('services.email_service.EmailService.send_email', return_value=True)

def mock_services(mocker) -> None:
    """Mock all external services for testing."""
    # Only mock email sending, not template rendering
    mock_sendgrid = mocker.MagicMock()
    mock_sendgrid.send.return_value = mocker.MagicMock(status_code=202)
    mocker.patch('sendgrid.SendGridAPIClient', return_value=mock_sendgrid)
    mocker.patch('app.services.email_service.EmailService._send_via_sendgrid', return_value="test_message_id")
    mocker.patch('app.services.email_service.EmailService._send_via_smtp', return_value="test_message_id")
    # Do NOT mock render_string_template here

class TestData:
    """Test data for use in tests."""
    PROSPECT = {
        'email': 'test@example.com',
        'name': 'Test User',
        'company': 'Test Company',
        'position': 'Test Position'
    }
    
    TEMPLATE = {
        'name': 'Test Template',
        'subject': 'Test Subject',
        'body': 'Hello {{name}}, this is a test.',
        'type': 'email'
    }
    
    CAMPAIGN = {
        'name': 'Test Campaign',
        'template_id': 1,
        'status': 'draft'
    }

def create_test_prospect(db_session: Session, data: Dict[str, Any] = None) -> Any:
    """Create a test prospect in the database."""
    prospect_data = data or TestData.PROSPECT
    prospect = AffiliateProspect(
        email=prospect_data['email'],
        first_name=prospect_data.get('name', 'Test').split()[0],
        last_name=prospect_data.get('name', 'User').split()[-1],
        company=prospect_data.get('company', 'Test Company'),
        status=ProspectStatus.NEW
    )
    db_session.add(prospect)
    db_session.commit()
    return prospect

def create_test_template(db_session: Session, data: Dict[str, Any] = None) -> Any:
    """Create a test email template in the database."""
    template_data = data or TestData.TEMPLATE
    template = MessageTemplate(
        name=template_data['name'],
        subject=template_data['subject'],
        content=template_data['body'],
        message_type=MessageType.EMAIL,
        is_active=True
    )
    db_session.add(template)
    db_session.commit()
    return template

def create_test_campaign(db_session: Session, data: Dict[str, Any] = None) -> Any:
    """Create a test campaign in the database."""
    campaign_data = data or TestData.CAMPAIGN
    campaign = OutreachCampaign(
        name=campaign_data['name'],
        template_id=campaign_data.get('template_id'),
        target_criteria={},
        status=CampaignStatus.DRAFT
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign

def with_db_rollback(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Try to find db_session in kwargs or args
        db_session = kwargs.get('db_session')
        if db_session is None:
            # Try to find db_session by inspecting the function signature
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            if 'db_session' in params:
                db_session_index = params.index('db_session')
                if len(args) > db_session_index:
                    db_session = args[db_session_index]
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            if db_session is not None:
                db_session.rollback()
    return wrapper

def with_redis_cache(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Assume the first argument is the redis_client
        redis_client = args[0]
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            redis_client.flushdb()
    return wrapper 