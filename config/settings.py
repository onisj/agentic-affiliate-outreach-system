import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY")
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    POSITIVE_RESPONSE_TEMPLATE_ID: str = os.getenv("POSITIVE_RESPONSE_TEMPLATE_ID")
    NEGATIVE_RESPONSE_TEMPLATE_ID: str = os.getenv("NEGATIVE_RESPONSE_TEMPLATE_ID")
    NEUTRAL_RESPONSE_TEMPLATE_ID: str = os.getenv("NEUTRAL_RESPONSE_TEMPLATE_ID")

settings = Settings()