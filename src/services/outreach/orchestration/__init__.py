"""
Outreach Orchestration Module

This module implements the Multi-Channel Campaign Architecture for the
Agentic Affiliate Outreach System, providing:

1. Campaign Intelligence:
   - Strategy Engine
   - Personalization AI
   - Timing Optimizer
   - Channel Selector

2. Message Generation:
   - Template Engine
   - Content Generation AI
   - Localization Engine
   - A/B Test Manager

3. Delivery Channels:
   - Email Service
   - LinkedIn Messenger
   - Twitter DM
   - Instagram DM
   - Facebook Messenger
   - WhatsApp Business

4. Tracking & Analytics:
   - Delivery Tracker
   - Engagement Tracker
   - Response Tracker
   - Conversion Tracker
"""

from .campaign_orchestrator import CampaignOrchestrator
from .campaign_intelligence import (
    StrategyEngine,
    PersonalizationAI,
    TimingOptimizer,
    ChannelSelector
)
from .message_generation import (
    TemplateEngine,
    ContentGenerationAI,
    LocalizationEngine,
    ABTestManager
)
from .delivery_channels import (
    EmailService,
    LinkedInMessenger,
    TwitterDM,
    InstagramDM,
    FacebookMessenger,
    WhatsAppBusiness,
    DeliveryTracker,
    EngagementTracker,
    ResponseTracker,
    ConversionTracker
)

__all__ = [
    'CampaignOrchestrator',
    'StrategyEngine',
    'PersonalizationAI',
    'TimingOptimizer',
    'ChannelSelector',
    'TemplateEngine',
    'ContentGenerationAI',
    'LocalizationEngine',
    'ABTestManager',
    'EmailService',
    'LinkedInMessenger',
    'TwitterDM',
    'InstagramDM',
    'FacebookMessenger',
    'WhatsAppBusiness',
    'DeliveryTracker',
    'EngagementTracker',
    'ResponseTracker',
    'ConversionTracker'
] 