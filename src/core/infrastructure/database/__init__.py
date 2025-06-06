"""
Database Package

This package contains all database-related functionality:
- Models: SQLAlchemy model definitions
- Session: Database session management
- Migrations: Alembic migration scripts
"""

from database.models import (
    AffiliateProspect as Prospect,
    OutreachCampaign as Campaign,
    MessageLog,
    MessageTemplate,
    ABTest,
    ABTestResult,
    SystemMetric,
    WebhookMetric,
    Alert
)

from database.session import get_db, SessionLocal

__all__ = [
    # Models
    "Prospect",
    "Campaign",
    "MessageLog",
    "MessageTemplate",
    "ABTest",
    "ABTestResult",
    "SystemMetric",
    "WebhookMetric",
    "Alert",
    
    # Session
    "get_db",
    "SessionLocal"
]
