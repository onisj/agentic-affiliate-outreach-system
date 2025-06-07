"""
Instagram API Client

This module provides a client for interacting with the Instagram Graph API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class InstagramClient(BaseAPIClient):
    """Instagram API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Instagram')
        self.app_id = settings.INSTAGRAM_APP_ID
        self.app_secret = settings.INSTAGRAM_APP_SECRET
        
        # Rate limiting settings
        self.rate_limits = {
            'dm': {'calls': 100, 'period': 3600},  # 100 DMs per hour
            'post': {'calls': 25, 'period': 3600},  # 25 posts per hour
            'comment': {'calls': 180, 'period': 3600}  # 180 comments per hour
        }
        self.call_timestamps = {
            'dm': [],
            'post': [],
            'comment': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Instagram Graph API"""
        try:
            if self.is_token_valid():
                return True
                
            auth_url = "https://api.instagram.com/oauth/authorize"
            token_url = "https://api.instagram.com/oauth/access_token"
            
            # Get authorization code
            params = {
                'client_id': self.app_id,
                'redirect_uri': settings.INSTAGRAM_REDIRECT_URI,
                'scope': 'instagram_basic,instagram_content_publish,instagram_messaging',
                'response_type': 'code'
            }
            
            response = await self.make_request('GET', auth_url, params=params)
            if not response:
                return False
            
            # Exchange code for access token
            data = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.INSTAGRAM_REDIRECT_URI,
                'code': response.get('code')
            }
            
            token_response = await self.make_request('POST', token_url, data=data)
            if not token_response:
                return False
            
            self.access_token = token_response['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_response['expires_in'])
            return True
                
        except Exception as e:
            self.log_api_error('authentication', e)
            return False
    
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """Send a direct message to an Instagram user"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('dm'):
                return False
            
            url = f"https://graph.instagram.com/v12.0/{recipient_id}/messages"
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
            self.log_api_error('send_message', e)
            return False
    
    async def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get an Instagram user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"https://graph.instagram.com/v12.0/{username}"
            return await self.make_request(
                'GET',
                url,
                headers=self.get_auth_headers()
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def create_post(self, caption: str, image_url: str) -> bool:
        """Create an Instagram post"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('post'):
                return False
            
            # First, upload the image
            url = "https://graph.instagram.com/v12.0/me/media"
            data = {
                'image_url': image_url,
                'caption': caption
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            if not response:
                return False
                
            media_id = response['id']
            
            # Then publish the post
            publish_url = f"https://graph.instagram.com/v12.0/me/media_publish"
            publish_data = {
                'creation_id': media_id
            }
            
            publish_response = await self.make_request(
                'POST',
                publish_url,
                headers=self.get_auth_headers(),
                json=publish_data
            )
            return publish_response is not None
                
        except Exception as e:
            self.log_api_error('create_post', e)
            return False
    
    async def comment_on_post(self, media_id: str, comment: str) -> bool:
        """Comment on an Instagram post"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('comment'):
                return False
            
            url = f"https://graph.instagram.com/v12.0/{media_id}/comments"
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