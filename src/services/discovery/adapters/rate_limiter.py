"""
Rate Limiter

This module implements rate limiting functionality for platform adapters.
"""

from typing import Dict, Any, Optional
import logging
import asyncio
import time
from datetime import datetime, timedelta
from collections import defaultdict
import aiohttp
from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class RateLimiter:
    """Handles rate limiting for platform adapters."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Rate limit configurations per platform
        self.rate_limits = {
            'linkedin': {
                'requests_per_minute': 100,
                'requests_per_hour': 1000,
                'requests_per_day': 10000
            },
            'twitter': {
                'requests_per_minute': 300,
                'requests_per_hour': 3000,
                'requests_per_day': 30000
            },
            'youtube': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000
            },
            'tiktok': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000
            },
            'instagram': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000
            },
            'reddit': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000
            },
            'generic': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 10000
            }
        }
        
        # Request tracking
        self.request_history = defaultdict(list)
        self.locks = defaultdict(asyncio.Lock)
        
    async def acquire(self, platform: str) -> bool:
        """Acquire rate limit permission for a platform."""
        try:
            async with self.locks[platform]:
                if not self._check_rate_limits(platform):
                    await self._handle_rate_limit(platform)
                self._record_request(platform)
                return True
                
        except Exception as e:
            self._handle_error(e, f"acquiring rate limit for {platform}")
            return False
            
    def _check_rate_limits(self, platform: str) -> bool:
        """Check if platform is within rate limits."""
        try:
            limits = self.rate_limits.get(platform, self.rate_limits['generic'])
            history = self.request_history[platform]
            now = datetime.utcnow()
            
            # Clean old history
            history = [t for t in history if now - t < timedelta(days=1)]
            self.request_history[platform] = history
            
            # Check minute limit
            minute_ago = now - timedelta(minutes=1)
            minute_requests = len([t for t in history if t > minute_ago])
            if minute_requests >= limits['requests_per_minute']:
                return False
                
            # Check hour limit
            hour_ago = now - timedelta(hours=1)
            hour_requests = len([t for t in history if t > hour_ago])
            if hour_requests >= limits['requests_per_hour']:
                return False
                
            # Check day limit
            day_ago = now - timedelta(days=1)
            day_requests = len([t for t in history if t > day_ago])
            if day_requests >= limits['requests_per_day']:
                return False
                
            return True
            
        except Exception as e:
            self._handle_error(e, f"checking rate limits for {platform}")
            return False
            
    async def _handle_rate_limit(self, platform: str):
        """Handle rate limit exceeded."""
        try:
            limits = self.rate_limits.get(platform, self.rate_limits['generic'])
            history = self.request_history[platform]
            now = datetime.utcnow()
            
            # Calculate wait time based on the most restrictive limit
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            minute_requests = len([t for t in history if t > minute_ago])
            hour_requests = len([t for t in history if t > hour_ago])
            day_requests = len([t for t in history if t > day_ago])
            
            wait_times = []
            
            if minute_requests >= limits['requests_per_minute']:
                oldest_minute_request = min([t for t in history if t > minute_ago])
                wait_times.append(60 - (now - oldest_minute_request).total_seconds())
                
            if hour_requests >= limits['requests_per_hour']:
                oldest_hour_request = min([t for t in history if t > hour_ago])
                wait_times.append(3600 - (now - oldest_hour_request).total_seconds())
                
            if day_requests >= limits['requests_per_day']:
                oldest_day_request = min([t for t in history if t > day_ago])
                wait_times.append(86400 - (now - oldest_day_request).total_seconds())
                
            if wait_times:
                wait_time = max(wait_times)
                self.monitoring.log_warning(
                    f"Rate limit exceeded for {platform}, waiting {wait_time:.2f} seconds"
                )
                await asyncio.sleep(wait_time)
                
        except Exception as e:
            self._handle_error(e, f"handling rate limit for {platform}")
            
    def _record_request(self, platform: str):
        """Record a request for rate limiting."""
        try:
            self.request_history[platform].append(datetime.utcnow())
        except Exception as e:
            self._handle_error(e, f"recording request for {platform}")
            
    def _handle_error(self, error: Exception, context: str):
        """Handle errors with proper logging and monitoring."""
        error_msg = f"Error in {context}: {str(error)}"
        self.monitoring.log_error(error_msg)
        logger.error(error_msg)
        
    async def reset(self, platform: Optional[str] = None):
        """Reset rate limit tracking for a platform or all platforms."""
        try:
            if platform:
                self.request_history[platform] = []
            else:
                self.request_history.clear()
        except Exception as e:
            self._handle_error(e, f"resetting rate limits for {platform or 'all platforms'}")
            
    def get_remaining_requests(self, platform: str) -> Dict[str, int]:
        """Get remaining requests for a platform."""
        try:
            limits = self.rate_limits.get(platform, self.rate_limits['generic'])
            history = self.request_history[platform]
            now = datetime.utcnow()
            
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            minute_requests = len([t for t in history if t > minute_ago])
            hour_requests = len([t for t in history if t > hour_ago])
            day_requests = len([t for t in history if t > day_ago])
            
            return {
                'minute': limits['requests_per_minute'] - minute_requests,
                'hour': limits['requests_per_hour'] - hour_requests,
                'day': limits['requests_per_day'] - day_requests
            }
            
        except Exception as e:
            self._handle_error(e, f"getting remaining requests for {platform}")
            return {'minute': 0, 'hour': 0, 'day': 0} 