"""
Twitter API Client

This module provides a client for interacting with the Twitter API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class TwitterClient(BaseAPIClient):
    """Twitter API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Twitter')
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.access_token = settings.TWITTER_ACCESS_TOKEN
        self.access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET
        self.bearer_token = settings.TWITTER_BEARER_TOKEN
        
        # Rate limiting settings
        self.rate_limits = {
            'dm': {'calls': 1000, 'period': 86400},  # 1000 DMs per day
            'tweet': {'calls': 200, 'period': 900},  # 200 tweets per 15 minutes
            'follow': {'calls': 400, 'period': 86400}  # 400 follows per day
        }
        self.call_timestamps = {
            'dm': [],
            'tweet': [],
            'follow': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        # Twitter uses bearer token authentication, which is already set
        return bool(self.bearer_token)
    
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """Send a direct message to a Twitter user"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('dm'):
                return False
            
            url = "https://api.twitter.com/2/dm_conversations/with/:recipient_id/messages"
            data = {
                'text': message
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_message', e)
            return False
    
    async def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a Twitter user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"https://api.twitter.com/2/users/by/username/{username}"
            return await self.make_request(
                'GET',
                url,
                headers=self.get_auth_headers()
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def send_tweet(self, text: str) -> bool:
        """Send a tweet"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('tweet'):
                return False
            
            url = "https://api.twitter.com/2/tweets"
            data = {
                'text': text
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_tweet', e)
            return False
    
    async def follow_user(self, user_id: str) -> bool:
        """Follow a Twitter user"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('follow'):
                return False
            
            url = f"https://api.twitter.com/2/users/:id/following"
            data = {
                'target_user_id': user_id
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('follow_user', e)
            return False 