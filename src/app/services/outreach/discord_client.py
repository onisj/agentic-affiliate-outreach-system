"""
Discord API Client

This module provides a client for interacting with the Discord API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class DiscordClient(BaseAPIClient):
    """Discord API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Discord')
        self.bot_token = settings.DISCORD_BOT_TOKEN
        self.api_base_url = "https://discord.com/api/v10"
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 5, 'period': 5},  # 5 messages per 5 seconds
            'reaction': {'calls': 1, 'period': 1},  # 1 reaction per second
            'channel': {'calls': 5, 'period': 5}  # 5 channel operations per 5 seconds
        }
        self.call_timestamps = {
            'message': [],
            'reaction': [],
            'channel': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Discord API"""
        # Discord uses bot tokens for authentication
        return bool(self.bot_token)
    
    async def send_message(self, channel_id: str, message: str) -> bool:
        """Send a message to a Discord channel"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = f"{self.api_base_url}/channels/{channel_id}/messages"
            data = {
                'content': message
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
        """Get a Discord user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"{self.api_base_url}/users/{user_id}"
            return await self.make_request(
                'GET',
                url,
                headers=self.get_auth_headers()
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def send_embed(
        self,
        channel_id: str,
        title: str,
        description: str,
        color: Optional[int] = None,
        fields: Optional[list] = None
    ) -> bool:
        """Send an embed message to a Discord channel"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = f"{self.api_base_url}/channels/{channel_id}/messages"
            embed = {
                'title': title,
                'description': description
            }
            
            if color:
                embed['color'] = color
            if fields:
                embed['fields'] = fields
            
            data = {
                'embeds': [embed]
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_embed', e)
            return False
    
    async def add_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> bool:
        """Add a reaction to a Discord message"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('reaction'):
                return False
            
            url = f"{self.api_base_url}/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
            response = await self.make_request(
                'PUT',
                url,
                headers=self.get_auth_headers()
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('add_reaction', e)
            return False
    
    async def create_channel(
        self,
        guild_id: str,
        name: str,
        channel_type: str = 'text'
    ) -> bool:
        """Create a Discord channel"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('channel'):
                return False
            
            url = f"{self.api_base_url}/guilds/{guild_id}/channels"
            data = {
                'name': name,
                'type': 0 if channel_type == 'text' else 2  # 0 for text, 2 for voice
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('create_channel', e)
            return False 