"""
Scraper Manager

This module implements the intelligent web scraping orchestration system that
manages multiple platform-specific scrapers with rate limiting, proxy rotation,
and intelligent retry mechanisms.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging
from abc import ABC, abstractmethod

from services.monitoring import MonitoringService
from services.discovery.scraping.base_scraper import BaseScraper
from services.discovery.scraping.proxy_manager import ProxyManager
from services.discovery.scraping.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class ScraperManager:
    """Manages and orchestrates multiple platform-specific scrapers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.proxy_manager = ProxyManager(config.get('proxy_config', {}))
        self.rate_limiter = RateLimiter(config.get('rate_limit_config', {}))
        self.scrapers: Dict[str, BaseScraper] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    async def register_scraper(self, platform: str, scraper: BaseScraper):
        """Register a platform-specific scraper."""
        try:
            self.scrapers[platform] = scraper
            logger.info(f"Registered scraper for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error registering scraper: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def start_scraping(
        self,
        platform: str,
        search_criteria: Dict[str, Any],
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Start scraping process for a specific platform."""
        try:
            if platform not in self.scrapers:
                raise ValueError(f"No scraper registered for platform: {platform}")
                
            # Get proxy for this scraping session
            proxy = await self.proxy_manager.get_proxy(platform)
            
            # Check rate limits
            await self.rate_limiter.wait_if_needed(platform)
            
            # Start scraping task
            scraper = self.scrapers[platform]
            scraper.set_proxy(proxy)
            
            results = await scraper.scrape(search_criteria)
            
            # Update metrics
            self.monitoring.record_metric(
                f"scraping_{platform}_results",
                len(results)
            )
            
            return results[:max_results]
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error during scraping: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def stop_scraping(self, platform: str):
        """Stop scraping process for a specific platform."""
        try:
            if platform in self.active_tasks:
                self.active_tasks[platform].cancel()
                del self.active_tasks[platform]
                logger.info(f"Stopped scraping for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error stopping scraping: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def get_scraping_status(self, platform: str) -> Dict[str, Any]:
        """Get current status of scraping process."""
        try:
            if platform not in self.scrapers:
                return {"status": "not_registered"}
                
            scraper = self.scrapers[platform]
            return {
                "status": "active" if platform in self.active_tasks else "idle",
                "metrics": scraper.get_metrics(),
                "rate_limit": self.rate_limiter.get_status(platform),
                "proxy": self.proxy_manager.get_current_proxy(platform)
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting scraping status: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def rotate_proxies(self, platform: str):
        """Rotate proxies for a specific platform."""
        try:
            await self.proxy_manager.rotate_proxy(platform)
            logger.info(f"Rotated proxy for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error rotating proxy: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def update_rate_limits(
        self,
        platform: str,
        new_limits: Dict[str, Any]
    ):
        """Update rate limits for a specific platform."""
        try:
            await self.rate_limiter.update_limits(platform, new_limits)
            logger.info(f"Updated rate limits for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating rate limits: {str(e)}",
                context={"platform": platform}
            )
            raise 