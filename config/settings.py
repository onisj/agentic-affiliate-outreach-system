from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    SENDGRID_API_KEY: str
    TWITTER_CONSUMER_KEY: str
    TWITTER_BEARER_TOKEN: str
    LINKEDIN_CLIENT_ID: str
    LINKEDIN_CLIENT_SECRET: str
    LINKEDIN_REDIRECT_URL: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    POSITIVE_RESPONSE_TEMPLATE_ID: str
    NEGATIVE_RESPONSE_TEMPLATE_ID: str
    NEUTRAL_RESPONSE_TEMPLATE_ID: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()