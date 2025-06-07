"""
WhatsApp Business Channel Service

Provides WhatsApp Business integration for messaging and customer engagement.
Uses WhatsApp Business API for automated messaging and customer support.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json

from .base_channel import (
    BaseChannelService, ChannelType, ChannelConfig, MessageRequest, 
    MessageResponse, ProfileData, EngagementMetrics, MessageStatus
)

class WhatsAppService(BaseChannelService):
    """WhatsApp Business channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://graph.facebook.com"
        self.api_version = "v18.0"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.WHATSAPP
    
    def _validate_config(self) -> None:
        """Validate WhatsApp Business configuration"""
        if not self.config.access_token:
            raise ValueError("WhatsApp Business access token is required")
        
        if not self.config.metadata.get('phone_number_id'):
            raise ValueError("WhatsApp Business phone number ID is required")
        
        # Set default features
        default_features = {
            'messaging': True,
            'templates': True,
            'media_messaging': True,
            'interactive_messages': True,
            'webhook_notifications': True,
            'business_profile': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize WhatsApp Business API client"""
        self.session = None
        self.headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json'
        }
        self.phone_number_id = self.config.metadata.get('phone_number_id')
        self.business_account_id = self.config.metadata.get('business_account_id')
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to WhatsApp Business API"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        session = await self._get_session()
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        
        try:
            self._record_request()
            async with session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    raise Exception("Rate limit exceeded")
                elif response.status == 401:
                    raise Exception("WhatsApp authentication failed")
                elif response.status == 403:
                    raise Exception("WhatsApp permission denied")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"WhatsApp API error: {error_msg}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"WhatsApp request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send WhatsApp message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="WhatsApp messaging is disabled"
                )
            
            # Validate phone number format
            recipient_phone = self._format_phone_number(request.recipient_id)
            if not recipient_phone:
                return MessageResponse(
                    success=False,
                    error="Invalid phone number format"
                )
            
            # Get recipient profile for personalization
            profile = await self.get_profile(request.recipient_id)
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            
            # Prepare message data
            message_data = {
                'messaging_product': 'whatsapp',
                'to': recipient_phone,
                'type': request.message_type or 'text'
            }
            
            # Handle different message types
            if request.message_type == 'template':
                message_data.update(self._prepare_template_message(request))
            elif request.message_type == 'interactive':
                message_data.update(self._prepare_interactive_message(request))
            elif request.message_type == 'media':
                message_data.update(self._prepare_media_message(request))
            else:
                # Default text message
                message_data['text'] = {
                    'body': personalized_content[:4096]  # WhatsApp message limit
                }
            
            # Send message
            endpoint = f"{self.phone_number_id}/messages"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            response = MessageResponse(
                success=True,
                message_id=message_id,
                external_id=response_data.get('messages', [{}])[0].get('id'),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'whatsapp',
                    'message_type': request.message_type,
                    'character_count': len(personalized_content),
                    'recipient_phone': recipient_phone
                }
            )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    def _format_phone_number(self, phone: str) -> Optional[str]:
        """Format phone number for WhatsApp API"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Must be between 10-15 digits
        if len(digits_only) < 10 or len(digits_only) > 15:
            return None
        
        # Add country code if not present (assuming US +1 if 10 digits)
        if len(digits_only) == 10:
            digits_only = '1' + digits_only
        
        return digits_only
    
    def _prepare_template_message(self, request: MessageRequest) -> Dict[str, Any]:
        """Prepare template message data"""
        template_data = request.metadata.get('template', {})
        
        return {
            'template': {
                'name': template_data.get('name'),
                'language': {
                    'code': template_data.get('language', 'en_US')
                },
                'components': template_data.get('components', [])
            }
        }
    
    def _prepare_interactive_message(self, request: MessageRequest) -> Dict[str, Any]:
        """Prepare interactive message data"""
        interactive_data = request.metadata.get('interactive', {})
        
        return {
            'interactive': {
                'type': interactive_data.get('type', 'button'),
                'body': {
                    'text': request.content[:1024]
                },
                'action': interactive_data.get('action', {})
            }
        }
    
    def _prepare_media_message(self, request: MessageRequest) -> Dict[str, Any]:
        """Prepare media message data"""
        media_data = request.metadata.get('media', {})
        media_type = media_data.get('type', 'image')
        
        message_data = {
            media_type: {
                'link': media_data.get('url'),
                'caption': request.content[:1024] if request.content else None
            }
        }
        
        return message_data
    
    async def get_profile(self, phone_number: str) -> Optional[ProfileData]:
        """Get WhatsApp profile information"""
        try:
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return None
            
            # WhatsApp Business API has limited profile access
            # Most profile data is not available due to privacy
            return ProfileData(
                user_id=formatted_phone,
                username=formatted_phone,
                display_name=f"WhatsApp User {formatted_phone[-4:]}",
                metadata={
                    'platform': 'whatsapp',
                    'phone_number': formatted_phone
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp profile: {str(e)}")
            return None
    
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for WhatsApp content"""
        try:
            # WhatsApp Business API provides limited analytics
            # This would typically be tracked through webhook events
            
            # Get message status if available
            endpoint = f"{content_id}"
            data = await self._make_request('GET', endpoint)
            
            return EngagementMetrics(
                views=1,  # Delivered messages are considered viewed
                metadata={
                    'platform': 'whatsapp',
                    'content_id': content_id,
                    'status': data.get('status', 'unknown')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp engagement metrics: {str(e)}")
            return None
    
    async def get_business_profile(self) -> Dict[str, Any]:
        """Get WhatsApp Business profile information"""
        try:
            endpoint = f"{self.phone_number_id}/whatsapp_business_profile"
            params = {
                'fields': 'about,address,description,email,profile_picture_url,websites,vertical'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [{}])[0] if data.get('data') else {}
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp business profile: {str(e)}")
            return {}
    
    async def update_business_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update WhatsApp Business profile"""
        try:
            endpoint = f"{self.phone_number_id}/whatsapp_business_profile"
            
            response_data = await self._make_request('POST', endpoint, json=profile_data)
            
            return {
                'success': True,
                'profile_id': response_data.get('id'),
                'platform': 'whatsapp'
            }
            
        except Exception as e:
            self.logger.error(f"Error updating WhatsApp business profile: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_message_templates(self) -> List[Dict[str, Any]]:
        """Get approved message templates"""
        try:
            endpoint = f"{self.business_account_id}/message_templates"
            params = {
                'fields': 'name,status,category,language,components'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp message templates: {str(e)}")
            return []
    
    async def create_message_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message template"""
        try:
            endpoint = f"{self.business_account_id}/message_templates"
            
            response_data = await self._make_request('POST', endpoint, json=template_data)
            
            return {
                'success': True,
                'template_id': response_data.get('id'),
                'status': response_data.get('status'),
                'platform': 'whatsapp'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating WhatsApp message template: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_phone_number_info(self) -> Dict[str, Any]:
        """Get phone number information and settings"""
        try:
            endpoint = f"{self.phone_number_id}"
            params = {
                'fields': 'display_phone_number,verified_name,code_verification_status,quality_rating'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp phone number info: {str(e)}")
            return {}
    
    async def set_webhook(self, webhook_url: str, verify_token: str) -> Dict[str, Any]:
        """Set up webhook for WhatsApp events"""
        try:
            # This is typically done through the Facebook App settings
            # But can be verified through the API
            
            webhook_data = {
                'callback_url': webhook_url,
                'verify_token': verify_token,
                'subscribed_fields': ['messages', 'message_deliveries', 'message_reads', 'message_echoes']
            }
            
            return {
                'success': True,
                'webhook_url': webhook_url,
                'platform': 'whatsapp'
            }
            
        except Exception as e:
            self.logger.error(f"Error setting WhatsApp webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_template_message(self, phone_number: str, template_name: str, 
                                  language: str = 'en_US', components: List[Dict] = None) -> MessageResponse:
        """Send a template message"""
        try:
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return MessageResponse(
                    success=False,
                    error="Invalid phone number format"
                )
            
            message_data = {
                'messaging_product': 'whatsapp',
                'to': formatted_phone,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': language},
                    'components': components or []
                }
            }
            
            endpoint = f"{self.phone_number_id}/messages"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            return MessageResponse(
                success=True,
                message_id=message_id,
                external_id=response_data.get('messages', [{}])[0].get('id'),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'whatsapp',
                    'message_type': 'template',
                    'template_name': template_name,
                    'recipient_phone': formatted_phone
                }
            )
            
        except Exception as e:
            return self._handle_api_error(e, "send_template_message")
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Get media URL from media ID"""
        try:
            endpoint = f"{media_id}"
            data = await self._make_request('GET', endpoint)
            return data.get('url')
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp media URL: {str(e)}")
            return None
    
    async def upload_media(self, file_path: str, media_type: str) -> Optional[str]:
        """Upload media file and get media ID"""
        try:
            endpoint = f"{self.phone_number_id}/media"
            
            # This would require multipart form data upload
            # Implementation depends on the specific file handling approach
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': file,
                    'type': media_type,
                    'messaging_product': 'whatsapp'
                }
                
                # Note: This is a simplified example
                # Actual implementation would use aiofiles and proper multipart handling
                response_data = await self._make_request('POST', endpoint, data=files)
                
                return response_data.get('id')
            
        except Exception as e:
            self.logger.error(f"Error uploading WhatsApp media: {str(e)}")
            return None
    
    async def get_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get WhatsApp Business analytics"""
        try:
            endpoint = f"{self.phone_number_id}/analytics"
            params = {
                'start': start_date,
                'end': end_date,
                'granularity': 'daily',
                'metric_types': ['sent', 'delivered', 'read', 'failed']
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('analytics', {})
            
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp analytics: {str(e)}")
            return {}
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This won't work in async context, but provides cleanup hint
            pass
