"""
YouTube API Client

This module provides a client for interacting with the YouTube Data API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class YouTubeClient(BaseAPIClient):
    """YouTube API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('YouTube')
        self.api_key = settings.YOUTUBE_API_KEY
        self.client_id = settings.YOUTUBE_CLIENT_ID
        self.client_secret = settings.YOUTUBE_CLIENT_SECRET
        
        # Rate limiting settings
        self.rate_limits = {
            'comment': {'calls': 100, 'period': 3600},  # 100 comments per hour
            'video': {'calls': 50, 'period': 3600},  # 50 video uploads per hour
            'playlist': {'calls': 50, 'period': 3600}  # 50 playlist operations per hour
        }
        self.call_timestamps = {
            'comment': [],
            'video': [],
            'playlist': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with YouTube Data API"""
        try:
            if self.is_token_valid():
                return True
                
            auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
            token_url = "https://oauth2.googleapis.com/token"
            
            # Get authorization code
            params = {
                'client_id': self.client_id,
                'redirect_uri': settings.YOUTUBE_REDIRECT_URI,
                'scope': 'https://www.googleapis.com/auth/youtube.force-ssl',
                'response_type': 'code',
                'access_type': 'offline'
            }
            
            response = await self.make_request('GET', auth_url, params=params)
            if not response:
                return False
            
            # Exchange code for access token
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': settings.YOUTUBE_REDIRECT_URI,
                'code': response.get('code'),
                'grant_type': 'authorization_code'
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
    
    async def send_message(self, channel_id: str, message: str) -> bool:
        """Send a message to a YouTube channel (via comment)"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('comment'):
                return False
            
            url = "https://www.googleapis.com/youtube/v3/commentThreads"
            params = {
                'part': 'snippet',
                'key': self.api_key
            }
            data = {
                'snippet': {
                    'channelId': channel_id,
                    'topLevelComment': {
                        'snippet': {
                            'textOriginal': message
                        }
                    }
                }
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                params=params,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_message', e)
            return False
    
    async def get_user_profile(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get a YouTube channel's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'snippet,statistics',
                'id': channel_id,
                'key': self.api_key
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
        title: str,
        description: str,
        video_file: str,
        privacy_status: str = 'private'
    ) -> bool:
        """Upload a video to YouTube"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('video'):
                return False
            
            url = "https://www.googleapis.com/upload/youtube/v3/videos"
            params = {
                'part': 'snippet,status',
                'key': self.api_key
            }
            data = {
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            # TODO: Implement multipart file upload
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                params=params,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('upload_video', e)
            return False
    
    async def create_playlist(
        self,
        title: str,
        description: str,
        privacy_status: str = 'private'
    ) -> bool:
        """Create a YouTube playlist"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('playlist'):
                return False
            
            url = "https://www.googleapis.com/youtube/v3/playlists"
            params = {
                'part': 'snippet,status',
                'key': self.api_key
            }
            data = {
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                params=params,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('create_playlist', e)
            return False 