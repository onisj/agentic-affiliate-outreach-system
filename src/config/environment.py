"""
Environment Configuration

This module handles environment-specific configuration.
"""

import os
from pathlib import Path
from typing import Dict, Any
from .settings import settings

def get_environment_config() -> Dict[str, Any]:
    """Get environment-specific configuration"""
    
    config = {
        "development": {
            "debug": True,
            "reload": True,
            "workers": 1,
            "log_level": "debug",
            "database_pool_size": 5,
            "redis_pool_size": 5,
            "celery_worker_concurrency": 2,
        },
        "testing": {
            "debug": True,
            "reload": False,
            "workers": 1,
            "log_level": "debug",
            "database_pool_size": 1,
            "redis_pool_size": 1,
            "celery_worker_concurrency": 1,
        },
        "staging": {
            "debug": False,
            "reload": False,
            "workers": 2,
            "log_level": "info",
            "database_pool_size": 10,
            "redis_pool_size": 10,
            "celery_worker_concurrency": 4,
        },
        "production": {
            "debug": False,
            "reload": False,
            "workers": 4,
            "log_level": "info",
            "database_pool_size": 20,
            "redis_pool_size": 20,
            "celery_worker_concurrency": 8,
        }
    }
    
    return config.get(settings.ENVIRONMENT, config["development"])

def setup_environment() -> None:
    """Setup environment-specific configurations"""
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
    
    # Set Celery environment variables
    os.environ["CELERY_BROKER_URL"] = settings.CELERY_BROKER_URL
    os.environ["CELERY_RESULT_BACKEND"] = settings.CELERY_RESULT_BACKEND
    
    # Set database environment variables
    os.environ["DATABASE_URL"] = settings.DATABASE_URL
    
    # Set Redis environment variables
    os.environ["REDIS_URL"] = settings.REDIS_URL
    
    # Set logging environment variables
    os.environ["LOG_LEVEL"] = get_environment_config()["log_level"]
    
    # Set Prometheus environment variables
    if settings.ENABLE_METRICS:
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.PROMETHEUS_MULTIPROC_DIR 