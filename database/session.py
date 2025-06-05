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
    """Get database URL based on environment."""
    # Check if we're running in Docker
    if os.getenv("DOCKER_ENV"):
        return settings.DATABASE_URL
    # Local development
    return "postgresql://root:root@localhost:5432/affiliate_db"

# Create SQLAlchemy engine for PostgreSQL
try:
    engine = create_engine(
        get_database_url(),
        pool_pre_ping=True,  # Test connections before use
        pool_size=5,         # Base pool size
        max_overflow=10,     # Allow extra connections
        pool_timeout=30      # Timeout for acquiring a connection
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Create configured Session class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """
    Provide a database session for dependency injection.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Create database tables
try:
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")
    raise