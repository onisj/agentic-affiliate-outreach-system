"""
Discord Channel Service

Provides Discord integration for server management, messaging, and community engagement.
Uses Discord Bot API for automated messaging and server analytics.
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

class DiscordService(BaseChannelService):
    """Discord channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://discord.com/api/v10"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.DISCORD
    
    def _validate_config(self) -> None:
        """Validate Discord configuration"""
        if not self.config.api_key:
            raise ValueError("Discord bot token is required")
        
        # Set default features
        default_features = {
            'messaging': True,
            'server_management': True,
            'channel_management': True,
            'role_management': True,
            'embed_messages': True,
            'slash_commands': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize Discord Bot API client"""
        self.session = None
        self.headers = {
            'Authorization': f'Bot {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AffiliateOutreach (https://github.com/affiliate-outreach, 1.0)'
        }
        self.bot_token = self.config.api_key
    
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
        """Make authenticated request to Discord API"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        try:
            self._record_request()
            async with session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    # Discord rate limiting
                    retry_after = response.headers.get('Retry-After', '1')
                    raise Exception(f"Rate limit exceeded. Retry after {retry_after} seconds")
                elif response.status == 401:
                    raise Exception("Discord authentication failed")
                elif response.status == 403:
                    raise Exception("Discord permission denied")
                elif response.status == 404:
                    raise Exception("Discord resource not found")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                    raise Exception(f"Discord API error: {error_msg}")
                
                if response.status == 204:
                    return {}  # No content response
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"Discord request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send Discord message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="Discord messaging is disabled"
                )
            
            # Get recipient profile for personalization
            profile = await self.get_profile(request.recipient_id)
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            
            # Prepare message data
            message_data = {
                'content': personalized_content[:2000]  # Discord message limit
            }
            
            # Add embeds if specified
            if request.metadata.get('embeds'):
                message_data['embeds'] = request.metadata['embeds']
            
            # Add components (buttons, select menus) if specified
            if request.metadata.get('components'):
                message_data['components'] = request.metadata['components']
            
            # Determine if it's a DM or channel message
            if request.recipient_id.startswith('dm_'):
                # Direct message - need to create DM channel first
                user_id = request.recipient_id[3:]  # Remove 'dm_' prefix
                dm_channel = await self._create_dm_channel(user_id)
                if not dm_channel:
                    return MessageResponse(
                        success=False,
                        error="Failed to create DM channel"
                    )
                channel_id = dm_channel['id']
            else:
                # Channel message
                channel_id = request.recipient_id
            
            # Send message
            endpoint = f"channels/{channel_id}/messages"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            response = MessageResponse(
                success=True,
                message_id=message_id,
                external_id=response_data.get('id'),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'discord',
                    'message_type': request.message_type,
                    'character_count': len(personalized_content),
                    'channel_id': channel_id,
                    'discord_message_id': response_data.get('id')
                }
            )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    async def _create_dm_channel(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Create a DM channel with a user"""
        try:
            endpoint = "users/@me/channels"
            data = {'recipient_id': user_id}
            
            response = await self._make_request('POST', endpoint, json=data)
            return response
            
        except Exception as e:
            self.logger.error(f"Error creating Discord DM channel: {str(e)}")
            return None
    
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Get Discord user information"""
        try:
            if user_id == "me":
                endpoint = "users/@me"
            else:
                endpoint = f"users/{user_id}"
            
            data = await self._make_request('GET', endpoint)
            
            if not data:
                return None
            
            return ProfileData(
                user_id=data.get('id'),
                username=data.get('username'),
                display_name=data.get('global_name') or data.get('username'),
                bio=data.get('bio'),
                verified=data.get('verified', False),
                profile_url=f"https://discord.com/users/{data.get('id')}",
                avatar_url=self._get_avatar_url(data),
                metadata={
                    'platform': 'discord',
                    'discriminator': data.get('discriminator'),
                    'bot': data.get('bot', False),
                    'system': data.get('system', False),
                    'mfa_enabled': data.get('mfa_enabled', False),
                    'banner': data.get('banner'),
                    'accent_color': data.get('accent_color'),
                    'locale': data.get('locale'),
                    'flags': data.get('flags', 0),
                    'premium_type': data.get('premium_type', 0),
                    'public_flags': data.get('public_flags', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Discord profile: {str(e)}")
            return None
    
    def _get_avatar_url(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Generate avatar URL from user data"""
        user_id = user_data.get('id')
        avatar_hash = user_data.get('avatar')
        
        if avatar_hash:
            return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
        else:
            # Default avatar
            discriminator = user_data.get('discriminator', '0')
            default_avatar = int(discriminator) % 5
            return f"https://cdn.discordapp.com/embed/avatars/{default_avatar}.png"
    
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for Discord message (limited)"""
        try:
            # Discord doesn't provide detailed engagement metrics through API
            # This would require tracking reactions and replies manually
            
            # Try to get message reactions if available
            if '_' in content_id:
                channel_id, message_id = content_id.split('_', 1)
                endpoint = f"channels/{channel_id}/messages/{message_id}"
                
                message_data = await self._make_request('GET', endpoint)
                
                reactions = message_data.get('reactions', [])
                total_reactions = sum(reaction.get('count', 0) for reaction in reactions)
                
                return EngagementMetrics(
                    views=0,  # Not available through Discord API
                    likes=total_reactions,
                    comments=0,  # Would need to track replies manually
                    shares=0,  # Discord doesn't have shares
                    metadata={
                        'platform': 'discord',
                        'content_id': content_id,
                        'reactions': reactions,
                        'total_reactions': total_reactions,
                        'message_type': message_data.get('type', 0)
                    }
                )
            
            return EngagementMetrics(
                views=0,
                likes=0,
                comments=0,
                shares=0,
                metadata={
                    'platform': 'discord',
                    'content_id': content_id,
                    'note': 'Limited metrics available through Discord API'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Discord engagement metrics: {str(e)}")
            return None
    
    async def get_guild_info(self, guild_id: str) -> Dict[str, Any]:
        """Get Discord server (guild) information"""
        try:
            endpoint = f"guilds/{guild_id}"
            data = await self._make_request('GET', endpoint)
            
            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'description': data.get('description'),
                'icon': data.get('icon'),
                'splash': data.get('splash'),
                'banner': data.get('banner'),
                'owner_id': data.get('owner_id'),
                'member_count': data.get('approximate_member_count'),
                'presence_count': data.get('approximate_presence_count'),
                'max_members': data.get('max_members'),
                'verification_level': data.get('verification_level'),
                'nsfw_level': data.get('nsfw_level'),
                'premium_tier': data.get('premium_tier'),
                'premium_subscription_count': data.get('premium_subscription_count'),
                'features': data.get('features', []),
                'vanity_url_code': data.get('vanity_url_code'),
                'platform': 'discord'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Discord guild info: {str(e)}")
            return {}
    
    async def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get channels in a Discord server"""
        try:
            endpoint = f"guilds/{guild_id}/channels"
            data = await self._make_request('GET', endpoint)
            
            channels = []
            for channel in data:
                channel_info = {
                    'id': channel.get('id'),
                    'name': channel.get('name'),
                    'type': channel.get('type'),
                    'position': channel.get('position'),
                    'topic': channel.get('topic'),
                    'nsfw': channel.get('nsfw', False),
                    'parent_id': channel.get('parent_id'),
                    'permission_overwrites': channel.get('permission_overwrites', [])
                }
                channels.append(channel_info)
            
            return channels
            
        except Exception as e:
            self.logger.error(f"Error getting Discord guild channels: {str(e)}")
            return []
    
    async def get_guild_members(self, guild_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get members in a Discord server"""
        try:
            endpoint = f"guilds/{guild_id}/members"
            params = {'limit': min(limit, 1000)}
            
            data = await self._make_request('GET', endpoint, params=params)
            
            members = []
            for member in data:
                user = member.get('user', {})
                member_info = {
                    'user_id': user.get('id'),
                    'username': user.get('username'),
                    'discriminator': user.get('discriminator'),
                    'avatar': user.get('avatar'),
                    'nick': member.get('nick'),
                    'roles': member.get('roles', []),
                    'joined_at': member.get('joined_at'),
                    'premium_since': member.get('premium_since'),
                    'deaf': member.get('deaf', False),
                    'mute': member.get('mute', False),
                    'pending': member.get('pending', False)
                }
                members.append(member_info)
            
            return members
            
        except Exception as e:
            self.logger.error(f"Error getting Discord guild members: {str(e)}")
            return []
    
    async def create_embed(self, title: str, description: str, color: int = 0x00ff00, 
                         fields: List[Dict[str, Any]] = None, 
                         footer: Dict[str, str] = None,
                         thumbnail: str = None,
                         image: str = None) -> Dict[str, Any]:
        """Create a Discord embed"""
        embed = {
            'title': title[:256],  # Discord title limit
            'description': description[:4096],  # Discord description limit
            'color': color,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if fields:
            embed['fields'] = fields[:25]  # Discord field limit
        
        if footer:
            embed['footer'] = footer
        
        if thumbnail:
            embed['thumbnail'] = {'url': thumbnail}
        
        if image:
            embed['image'] = {'url': image}
        
        return embed
    
    async def send_embed_message(self, channel_id: str, embed: Dict[str, Any], 
                               content: str = "") -> MessageResponse:
        """Send message with embed"""
        try:
            message_data = {
                'embeds': [embed]
            }
            
            if content:
                message_data['content'] = content[:2000]
            
            endpoint = f"channels/{channel_id}/messages"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            return MessageResponse(
                success=True,
                message_id=message_id,
                external_id=response_data.get('id'),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'discord',
                    'message_type': 'embed',
                    'channel_id': channel_id
                }
            )
            
        except Exception as e:
            return self._handle_api_error(e, "send_embed_message")
    
    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> Dict[str, Any]:
        """Add reaction to a message"""
        try:
            endpoint = f"channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
            await self._make_request('PUT', endpoint)
            
            return {
                'success': True,
                'platform': 'discord'
            }
            
        except Exception as e:
            self.logger.error(f"Error adding Discord reaction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_thread(self, channel_id: str, name: str, message_id: str = None, 
                          auto_archive_duration: int = 1440) -> Dict[str, Any]:
        """Create a thread in a channel"""
        try:
            if message_id:
                # Create thread from message
                endpoint = f"channels/{channel_id}/messages/{message_id}/threads"
                thread_data = {
                    'name': name[:100],  # Discord thread name limit
                    'auto_archive_duration': auto_archive_duration
                }
            else:
                # Create thread without message
                endpoint = f"channels/{channel_id}/threads"
                thread_data = {
                    'name': name[:100],
                    'auto_archive_duration': auto_archive_duration,
                    'type': 11  # PUBLIC_THREAD
                }
            
            response_data = await self._make_request('POST', endpoint, json=thread_data)
            
            return {
                'success': True,
                'thread_id': response_data.get('id'),
                'thread_name': response_data.get('name'),
                'platform': 'discord'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Discord thread: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_channel_messages(self, channel_id: str, limit: int = 50, 
                                 before: str = None, after: str = None) -> List[Dict[str, Any]]:
        """Get messages from a channel"""
        try:
            endpoint = f"channels/{channel_id}/messages"
            params = {'limit': min(limit, 100)}
            
            if before:
                params['before'] = before
            if after:
                params['after'] = after
            
            data = await self._make_request('GET', endpoint, params=params)
            
            messages = []
            for message in data:
                message_info = {
                    'id': message.get('id'),
                    'content': message.get('content'),
                    'author': message.get('author', {}),
                    'timestamp': message.get('timestamp'),
                    'edited_timestamp': message.get('edited_timestamp'),
                    'tts': message.get('tts', False),
                    'mention_everyone': message.get('mention_everyone', False),
                    'mentions': message.get('mentions', []),
                    'attachments': message.get('attachments', []),
                    'embeds': message.get('embeds', []),
                    'reactions': message.get('reactions', []),
                    'pinned': message.get('pinned', False),
                    'type': message.get('type', 0)
                }
                messages.append(message_info)
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error getting Discord channel messages: {str(e)}")
            return []
    
    async def ban_member(self, guild_id: str, user_id: str, reason: str = None, 
                        delete_message_days: int = 0) -> Dict[str, Any]:
        """Ban a member from a server"""
        try:
            endpoint = f"guilds/{guild_id}/bans/{user_id}"
            ban_data = {
                'delete_message_days': min(delete_message_days, 7)
            }
            
            if reason:
                ban_data['reason'] = reason[:512]  # Discord reason limit
            
            await self._make_request('PUT', endpoint, json=ban_data)
            
            return {
                'success': True,
                'platform': 'discord'
            }
            
        except Exception as e:
            self.logger.error(f"Error banning Discord member: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def kick_member(self, guild_id: str, user_id: str, reason: str = None) -> Dict[str, Any]:
        """Kick a member from a server"""
        try:
            endpoint = f"guilds/{guild_id}/members/{user_id}"
            headers = {}
            
            if reason:
                headers['X-Audit-Log-Reason'] = reason[:512]
            
            await self._make_request('DELETE', endpoint, headers=headers)
            
            return {
                'success': True,
                'platform': 'discord'
            }
            
        except Exception as e:
            self.logger.error(f"Error kicking Discord member: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_invite(self, channel_id: str, max_age: int = 86400, 
                          max_uses: int = 0, temporary: bool = False) -> Dict[str, Any]:
        """Create an invite for a channel"""
        try:
            endpoint = f"channels/{channel_id}/invites"
            invite_data = {
                'max_age': max_age,
                'max_uses': max_uses,
                'temporary': temporary,
                'unique': True
            }
            
            response_data = await self._make_request('POST', endpoint, json=invite_data)
            
            return {
                'success': True,
                'invite_code': response_data.get('code'),
                'invite_url': f"https://discord.gg/{response_data.get('code')}",
                'platform': 'discord'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Discord invite: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_server_activity(self, guild_id: str) -> Dict[str, Any]:
        """Analyze server activity and engagement"""
        try:
            # Get server info
            guild_info = await self.get_guild_info(guild_id)
            
            # Get channels
            channels = await self.get_guild_channels(guild_id)
            
            # Get recent messages from active channels
            text_channels = [ch for ch in channels if ch.get('type') == 0]  # Text channels
            
            total_messages = 0
            active_channels = 0
            
            for channel in text_channels[:10]:  # Limit to first 10 channels
                try:
                    messages = await self.get_channel_messages(channel['id'], limit=50)
                    if messages:
                        total_messages += len(messages)
                        active_channels += 1
                except:
                    continue  # Skip channels we can't access
            
            return {
                'guild_info': guild_info,
                'channel_stats': {
                    'total_channels': len(channels),
                    'text_channels': len(text_channels),
                    'active_channels': active_channels
                },
                'activity_stats': {
                    'recent_messages': total_messages,
                    'avg_messages_per_channel': total_messages / active_channels if active_channels > 0 else 0
                },
                'platform': 'discord',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Discord server activity: {str(e)}")
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
