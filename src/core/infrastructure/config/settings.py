from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql+psycopg2://root:root@localhost:5432/affiliate_db"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    
    # API Keys (optional - provide defaults)
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    TWITTER_CLIENT_ID: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    
    # JWT settings
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    EMAIL_FROM: Optional[str] = None  # Alias for FROM_EMAIL
    
    @property
    def SMTP_SERVER(self) -> Optional[str]:
        """Get SMTP server from SMTP_HOST."""
        return self.SMTP_HOST
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: Optional[str] = None

    # Template IDs (optional for migrations)
    POSITIVE_RESPONSE_TEMPLATE_ID: Optional[str] = None
    NEGATIVE_RESPONSE_TEMPLATE_ID: Optional[str] = None
    NEUTRAL_RESPONSE_TEMPLATE_ID: Optional[str] = None

    # LinkedIn OAuth settings
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URL: Optional[str] = None
    LINKEDIN_TOKEN_EXPIRY: int = 5184000
    LINKEDIN_SCOPES_STR: str = "w_member_social"

    @property
    def LINKEDIN_SCOPES(self) -> List[str]:
        return [s.strip() for s in self.LINKEDIN_SCOPES_STR.split(",")]

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @property
    def SMTP_PASSWORD(self) -> Optional[str]:
        # Use SENDGRID_API_KEY for SMTP auth if available
        return self.SENDGRID_API_KEY
    
    model_config = ConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()