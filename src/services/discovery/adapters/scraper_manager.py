"""
Scraper Manager

This module implements the ScraperManager class for managing platform-specific
scrapers in the Agentic Affiliate Outreach System.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from services.monitoring import MonitoringService
from services.discovery.adapters.linkedin_scraper import LinkedInScraper
from services.discovery.adapters.twitter_scraper import TwitterScraper
from services.discovery.adapters.youtube_scraper import YouTubeScraper
from services.discovery.adapters.tiktok_scraper import TikTokScraper
from services.discovery.adapters.instagram_scraper import InstagramScraper
from services.discovery.adapters.reddit_scraper import RedditScraper
from services.discovery.adapters.generic_scraper import GenericWebScraper
from services.discovery.models.data_object import DataObject, PlatformType

class ScraperManager:
    """Manages platform-specific scrapers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize scraper manager."""
        self.config = config or {}
        self.monitoring = MonitoringService()
        
        # Initialize scrapers
        self.scrapers = {
            PlatformType.LINKEDIN: LinkedInScraper(self.config),
            PlatformType.TWITTER: TwitterScraper(self.config),
            PlatformType.YOUTUBE: YouTubeScraper(self.config),
            PlatformType.TIKTOK: TikTokScraper(self.config),
            PlatformType.INSTAGRAM: InstagramScraper(self.config),
            PlatformType.REDDIT: RedditScraper(self.config),
            PlatformType.GENERIC: GenericWebScraper(self.config)
        }
        
        # Initialize scraper status
        self.scraper_status: Dict[str, Dict[str, Any]] = {}
        
    async def get_scraper(self, platform: str) -> Any:
        """Get scraper for a specific platform."""
        try:
            # Get platform type
            platform_type = self._get_platform_type(platform)
            
            # Get scraper
            scraper = self.scrapers.get(platform_type)
            if not scraper:
                raise ValueError(f"No scraper found for platform: {platform}")
                
            return scraper
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting scraper: {str(e)}",
                error_type="scraper_retrieval_error",
                component="scraper_manager",
                context={'platform': platform}
            )
            raise
            
    async def update_scraper_status(self, platform: str, status: Dict[str, Any]):
        """Update status of a specific scraper."""
        try:
            self.scraper_status[platform] = {
                **status,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Record metric
            self.monitoring.record_metric(
                'scraper_status',
                1,
                {
                    'platform': platform,
                    'status': status.get('status', 'unknown')
                }
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating scraper status: {str(e)}",
                error_type="status_update_error",
                component="scraper_manager",
                context={'platform': platform}
            )
            raise
            
    def get_scraper_status(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific scraper."""
        return self.scraper_status.get(platform)
        
    def get_all_scraper_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all scrapers."""
        return self.scraper_status
        
    def _get_platform_type(self, platform: str) -> PlatformType:
        """Get platform type from string."""
        try:
            return PlatformType(platform.lower())
        except ValueError:
            return PlatformType.GENERIC
            
    async def cleanup(self):
        """Cleanup resources."""
        try:
            # Update all scrapers to inactive
            for platform in self.scrapers.keys():
                await self.update_scraper_status(
                    platform,
                    {'status': 'inactive'}
                )
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error in cleanup: {str(e)}",
                error_type="cleanup_error",
                component="scraper_manager"
            )
            raise 