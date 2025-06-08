"""
Affiliate Outreach System - Main Package

This package contains the core functionality of the Affiliate Outreach System,
including the API, services, database models, and configuration.

Modules:
    api: API endpoints and routes
    app: Application core and utilities
    config: Configuration management
    core: Core business logic
    database: Database models and session management
    services: Business services and utilities
    shared: Shared utilities and constants
    web: Web interface components
"""

__version__ = "1.0.0"
__author__ = "Affiliate Outreach Team"

from .api import *
from .app import *
from .config import *
from .core import *
from .database import *
from .services.monitoring import *
from .shared import *
from .web import *
