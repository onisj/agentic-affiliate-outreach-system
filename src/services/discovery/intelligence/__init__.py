"""
Intelligence Module

This module implements the intelligence components for the discovery process,
including AI agents, timing analysis, personalization, and sentiment analysis.
"""

from .ai_agent import AIAgent
from .timing import TimingAnalyzer
from .personalization import PersonalizationEngine
from .sentiment import SentimentAnalyzer
from .scoring import ProspectScorer

__all__ = [
    'AIAgent',
    'TimingAnalyzer',
    'PersonalizationEngine',
    'SentimentAnalyzer',
    'ProspectScorer'
]

__version__ = "1.0.0"