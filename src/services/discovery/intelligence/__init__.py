"""
Affiliate Discovery AI Package

This package provides AI-powered analysis tools for affiliate discovery across multiple platforms,
including competitive analysis, content analysis, network analysis, profile analysis, and trend analysis.
"""

from .competitive_analysis import CompetitiveAnalysisAI
from .content_analysis import ContentAnalysisAI
from .network_analysis import NetworkAnalysisAI
from .profile_analysis import ProfileAnalysisAI
from .trend_analysis import TrendAnalysisAI

__all__ = [
    "CompetitiveAnalysisAI",
    "ContentAnalysisAI",
    "NetworkAnalysisAI",
    "ProfileAnalysisAI",
    "TrendAnalysisAI",
]

__version__ = "1.0.0"