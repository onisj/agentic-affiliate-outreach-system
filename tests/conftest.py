import os
import pytest
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
from fastapi.testclient import TestClient
from api.main import app
from tasks.celery_app import celery_app
from database.session import get_db

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
    db_url = os.getenv("TEST_DB_URL", "postgresql+psycopg2://root:root@localhost:5432/affiliate_db")
    engine = create_engine(db_url, echo=False)
    
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()

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