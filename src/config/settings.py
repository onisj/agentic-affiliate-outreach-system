"""
Application Settings

This module contains all application settings and configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Affiliate Outreach System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "Affiliate Outreach API"
    API_DESCRIPTION: str = "API for managing affiliate outreach campaigns"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_POOL_SIZE: int = 10
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    
    # Social Media
    LINKEDIN_API_KEY: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    INSTAGRAM_API_KEY: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Create settings instance
settings = get_settings() 