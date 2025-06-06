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

# LinkedIn-specific settings
LINKEDIN_SETTINGS = {
    "data_dir": DATA_DIR / "linkedin",
    "output_dir": OUTPUT_DIR / "linkedin",
    "logs_dir": LOGS_DIR / "linkedin",
    "max_retries": 3,
    "rate_limit_delay": 1,  # seconds
    "batch_size": 50,
}

# Twitter-specific settings
TWITTER_SETTINGS = {
    "data_dir": DATA_DIR / "twitter",
    "output_dir": OUTPUT_DIR / "twitter",
    "logs_dir": LOGS_DIR / "twitter",
    "max_retries": 3,
    "rate_limit_delay": 1,  # seconds
    "batch_size": 100,
}

# Common settings
COMMON_SETTINGS = {
    "date_format": "%Y-%m-%d",
    "datetime_format": "%Y-%m-%d %H:%M:%S",
    "timezone": "UTC",
}

def get_settings(platform: str) -> Dict[str, Any]:
    """Get settings for a specific platform."""
    settings_map = {
        "linkedin": LINKEDIN_SETTINGS,
        "twitter": TWITTER_SETTINGS,
    }
    return {**COMMON_SETTINGS, **(settings_map.get(platform, {}))} 