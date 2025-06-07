"""
Facebook API Client

This module provides a client for interacting with the Facebook Graph API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class FacebookClient(BaseAPIClient):
    """Facebook API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Facebook')
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 200, 'period': 3600},  # 200 messages per hour
            'post': {'calls': 50, 'period': 3600},  # 50 posts per hour
            'comment': {'calls': 200, 'period': 3600}  # 200 comments per hour
        }
        self.call_timestamps = {
            'message': [],
            'post': [],
            'comment': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Facebook Graph API"""
        try:
            if self.is_token_valid():
                return True
                
            auth_url = "https://www.facebook.com/v12.0/dialog/oauth"
            token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
            
            # Get authorization code
            params = {
                'client_id': self.app_id,
                'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
                'scope': 'pages_messaging,pages_show_list,pages_read_engagement',
                'response_type': 'code'
            }
            
            response = await self.make_request('GET', auth_url, params=params)
            if not response:
                return False
            
            # Exchange code for access token
            data = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
                'code': response.get('code')
            }
            
            token_response = await self.make_request('GET', token_url, params=data)
            if not token_response:
                return False
            
            self.access_token = token_response['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_response['expires_in'])
            return True
                
        except Exception as e:
            self.log_api_error('authentication', e)
            return False
    
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """Send a message to a Facebook user"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = f"https://graph.facebook.com/v12.0/me/messages"
            data = {
                'recipient': {'id': recipient_id},
                'message': {'text': message}
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
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a Facebook user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"https://graph.facebook.com/v12.0/{user_id}"
            params = {
                'fields': 'id,name,email,picture'
            }
            
            return await self.make_request(
                'GET',
                url,
                headers=self.get_auth_headers(),
                params=params
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def create_post(self, page_id: str, message: str) -> bool:
        """Create a post on a Facebook page"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('post'):
                return False
            
            url = f"https://graph.facebook.com/v12.0/{page_id}/feed"
            data = {
                'message': message
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('create_post', e)
            return False
    
    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a Facebook post"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('comment'):
                return False
            
            url = f"https://graph.facebook.com/v12.0/{post_id}/comments"
            data = {
                'message': comment
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('comment_on_post', e)
            return False 