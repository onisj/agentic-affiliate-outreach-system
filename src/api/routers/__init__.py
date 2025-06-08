"""
API Endpoints Package

This package contains all API endpoint handlers.

Modules:
    prospects: Prospect-related endpoints
    campaigns: Campaign-related endpoints
    templates: Template-related endpoints
    ab_testing: A/B testing endpoints
    analytics: Analytics endpoints
"""
from .platform_router import PlatformRouter
from .ab_testing import *
from .affiliate_discovery import *
from .campaigns import *
from .message_templates import *
from .monitoring import *
from .prospects import *
from .responses import *
from .templates import *
from .webhooks import *

__all__ = ['PlatformRouter']