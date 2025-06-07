"""
Script Configuration

This module provides configuration settings for scripts:
- Output directories
- File paths
- Default values
- Environment-specific settings
"""

from pathlib import Path
from typing import Dict, Any

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Common settings template
def create_channel_settings(channel_name: str) -> Dict[str, Any]:
    return {
        "data_dir": DATA_DIR / channel_name,
        "output_dir": OUTPUT_DIR / channel_name,
        "logs_dir": LOGS_DIR / channel_name,
        "max_retries": 3,
        "rate_limit_delay": 1,  # seconds
        "batch_size": 50,
    }

# Channel-specific settings
LINKEDIN_SETTINGS = create_channel_settings("linkedin")
TWITTER_SETTINGS = create_channel_settings("twitter")
INSTAGRAM_SETTINGS = {
    **create_channel_settings("instagram"),
    "api_version": "v12.0",
    "media_types": ["IMAGE", "VIDEO", "CAROUSEL_ALBUM"]
}

FACEBOOK_SETTINGS = {
    **create_channel_settings("facebook"),
    "api_version": "v16.0",
    "include_messenger": True
}

WHATSAPP_SETTINGS = {
    **create_channel_settings("whatsapp"),
    "message_template_limit": 100,
    "business_account_required": True
}

YOUTUBE_SETTINGS = {
    **create_channel_settings("youtube"),
    "api_version": "v3",
    "comment_moderation": True
}

TIKTOK_SETTINGS = {
    **create_channel_settings("tiktok"),
    "api_version": "v2",
    "content_categories": ["educational", "business"]
}

TELEGRAM_SETTINGS = {
    **create_channel_settings("telegram"),
    "bot_api_version": "6.3",
    "group_size_limit": 200000
}

REDDIT_SETTINGS = {
    **create_channel_settings("reddit"),
    "api_version": "2.0",
    "rate_limit_window": 600  # seconds
}

EMAIL_SETTINGS = {
    **create_channel_settings("email"),
    "providers": ["sendgrid", "mailgun", "ses"],
    "bounce_threshold": 0.05,
    "max_daily_sends": 10000
}

# Global settings
GLOBAL_SETTINGS = {
    "default_timeout": 30,  # seconds
    "retry_delay": 5,  # seconds
    "max_concurrent_requests": 10,
    "user_agent": "YourApp/1.0",
}

# Compliance settings
COMPLIANCE_SETTINGS = {
    "gdpr_enabled": True,
    "ccpa_enabled": True,
    "data_retention_days": 90,
    "consent_required": True,
}

# Analytics settings
ANALYTICS_SETTINGS = {
    "tracking_enabled": True,
    "metrics_interval": 300,  # seconds
    "dashboard_update_frequency": 900,  # seconds
}