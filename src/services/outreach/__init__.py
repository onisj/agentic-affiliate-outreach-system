"""
Outreach Module

This module provides comprehensive outreach capabilities,
including message personalization, campaign management,
and intelligent response handling.
"""

from .intelligence import (
    ContextEngine,
    ContentGenerator,
    CampaignIntelligence,
    TimingEngine,
    ResponseAnalyzer,
    PersonalizationEngine
)

__all__ = [
    'ContextEngine',
    'ContentGenerator',
    'CampaignIntelligence',
    'TimingEngine',
    'ResponseAnalyzer',
    'PersonalizationEngine'
] 