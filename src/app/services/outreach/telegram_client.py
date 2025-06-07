"""
Telegram Bot API Client

This module provides a client for interacting with the Telegram Bot API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class TelegramClient(BaseAPIClient):
    """Telegram Bot API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Telegram')
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_base_url = "https://api.telegram.org/bot"
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 30, 'period': 1},  # 30 messages per second
            'media': {'calls': 20, 'period': 1},  # 20 media messages per second
            'callback': {'calls': 30, 'period': 1}  # 30 callback queries per second
        }
        self.call_timestamps = {
            'message': [],
            'media': [],
            'callback': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Telegram Bot API"""
        # Telegram uses bot tokens for authentication
        return bool(self.bot_token)
    
    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a Telegram chat"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = f"{self.api_base_url}{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = await self.make_request(
                'POST',
                url,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_message', e)
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a Telegram user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"{self.api_base_url}{self.bot_token}/getChat"
            params = {
                'chat_id': user_id
            }
            
            return await self.make_request(
                'GET',
                url,
                params=params
            )
                
        except Exception as e:
            self.log_api_error('get_user_profile', e)
            return None
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Send a photo to a Telegram chat"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('media'):
                return False
            
            url = f"{self.api_base_url}{self.bot_token}/sendPhoto"
            data = {
                'chat_id': chat_id,
                'photo': photo_url
            }
            
            if caption:
                data['caption'] = caption
                data['parse_mode'] = 'HTML'
            
            response = await self.make_request(
                'POST',
                url,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_photo', e)
            return False
    
    async def send_document(
        self,
        chat_id: str,
        document_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Send a document to a Telegram chat"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('media'):
                return False
            
            url = f"{self.api_base_url}{self.bot_token}/sendDocument"
            data = {
                'chat_id': chat_id,
                'document': document_url
            }
            
            if caption:
                data['caption'] = caption
                data['parse_mode'] = 'HTML'
            
            response = await self.make_request(
                'POST',
                url,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_document', e)
            return False
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> bool:
        """Answer a callback query"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('callback'):
                return False
            
            url = f"{self.api_base_url}{self.bot_token}/answerCallbackQuery"
            data = {
                'callback_query_id': callback_query_id,
                'show_alert': show_alert
            }
            
            if text:
                data['text'] = text
            
            response = await self.make_request(
                'POST',
                url,
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('answer_callback_query', e)
            return False 