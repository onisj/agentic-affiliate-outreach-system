"""
LinkedIn API Client

This module provides a client for interacting with the LinkedIn API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class LinkedInClient(BaseAPIClient):
    """LinkedIn API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('LinkedIn')
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.redirect_uri = settings.LINKEDIN_REDIRECT_URI
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 100, 'period': 3600},  # 100 messages per hour
            'profile': {'calls': 1000, 'period': 3600},  # 1000 profile views per hour
            'connection': {'calls': 50, 'period': 3600}  # 50 connection requests per hour
        }
        self.call_timestamps = {
            'message': [],
            'profile': [],
            'connection': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with LinkedIn API"""
        try:
            if self.is_token_valid():
                return True
                
            auth_url = "https://www.linkedin.com/oauth/v2/authorization"
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            
            # Get authorization code
            params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': 'r_liteprofile r_emailaddress w_messages'
            }
            
            response = await self.make_request('GET', auth_url, params=params)
            if not response:
                return False
            
            # Exchange code for access token
            data = {
                'grant_type': 'authorization_code',
                'code': response.get('code'),
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
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
        """Send a message to a LinkedIn profile"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = f"https://api.linkedin.com/v2/messages"
            data = {
                'recipients': [{'person': {'id': recipient_id}}],
                'subject': 'New Connection',
                'body': message
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
        """Get a LinkedIn profile"""
        try:
            if not await self.authenticate():
                return None
                
            if not await self.handle_rate_limit('profile'):
                return None
            
            url = f"https://api.linkedin.com/v2/people/{user_id}"
            return await self.make_request(
                'GET',
                url,
                headers=self.get_auth_headers()
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def send_connection_request(self, profile_id: str, message: str) -> bool:
        """Send a connection request"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('connection'):
                return False
            
            url = f"https://api.linkedin.com/v2/invitations"
            data = {
                'invitee': {'person': {'id': profile_id}},
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
            self.log_api_error('send_connection_request', e)
            return False 