from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from database.base import Base
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """
    Get the database URL depending on the environment.
    Prioritizes:
    1. Environment variable from settings
    2. Local dev default
    """
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "postgresql+psycopg2://root:root@localhost:5432/affiliate_db"
    return settings.DATABASE_URL or "postgresql+psycopg2://root:root@localhost:5432/affiliate_db"

# Create SQLAlchemy engine
try:
    engine = create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
    )
    logger.info("Database engine created successfully.")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Provide a DB session generator for FastAPI or other consumers."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize the database schema."""
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
