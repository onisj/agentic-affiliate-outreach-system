"""
Intelligence Service Package

This package contains services for prospect intelligence and analysis.

Modules:
    scoring: Prospect scoring service
    sentiment: Sentiment analysis service
    personalization: Content personalization service
    timing: Optimal timing service
"""

from .scoring import ScoringService
from .sentiment import SentimentAnalyzer
from .personalization import PersonalizationService
from .timing import TimingService

__all__ = ['ScoringService', 'SentimentAnalyzer', 'PersonalizationService', 'TimingService'] 