"""
Reddit API Client

This module provides a client for interacting with the Reddit API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class RedditClient(BaseAPIClient):
    """Reddit API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Reddit')
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.username = settings.REDDIT_USERNAME
        self.password = settings.REDDIT_PASSWORD
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 100, 'period': 3600},  # 100 messages per hour
            'post': {'calls': 50, 'period': 3600},  # 50 posts per hour
            'comment': {'calls': 200, 'period': 3600}  # 200 comments per hour
        }
        self.call_timestamps = {
            'message': [],
            'post': [],
            'comment': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Reddit API"""
        try:
            if self.is_token_valid():
                return True
                
            auth_url = "https://www.reddit.com/api/v1/access_token"
            data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password
            }
            headers = {
                'Authorization': f'Basic {self.client_id}:{self.client_secret}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = await self.make_request('POST', auth_url, headers=headers, data=data)
            if not response:
                return False
            
            self.access_token = response['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=response['expires_in'])
            return True
                
        except Exception as e:
            self.log_api_error('authentication', e)
            return False
    
    async def send_message(self, username: str, message: str) -> bool:
        """Send a message to a Reddit user"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = "https://oauth.reddit.com/api/compose"
            data = {
                'api_type': 'json',
                'to': username,
                'subject': 'New Message',
                'text': message
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                data=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_message', e)
            return False
    
    async def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a Reddit user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"https://oauth.reddit.com/user/{username}/about"
            return await self.make_request(
                'GET',
                url,
                headers=self.get_auth_headers()
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def create_post(
        self,
        subreddit: str,
        title: str,
        content: str,
        kind: str = 'text'
    ) -> bool:
        """Create a Reddit post"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('post'):
                return False
            
            url = f"https://oauth.reddit.com/r/{subreddit}/submit"
            data = {
                'api_type': 'json',
                'kind': kind,
                'title': title,
                'text': content
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                data=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('create_post', e)
            return False
    
    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a Reddit post"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('comment'):
                return False
            
            url = "https://oauth.reddit.com/api/comment"
            data = {
                'api_type': 'json',
                'thing_id': post_id,
                'text': comment
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                data=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('comment_on_post', e)
            return False 