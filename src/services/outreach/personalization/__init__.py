"""
Intelligent Personalization Engine

This module implements the Intelligent Personalization Engine for the Agentic Affiliate Outreach System.
It provides components for personalizing outreach messages based on prospect data, context, and engagement history.

Components:
- IntelligentPersonalizationEngine: Main engine for personalizing messages
- PersonalizationStrategy: Strategy generation and management
- MessageVariation: Message variation generation and selection
- ContextEngine: Context gathering and analysis
- FeedbackLoop: Learning and improvement from engagement data

The engine follows a sequence of steps:
1. Gather profile information
2. Collect context data
3. Generate personalization strategy
4. Create message variations
5. Select and create final message
6. Update personalization model based on feedback
"""

from .intelligent_engine import IntelligentPersonalizationEngine
from .strategy import PersonalizationStrategy
from .variation import MessageVariation
from .context import ContextEngine
from .feedback import FeedbackLoop

__all__ = [
    'IntelligentPersonalizationEngine',
    'PersonalizationStrategy',
    'MessageVariation',
    'ContextEngine',
    'FeedbackLoop'
] 