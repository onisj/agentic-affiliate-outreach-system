"""
WhatsApp Business API Client

This module provides a client for interacting with the WhatsApp Business API, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class WhatsAppClient(BaseAPIClient):
    """WhatsApp Business API client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('WhatsApp')
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        
        # Rate limiting settings
        self.rate_limits = {
            'message': {'calls': 1000, 'period': 3600},  # 1000 messages per hour
            'template': {'calls': 100, 'period': 3600},  # 100 template messages per hour
            'media': {'calls': 100, 'period': 3600}  # 100 media messages per hour
        }
        self.call_timestamps = {
            'message': [],
            'template': [],
            'media': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with WhatsApp Business API"""
        # WhatsApp uses permanent access tokens
        return bool(self.access_token)
    
    async def send_message(self, phone_number: str, message: str) -> bool:
        """Send a WhatsApp message"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('message'):
                return False
            
            url = f"https://graph.facebook.com/v12.0/{self.phone_number_id}/messages"
            data = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'text',
                'text': {'body': message}
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
    
    async def get_user_profile(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get a WhatsApp user's profile"""
        try:
            if not await self.authenticate():
                return None
            
            url = f"https://graph.facebook.com/v12.0/{self.phone_number_id}"
            params = {
                'fields': 'profile'
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
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        template_params: Dict[str, str]
    ) -> bool:
        """Send a WhatsApp template message"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('template'):
                return False
            
            url = f"https://graph.facebook.com/v12.0/{self.phone_number_id}/messages"
            data = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': 'en'},
                    'components': [
                        {
                            'type': 'body',
                            'parameters': [
                                {'type': 'text', 'text': value}
                                for value in template_params.values()
                            ]
                        }
                    ]
                }
            }
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_template_message', e)
            return False
    
    async def send_media_message(
        self,
        phone_number: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Send a WhatsApp media message"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('media'):
                return False
            
            url = f"https://graph.facebook.com/v12.0/{self.phone_number_id}/messages"
            data = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': media_type,
                media_type: {
                    'link': media_url
                }
            }
            
            if caption:
                data[media_type]['caption'] = caption
            
            response = await self.make_request(
                'POST',
                url,
                headers=self.get_auth_headers(),
                json=data
            )
            return response is not None
                
        except Exception as e:
            self.log_api_error('send_media_message', e)
            return False 