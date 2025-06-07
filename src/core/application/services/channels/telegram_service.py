"""
Telegram Channel Service

Provides Telegram integration for messaging, channel management, and bot automation.
Uses Telegram Bot API for automated messaging and group management.
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

class TelegramService(BaseChannelService):
    """Telegram channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://api.telegram.org"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.TELEGRAM
    
    def _validate_config(self) -> None:
        """Validate Telegram configuration"""
        if not self.config.api_key:
            raise ValueError("Telegram bot token is required")
        
        # Set default features
        default_features = {
            'messaging': True,
            'group_management': True,
            'channel_management': True,
            'inline_keyboards': True,
            'file_sharing': True,
            'webhook_support': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize Telegram Bot API client"""
        self.session = None
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.bot_token = self.config.api_key
        self.bot_username = self.config.metadata.get('bot_username')
    
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
        """Make authenticated request to Telegram Bot API"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        session = await self._get_session()
        url = f"{self.base_url}/bot{self.bot_token}/{endpoint}"
        
        try:
            self._record_request()
            async with session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    raise Exception("Rate limit exceeded")
                elif response.status == 401:
                    raise Exception("Telegram authentication failed")
                elif response.status == 403:
                    raise Exception("Telegram permission denied")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('description', 'Unknown error')
                    raise Exception(f"Telegram API error: {error_msg}")
                
                data = await response.json()
                if not data.get('ok'):
                    raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
                return data
        
        except aiohttp.ClientError as e:
            raise Exception(f"Telegram request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send Telegram message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="Telegram messaging is disabled"
                )
            
            # Get recipient profile for personalization
            profile = await self.get_profile(request.recipient_id)
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            
            # Prepare message data
            message_data = {
                'chat_id': request.recipient_id,
                'text': personalized_content[:4096],  # Telegram message limit
                'parse_mode': request.metadata.get('parse_mode', 'HTML')
            }
            
            # Add optional parameters
            if request.metadata.get('reply_markup'):
                message_data['reply_markup'] = json.dumps(request.metadata['reply_markup'])
            
            if request.metadata.get('disable_web_page_preview'):
                message_data['disable_web_page_preview'] = True
            
            if request.metadata.get('disable_notification'):
                message_data['disable_notification'] = True
            
            # Send message
            endpoint = "sendMessage"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            response = MessageResponse(
                success=True,
                message_id=message_id,
                external_id=str(response_data.get('result', {}).get('message_id')),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'telegram',
                    'message_type': request.message_type,
                    'character_count': len(personalized_content),
                    'chat_id': request.recipient_id,
                    'telegram_message_id': response_data.get('result', {}).get('message_id')
                }
            )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Get Telegram user/chat information"""
        try:
            if user_id == "me":
                # Get bot info
                endpoint = "getMe"
                data = await self._make_request('GET', endpoint)
                bot_info = data.get('result', {})
                
                return ProfileData(
                    user_id=str(bot_info.get('id')),
                    username=bot_info.get('username'),
                    display_name=f"{bot_info.get('first_name', '')} {bot_info.get('last_name', '')}".strip(),
                    verified=bot_info.get('is_bot', False),
                    metadata={
                        'platform': 'telegram',
                        'is_bot': bot_info.get('is_bot'),
                        'can_join_groups': bot_info.get('can_join_groups'),
                        'can_read_all_group_messages': bot_info.get('can_read_all_group_messages'),
                        'supports_inline_queries': bot_info.get('supports_inline_queries')
                    }
                )
            else:
                # Get chat info
                endpoint = "getChat"
                params = {'chat_id': user_id}
                
                data = await self._make_request('GET', endpoint, params=params)
                chat_info = data.get('result', {})
                
                return ProfileData(
                    user_id=str(chat_info.get('id')),
                    username=chat_info.get('username'),
                    display_name=self._get_display_name(chat_info),
                    bio=chat_info.get('description'),
                    follower_count=chat_info.get('member_count') if chat_info.get('type') in ['group', 'supergroup', 'channel'] else None,
                    profile_url=f"https://t.me/{chat_info.get('username')}" if chat_info.get('username') else None,
                    metadata={
                        'platform': 'telegram',
                        'chat_type': chat_info.get('type'),
                        'invite_link': chat_info.get('invite_link'),
                        'pinned_message': chat_info.get('pinned_message'),
                        'permissions': chat_info.get('permissions'),
                        'slow_mode_delay': chat_info.get('slow_mode_delay')
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error getting Telegram profile: {str(e)}")
            return None
    
    def _get_display_name(self, chat_info: Dict[str, Any]) -> str:
        """Extract display name from chat info"""
        if chat_info.get('title'):
            return chat_info['title']
        
        first_name = chat_info.get('first_name', '')
        last_name = chat_info.get('last_name', '')
        return f"{first_name} {last_name}".strip() or chat_info.get('username', 'Unknown')
    
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for Telegram content (limited)"""
        try:
            # Telegram doesn't provide detailed engagement metrics through Bot API
            # This would require Telegram Analytics API or manual tracking
            
            return EngagementMetrics(
                views=0,  # Not available through Bot API
                likes=0,  # Telegram doesn't have likes
                comments=0,  # Would need to track replies manually
                shares=0,  # Would need to track forwards manually
                metadata={
                    'platform': 'telegram',
                    'content_id': content_id,
                    'note': 'Limited metrics available through Bot API'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Telegram engagement metrics: {str(e)}")
            return None
    
    async def send_photo(self, chat_id: str, photo_url: str, caption: str = "") -> MessageResponse:
        """Send photo message"""
        try:
            message_data = {
                'chat_id': chat_id,
                'photo': photo_url,
                'caption': caption[:1024] if caption else ""  # Caption limit
            }
            
            endpoint = "sendPhoto"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            return MessageResponse(
                success=True,
                message_id=message_id,
                external_id=str(response_data.get('result', {}).get('message_id')),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'telegram',
                    'message_type': 'photo',
                    'chat_id': chat_id
                }
            )
            
        except Exception as e:
            return self._handle_api_error(e, "send_photo")
    
    async def send_document(self, chat_id: str, document_url: str, caption: str = "") -> MessageResponse:
        """Send document message"""
        try:
            message_data = {
                'chat_id': chat_id,
                'document': document_url,
                'caption': caption[:1024] if caption else ""
            }
            
            endpoint = "sendDocument"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            return MessageResponse(
                success=True,
                message_id=message_id,
                external_id=str(response_data.get('result', {}).get('message_id')),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'telegram',
                    'message_type': 'document',
                    'chat_id': chat_id
                }
            )
            
        except Exception as e:
            return self._handle_api_error(e, "send_document")
    
    async def create_inline_keyboard(self, buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
        """Create inline keyboard markup"""
        return {
            'inline_keyboard': buttons
        }
    
    async def send_message_with_keyboard(self, chat_id: str, text: str, 
                                       keyboard: Dict[str, Any]) -> MessageResponse:
        """Send message with inline keyboard"""
        try:
            message_data = {
                'chat_id': chat_id,
                'text': text[:4096],
                'reply_markup': json.dumps(keyboard)
            }
            
            endpoint = "sendMessage"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            return MessageResponse(
                success=True,
                message_id=message_id,
                external_id=str(response_data.get('result', {}).get('message_id')),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'telegram',
                    'message_type': 'keyboard',
                    'chat_id': chat_id
                }
            )
            
        except Exception as e:
            return self._handle_api_error(e, "send_message_with_keyboard")
    
    async def get_chat_members_count(self, chat_id: str) -> int:
        """Get number of members in a chat"""
        try:
            endpoint = "getChatMemberCount"
            params = {'chat_id': chat_id}
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('result', 0)
            
        except Exception as e:
            self.logger.error(f"Error getting Telegram chat members count: {str(e)}")
            return 0
    
    async def get_chat_administrators(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get chat administrators"""
        try:
            endpoint = "getChatAdministrators"
            params = {'chat_id': chat_id}
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('result', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Telegram chat administrators: {str(e)}")
            return []
    
    async def set_webhook(self, webhook_url: str, secret_token: str = None) -> Dict[str, Any]:
        """Set webhook for receiving updates"""
        try:
            webhook_data = {
                'url': webhook_url,
                'max_connections': 40,
                'allowed_updates': ['message', 'callback_query', 'inline_query']
            }
            
            if secret_token:
                webhook_data['secret_token'] = secret_token
            
            endpoint = "setWebhook"
            response_data = await self._make_request('POST', endpoint, json=webhook_data)
            
            return {
                'success': True,
                'webhook_url': webhook_url,
                'platform': 'telegram',
                'description': response_data.get('description')
            }
            
        except Exception as e:
            self.logger.error(f"Error setting Telegram webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def delete_webhook(self) -> Dict[str, Any]:
        """Delete webhook"""
        try:
            endpoint = "deleteWebhook"
            response_data = await self._make_request('POST', endpoint)
            
            return {
                'success': True,
                'platform': 'telegram',
                'description': response_data.get('description')
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting Telegram webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook information"""
        try:
            endpoint = "getWebhookInfo"
            data = await self._make_request('GET', endpoint)
            
            return data.get('result', {})
            
        except Exception as e:
            self.logger.error(f"Error getting Telegram webhook info: {str(e)}")
            return {}
    
    async def send_broadcast_message(self, chat_ids: List[str], message: str, 
                                   delay_between_messages: float = 0.1) -> Dict[str, Any]:
        """Send broadcast message to multiple chats"""
        try:
            successful_sends = 0
            failed_sends = 0
            results = []
            
            for chat_id in chat_ids:
                try:
                    request = MessageRequest(
                        recipient_id=chat_id,
                        content=message
                    )
                    
                    response = await self.send_message(request)
                    
                    if response.success:
                        successful_sends += 1
                    else:
                        failed_sends += 1
                    
                    results.append({
                        'chat_id': chat_id,
                        'success': response.success,
                        'error': response.error
                    })
                    
                    # Add delay to avoid rate limiting
                    if delay_between_messages > 0:
                        await asyncio.sleep(delay_between_messages)
                        
                except Exception as e:
                    failed_sends += 1
                    results.append({
                        'chat_id': chat_id,
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'total_chats': len(chat_ids),
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'success_rate': (successful_sends / len(chat_ids)) * 100 if chat_ids else 0,
                'results': results,
                'platform': 'telegram'
            }
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram broadcast: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_chat_invite_link(self, chat_id: str, expire_date: int = None, 
                                    member_limit: int = None) -> Dict[str, Any]:
        """Create chat invite link"""
        try:
            link_data = {'chat_id': chat_id}
            
            if expire_date:
                link_data['expire_date'] = expire_date
            
            if member_limit:
                link_data['member_limit'] = member_limit
            
            endpoint = "createChatInviteLink"
            response_data = await self._make_request('POST', endpoint, json=link_data)
            
            return {
                'success': True,
                'invite_link': response_data.get('result', {}).get('invite_link'),
                'platform': 'telegram'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Telegram chat invite link: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def ban_chat_member(self, chat_id: str, user_id: str, until_date: int = None) -> Dict[str, Any]:
        """Ban a chat member"""
        try:
            ban_data = {
                'chat_id': chat_id,
                'user_id': user_id
            }
            
            if until_date:
                ban_data['until_date'] = until_date
            
            endpoint = "banChatMember"
            response_data = await self._make_request('POST', endpoint, json=ban_data)
            
            return {
                'success': True,
                'platform': 'telegram',
                'description': response_data.get('description')
            }
            
        except Exception as e:
            self.logger.error(f"Error banning Telegram chat member: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def unban_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Unban a chat member"""
        try:
            unban_data = {
                'chat_id': chat_id,
                'user_id': user_id,
                'only_if_banned': True
            }
            
            endpoint = "unbanChatMember"
            response_data = await self._make_request('POST', endpoint, json=unban_data)
            
            return {
                'success': True,
                'platform': 'telegram',
                'description': response_data.get('description')
            }
            
        except Exception as e:
            self.logger.error(f"Error unbanning Telegram chat member: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_updates(self, offset: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get updates (messages, callbacks, etc.)"""
        try:
            params = {'limit': min(limit, 100)}
            
            if offset:
                params['offset'] = offset
            
            endpoint = "getUpdates"
            data = await self._make_request('GET', endpoint, params=params)
            
            return data.get('result', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Telegram updates: {str(e)}")
            return []
    
    async def answer_callback_query(self, callback_query_id: str, text: str = "", 
                                  show_alert: bool = False) -> Dict[str, Any]:
        """Answer callback query from inline keyboard"""
        try:
            answer_data = {
                'callback_query_id': callback_query_id,
                'text': text[:200],  # Callback answer text limit
                'show_alert': show_alert
            }
            
            endpoint = "answerCallbackQuery"
            response_data = await self._make_request('POST', endpoint, json=answer_data)
            
            return {
                'success': True,
                'platform': 'telegram'
            }
            
        except Exception as e:
            self.logger.error(f"Error answering Telegram callback query: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def edit_message_text(self, chat_id: str, message_id: str, new_text: str, 
                              reply_markup: Dict[str, Any] = None) -> Dict[str, Any]:
        """Edit message text"""
        try:
            edit_data = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': new_text[:4096]
            }
            
            if reply_markup:
                edit_data['reply_markup'] = json.dumps(reply_markup)
            
            endpoint = "editMessageText"
            response_data = await self._make_request('POST', endpoint, json=edit_data)
            
            return {
                'success': True,
                'platform': 'telegram'
            }
            
        except Exception as e:
            self.logger.error(f"Error editing Telegram message: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This won't work in async context, but provides cleanup hint
            pass
