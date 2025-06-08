"""
Rate Limiter

This module implements intelligent rate limiting for web scraping operations
to prevent IP blocking and ensure ethical scraping practices.
"""

from typing import Dict, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
from collections import deque

from services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class RateLimiter:
    """Manages request rates for different platforms."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.request_timestamps: Dict[str, deque] = {}
        self.rate_limits: Dict[str, Dict[str, int]] = {}
        self.backoff_times: Dict[str, datetime] = {}
        
    async def wait_if_needed(self, platform: str):
        """Wait if necessary to respect rate limits."""
        try:
            # Check if platform is in backoff
            if await self._is_in_backoff(platform):
                await self._wait_for_backoff(platform)
                
            # Initialize if not exists
            if platform not in self.request_timestamps:
                self.request_timestamps[platform] = deque()
                self.rate_limits[platform] = self._get_default_limits(platform)
                
            # Clean old timestamps
            await self._clean_old_timestamps(platform)
            
            # Check if we need to wait
            if len(self.request_timestamps[platform]) >= self.rate_limits[platform]['requests_per_minute']:
                wait_time = await self._calculate_wait_time(platform)
                if wait_time > 0:
                    logger.info(f"Rate limit reached for {platform}, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    
            # Record new request
            self.request_timestamps[platform].append(datetime.now())
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error in rate limiting: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def update_limits(
        self,
        platform: str,
        new_limits: Dict[str, int]
    ):
        """Update rate limits for a platform."""
        try:
            if platform not in self.rate_limits:
                self.rate_limits[platform] = self._get_default_limits(platform)
                
            self.rate_limits[platform].update(new_limits)
            logger.info(f"Updated rate limits for {platform}: {new_limits}")
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating rate limits: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    def get_status(self, platform: str) -> Dict[str, Any]:
        """Get current rate limiting status."""
        try:
            if platform not in self.rate_limits:
                return {"status": "not_initialized"}
                
            return {
                "current_requests": len(self.request_timestamps.get(platform, [])),
                "rate_limits": self.rate_limits[platform],
                "in_backoff": platform in self.backoff_times,
                "backoff_until": self.backoff_times.get(platform)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting rate limit status: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def trigger_backoff(self, platform: str, duration_minutes: int = 5):
        """Trigger backoff period for a platform."""
        try:
            self.backoff_times[platform] = datetime.now() + timedelta(minutes=duration_minutes)
            logger.info(f"Triggered {duration_minutes} minute backoff for {platform}")
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error triggering backoff: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def _is_in_backoff(self, platform: str) -> bool:
        """Check if platform is in backoff period."""
        if platform not in self.backoff_times:
            return False
            
        if datetime.now() > self.backoff_times[platform]:
            del self.backoff_times[platform]
            return False
            
        return True
        
    async def _wait_for_backoff(self, platform: str):
        """Wait until backoff period is over."""
        if platform in self.backoff_times:
            wait_time = (self.backoff_times[platform] - datetime.now()).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
    async def _clean_old_timestamps(self, platform: str):
        """Remove timestamps older than the rate limit window."""
        if platform not in self.request_timestamps:
            return
            
        window = timedelta(minutes=1)
        now = datetime.now()
        
        while (self.request_timestamps[platform] and
               now - self.request_timestamps[platform][0] > window):
            self.request_timestamps[platform].popleft()
            
    async def _calculate_wait_time(self, platform: str) -> float:
        """Calculate how long to wait before next request."""
        if not self.request_timestamps[platform]:
            return 0
            
        oldest_timestamp = self.request_timestamps[platform][0]
        window = timedelta(minutes=1)
        now = datetime.now()
        
        if now - oldest_timestamp < window:
            return (window - (now - oldest_timestamp)).total_seconds()
            
        return 0
        
    def _get_default_limits(self, platform: str) -> Dict[str, int]:
        """Get default rate limits for a platform."""
        return {
            'requests_per_minute': self.config.get('default_requests_per_minute', 30),
            'max_requests_per_hour': self.config.get('default_max_requests_per_hour', 1000),
            'max_requests_per_day': self.config.get('default_max_requests_per_day', 10000)
        } 