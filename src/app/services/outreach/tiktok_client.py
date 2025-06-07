"""
TikTok API Client

This module provides a client for interacting with the TikTok API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class TikTokClient(BaseAPIClient):
    """TikTok API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('TikTok')
        self.client_key = settings.TIKTOK_CLIENT_KEY
        self.client_secret = settings.TIKTOK_CLIENT_SECRET
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 100, 'period': 3600},  # 100 messages per hour
            'video': {'calls': 50, 'period': 3600},  # 50 video uploads per hour
            'comment': {'calls': 200, 'period': 3600}  # 200 comments per hour
        }
        self.call_timestamps = {
            'message': [],
            'video': [],
            'comment': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with TikTok API"""
        try:
            if self.is_token_valid():
                return True
                
            auth_url = "https://open.tiktokapis.com/v2/oauth/token/"
            data = {
                'client_key': self.client_key,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            response = await self.make_request('POST', auth_url, json=data)
            if not response:
                return False
            
            self.access_token = response['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=response['expires_in'])
            return True
                
        except Exception as e:
            self.log_api_error('authentication', e)
            return False
    
    async def send_message(self, user_id: str, message: str) -> bool:
        """Send a message to a TikTok user"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = "https://open.tiktokapis.com/v2/message/send/"
            data = {
                'user_id': user_id,
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
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a TikTok user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"https://open.tiktokapis.com/v2/user/info/"
            params = {
                'user_id': user_id
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
    
    async def upload_video(
        self,
        video_file: str,
        title: str,
        privacy_level: str = 'private'
    ) -> bool:
        """Upload a video to TikTok"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('video'):
                return False
            
            # First, get upload URL
            url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            data = {
                'post_info': {
                    'title': title,
                    'privacy_level': privacy_level
                }
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            if not response:
                return False
            
            upload_url = response['upload_url']
            
            # TODO: Implement multipart file upload
            upload_response = await self.make_request(
                'POST',
                upload_url,
                headers=self.get_auth_headers(),
                data={'video': video_file}
            )
            return upload_response is not None
                
        except Exception as e:
            self.log_api_error('upload_video', e)
            return False
    
    async def comment_on_video(self, video_id: str, comment: str) -> bool:
        """Comment on a TikTok video"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('comment'):
                return False
            
            url = "https://open.tiktokapis.com/v2/comment/publish/"
            data = {
                'video_id': video_id,
                'comment_text': comment
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('comment_on_video', e)
            return False 