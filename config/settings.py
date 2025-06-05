import os
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    # Redis settings
    REDIS_URL: Optional[str] = None
    
    # API Keys (required for runtime, not for migrations)
    TWITTER_BEARER_TOKEN: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    
    # JWT settings
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email settings
    SMTP_HOST: str = "smtp.sendgrid.net"
    SMTP_PORT: int = 587
    SMTP_USER: str = "apikey"
    EMAIL_FROM: str = "noreply@yourdomain.com"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Template IDs (optional for migrations)
    POSITIVE_RESPONSE_TEMPLATE_ID: Optional[str] = None
    NEGATIVE_RESPONSE_TEMPLATE_ID: Optional[str] = None
    NEUTRAL_RESPONSE_TEMPLATE_ID: Optional[str] = None

    # LinkedIn OAuth (optional for migrations)
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URL: Optional[str] = None
    SECRET_KEY: Optional[str] = None

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @property
    def SMTP_PASSWORD(self) -> Optional[str]:
        # Use SENDGRID_API_KEY for SMTP auth if available
        return self.SENDGRID_API_KEY

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()