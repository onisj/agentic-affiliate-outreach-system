"""
Base API Client

This module provides a base class for all platform-specific API clients,
implementing common functionality like rate limiting, authentication, and error handling.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class BaseAPIClient(ABC):
    """Base class for all platform-specific API clients"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Rate limiting settings - to be overridden by child classes
        self.rate_limits: Dict[str, Dict[str, int]] = {}
        self.call_timestamps: Dict[str, List[datetime]] = {}
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform's API"""
        pass
    
    async def respect_rate_limit(self, operation: str) -> None:
        """Ensure we don't exceed rate limits"""
        if operation not in self.rate_limits:
            return
            
        limit = self.rate_limits[operation]
        now = datetime.now()
        
        # Remove old timestamps
        self.call_timestamps[operation] = [
            ts for ts in self.call_timestamps[operation]
            if now - ts < timedelta(seconds=limit['period'])
        ]
        
        # If we've hit the limit, wait
        if len(self.call_timestamps[operation]) >= limit['calls']:
            wait_time = (self.call_timestamps[operation][0] + 
                        timedelta(seconds=limit['period']) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.call_timestamps[operation].append(now)
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make an HTTP request with error handling"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json,
                params=params
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(
                        f"{self.platform_name} API error: {response.status} - {error_text}"
                    )
                    return None
                
                return await response.json()
                
        except Exception as e:
            logger.error(f"Error making {self.platform_name} API request: {str(e)}")
            return None
    
    @abstractmethod
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """Send a message to a user"""
        pass
    
    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's profile"""
        pass
    
    def is_token_valid(self) -> bool:
        """Check if the current access token is valid"""
        return (
            self.access_token is not None
            and self.token_expiry is not None
            and datetime.now() < self.token_expiry
        )
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    async def handle_rate_limit(self, operation: str) -> bool:
        """Handle rate limiting for an operation"""
        try:
            await self.respect_rate_limit(operation)
            return True
        except Exception as e:
            logger.error(f"Error handling rate limit for {operation}: {str(e)}")
            return False
    
    def log_api_error(self, operation: str, error: Exception) -> None:
        """Log API errors consistently"""
        logger.error(
            f"{self.platform_name} {operation} error: {str(error)}",
            extra={
                'platform': self.platform_name,
                'operation': operation,
                'error': str(error)
            }
        ) 