"""
Discovery Module

This module provides comprehensive prospect discovery capabilities,
including intelligence analysis, data scraping, pipeline processing,
and orchestration of discovery tasks.
"""

from .intelligence import (
    AIAgent,
    TimingAnalyzer,
    PersonalizationEngine,
    SentimentAnalyzer,
    ProspectScorer
)
from .scrapers import (
    BaseScraper,
    LinkedInScraper,
    TwitterScraper,
    YouTubeScraper,
    TikTokScraper,
    InstagramScraper,
    RedditScraper,
    WebScraper
)
from .pipeline import (
    DataCleaner,
    DataValidator,
    DataEnricher,
    ProspectScorer
)
from .orchestrator import (
    SmartScheduler,
    TaskManager
)

__all__ = [
    # Intelligence
    'AIAgent',
    'TimingAnalyzer',
    'PersonalizationEngine',
    'SentimentAnalyzer',
    'ProspectScorer',
    
    # Scrapers
    'BaseScraper',
    'LinkedInScraper',
    'TwitterScraper',
    'YouTubeScraper',
    'TikTokScraper',
    'InstagramScraper',
    'RedditScraper',
    'WebScraper',
    
    # Pipeline
    'DataCleaner',
    'DataValidator',
    'DataEnricher',
    'ProspectScorer',
    
    # Orchestrator
    'SmartScheduler',
    'TaskManager'
] 