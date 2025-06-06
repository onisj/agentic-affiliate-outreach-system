"""
Social Media Tasks

This package provides Celery tasks for social media operations:
1. LinkedIn tasks for profile research, messaging, and analytics
2. Twitter tasks for profile research, messaging, and analytics
"""

from tasks.social.linkedin_tasks import (
    research_prospect as linkedin_research_prospect,
    analyze_campaign as linkedin_analyze_campaign,
    manage_connections as linkedin_manage_connections,
    send_messages as linkedin_send_messages
)

from tasks.social.twitter_tasks import (
    research_prospect as twitter_research_prospect,
    analyze_campaign as twitter_analyze_campaign,
    manage_connections as twitter_manage_connections,
    send_messages as twitter_send_messages
)

__all__ = [
    # LinkedIn tasks
    "linkedin_research_prospect",
    "linkedin_analyze_campaign",
    "linkedin_manage_connections",
    "linkedin_send_messages",
    
    # Twitter tasks
    "twitter_research_prospect",
    "twitter_analyze_campaign",
    "twitter_manage_connections",
    "twitter_send_messages"
] 