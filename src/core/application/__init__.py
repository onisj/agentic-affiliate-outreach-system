"""
Affiliate Outreach System Core Application

This package contains the core application components:
- Services: Business logic and external integrations
- Tasks: Background processing and scheduled jobs
"""

from app.services import (
    MonitoringService,
    SocialService,
    OutreachService,
    ResponseTrackingService,
    LeadScoringService,
    CacheService,
    EmailService,
    WebhookService,
    VisualizationService
)

from app.tasks import (
    scoring_tasks,
    ab_testing_tasks,
    outreach_tasks,
    sequence_tasks
)

__version__ = "0.1.0"
__all__ = [
    "MonitoringService",
    "SocialService",
    "OutreachService",
    "ResponseTrackingService",
    "LeadScoringService",
    "CacheService",
    "EmailService",
    "WebhookService",
    "VisualizationService",
    "scoring_tasks",
    "ab_testing_tasks",
    "outreach_tasks",
    "sequence_tasks"
] 