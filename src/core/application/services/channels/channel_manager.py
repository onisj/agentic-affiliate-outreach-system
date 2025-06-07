"""
Channel Manager

Centralized manager for all channel services, providing unified interface
for multi-channel outreach campaigns and analytics.
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from .base_channel import (
    BaseChannelService, ChannelType, ChannelConfig, MessageRequest, 
    MessageResponse, ProfileData, EngagementMetrics
)
from .instagram_service import InstagramService
from .facebook_service import FacebookService
from .whatsapp_service import WhatsAppService
from .youtube_service import YouTubeService
from .tiktok_service import TikTokService
from .telegram_service import TelegramService
from .reddit_service import RedditService
from .discord_service import DiscordService
from .email_enhanced import EnhancedEmailService

logger = logging.getLogger(__name__)

class ChannelManager:
    """Manages all channel services and provides unified interface"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.channels: Dict[ChannelType, BaseChannelService] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_channel(self, channel_type: ChannelType, config: ChannelConfig) -> bool:
        """Register a channel service with configuration"""
        try:
            service_class = self._get_service_class(channel_type)
            if not service_class:
                self.logger.error(f"No service class found for channel type: {channel_type}")
                return False
            
            service = service_class(config, self.db)
            self.channels[channel_type] = service
            
            self.logger.info(f"Successfully registered {channel_type.value} channel")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register {channel_type.value} channel: {str(e)}")
            return False
    
    def _get_service_class(self, channel_type: ChannelType) -> Optional[type]:
        """Get the service class for a channel type"""
        service_map = {
            ChannelType.EMAIL: EnhancedEmailService,
            ChannelType.INSTAGRAM: InstagramService,
            ChannelType.FACEBOOK: FacebookService,
            ChannelType.WHATSAPP: WhatsAppService,
            ChannelType.YOUTUBE: YouTubeService,
            ChannelType.TIKTOK: TikTokService,
            ChannelType.TELEGRAM: TelegramService,
            ChannelType.REDDIT: RedditService,
            ChannelType.DISCORD: DiscordService,
        }
        return service_map.get(channel_type)
    
    def get_channel(self, channel_type: ChannelType) -> Optional[BaseChannelService]:
        """Get a registered channel service"""
        return self.channels.get(channel_type)
    
    def get_available_channels(self) -> List[ChannelType]:
        """Get list of available channel types"""
        return list(self.channels.keys())
    
    def is_channel_available(self, channel_type: ChannelType) -> bool:
        """Check if a channel is available and enabled"""
        channel = self.channels.get(channel_type)
        return channel is not None and channel.config.enabled
    
    async def send_message(self, channel_type: ChannelType, request: MessageRequest) -> MessageResponse:
        """Send message through specific channel"""
        try:
            channel = self.get_channel(channel_type)
            if not channel:
                return MessageResponse(
                    success=False,
                    error=f"Channel {channel_type.value} not available"
                )
            
            if not channel.config.enabled:
                return MessageResponse(
                    success=False,
                    error=f"Channel {channel_type.value} is disabled"
                )
            
            return await channel.send_message(request)
            
        except Exception as e:
            self.logger.error(f"Error sending message via {channel_type.value}: {str(e)}")
            return MessageResponse(
                success=False,
                error=f"Failed to send message: {str(e)}"
            )
    
    async def send_multi_channel_message(self, channel_types: List[ChannelType], 
                                       request: MessageRequest) -> Dict[ChannelType, MessageResponse]:
        """Send message through multiple channels"""
        results = {}
        
        # Send messages concurrently
        tasks = []
        for channel_type in channel_types:
            if self.is_channel_available(channel_type):
                task = self.send_message(channel_type, request)
                tasks.append((channel_type, task))
        
        # Wait for all tasks to complete
        for channel_type, task in tasks:
            try:
                response = await task
                results[channel_type] = response
            except Exception as e:
                results[channel_type] = MessageResponse(
                    success=False,
                    error=f"Task failed: {str(e)}"
                )
        
        return results
    
    async def get_profile(self, channel_type: ChannelType, user_id: str) -> Optional[ProfileData]:
        """Get profile from specific channel"""
        try:
            channel = self.get_channel(channel_type)
            if not channel:
                return None
            
            return await channel.get_profile(user_id)
            
        except Exception as e:
            self.logger.error(f"Error getting profile from {channel_type.value}: {str(e)}")
            return None
    
    async def get_multi_channel_profile(self, user_identifiers: Dict[ChannelType, str]) -> Dict[ChannelType, Optional[ProfileData]]:
        """Get profile data from multiple channels"""
        results = {}
        
        # Get profiles concurrently
        tasks = []
        for channel_type, user_id in user_identifiers.items():
            if self.is_channel_available(channel_type):
                task = self.get_profile(channel_type, user_id)
                tasks.append((channel_type, task))
        
        # Wait for all tasks to complete
        for channel_type, task in tasks:
            try:
                profile = await task
                results[channel_type] = profile
            except Exception as e:
                self.logger.error(f"Failed to get profile from {channel_type.value}: {str(e)}")
                results[channel_type] = None
        
        return results
    
    async def get_engagement_metrics(self, channel_type: ChannelType, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics from specific channel"""
        try:
            channel = self.get_channel(channel_type)
            if not channel:
                return None
            
            return await channel.get_engagement_metrics(content_id)
            
        except Exception as e:
            self.logger.error(f"Error getting engagement metrics from {channel_type.value}: {str(e)}")
            return None
    
    async def test_all_connections(self) -> Dict[ChannelType, Dict[str, Any]]:
        """Test connections to all registered channels"""
        results = {}
        
        # Test connections concurrently
        tasks = []
        for channel_type, channel in self.channels.items():
            if channel.config.enabled:
                task = channel.test_connection()
                tasks.append((channel_type, task))
        
        # Wait for all tasks to complete
        for channel_type, task in tasks:
            try:
                result = await task
                results[channel_type] = result
            except Exception as e:
                results[channel_type] = {
                    'success': False,
                    'channel': channel_type.value,
                    'error': str(e)
                }
        
        return results
    
    def get_channel_info(self, channel_type: ChannelType = None) -> Union[Dict[str, Any], Dict[ChannelType, Dict[str, Any]]]:
        """Get information about channels"""
        if channel_type:
            channel = self.get_channel(channel_type)
            return channel.get_channel_info() if channel else {}
        
        # Return info for all channels
        info = {}
        for ch_type, channel in self.channels.items():
            info[ch_type] = channel.get_channel_info()
        
        return info
    
    async def run_campaign(self, campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a multi-channel outreach campaign"""
        try:
            campaign_id = campaign_config.get('campaign_id', f"campaign_{datetime.now().timestamp()}")
            channels = campaign_config.get('channels', [])
            recipients = campaign_config.get('recipients', [])
            message_template = campaign_config.get('message_template', {})
            delay_between_messages = campaign_config.get('delay_between_messages', 1.0)
            
            results = {
                'campaign_id': campaign_id,
                'total_recipients': len(recipients),
                'channels_used': channels,
                'results': [],
                'summary': {
                    'total_sent': 0,
                    'total_failed': 0,
                    'success_rate': 0.0
                }
            }
            
            # Process each recipient
            for recipient in recipients:
                recipient_results = {}
                
                # Create message request
                request = MessageRequest(
                    recipient_id=recipient.get('id'),
                    content=message_template.get('content', ''),
                    subject=message_template.get('subject'),
                    message_type=message_template.get('type', 'text'),
                    campaign_id=campaign_id,
                    metadata=message_template.get('metadata', {})
                )
                
                # Send through specified channels
                channel_types = [ChannelType(ch) for ch in channels if ch in [ct.value for ct in ChannelType]]
                responses = await self.send_multi_channel_message(channel_types, request)
                
                # Process responses
                for channel_type, response in responses.items():
                    recipient_results[channel_type.value] = {
                        'success': response.success,
                        'message_id': response.message_id,
                        'error': response.error,
                        'status': response.status.value if response.status else None
                    }
                    
                    if response.success:
                        results['summary']['total_sent'] += 1
                    else:
                        results['summary']['total_failed'] += 1
                
                results['results'].append({
                    'recipient': recipient,
                    'channels': recipient_results
                })
                
                # Add delay between recipients
                if delay_between_messages > 0:
                    await asyncio.sleep(delay_between_messages)
            
            # Calculate success rate
            total_attempts = results['summary']['total_sent'] + results['summary']['total_failed']
            if total_attempts > 0:
                results['summary']['success_rate'] = (results['summary']['total_sent'] / total_attempts) * 100
            
            results['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error running campaign: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'campaign_id': campaign_config.get('campaign_id', 'unknown')
            }
    
    async def analyze_cross_platform_engagement(self, content_identifiers: Dict[ChannelType, str]) -> Dict[str, Any]:
        """Analyze engagement across multiple platforms"""
        try:
            platform_metrics = {}
            total_views = 0
            total_likes = 0
            total_comments = 0
            total_shares = 0
            
            # Get metrics from each platform
            for channel_type, content_id in content_identifiers.items():
                metrics = await self.get_engagement_metrics(channel_type, content_id)
                if metrics:
                    platform_metrics[channel_type.value] = {
                        'views': metrics.views,
                        'likes': metrics.likes,
                        'comments': metrics.comments,
                        'shares': metrics.shares,
                        'engagement_rate': metrics.engagement_rate,
                        'metadata': metrics.metadata
                    }
                    
                    total_views += metrics.views
                    total_likes += metrics.likes
                    total_comments += metrics.comments
                    total_shares += metrics.shares
            
            # Calculate cross-platform metrics
            total_engagement = total_likes + total_comments + total_shares
            overall_engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0
            
            # Find best performing platform
            best_platform = None
            best_engagement_rate = 0
            
            for platform, metrics in platform_metrics.items():
                if metrics['engagement_rate'] > best_engagement_rate:
                    best_engagement_rate = metrics['engagement_rate']
                    best_platform = platform
            
            return {
                'cross_platform_summary': {
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'total_engagement': total_engagement,
                    'overall_engagement_rate': overall_engagement_rate,
                    'platforms_analyzed': len(platform_metrics),
                    'best_performing_platform': best_platform
                },
                'platform_breakdown': platform_metrics,
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cross-platform engagement: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def discover_prospects(self, discovery_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover prospects across multiple platforms"""
        try:
            keywords = discovery_config.get('keywords', [])
            channels = discovery_config.get('channels', [])
            filters = discovery_config.get('filters', {})
            
            all_prospects = {}
            
            # Search each platform
            for channel_name in channels:
                try:
                    channel_type = ChannelType(channel_name)
                    channel = self.get_channel(channel_type)
                    
                    if not channel:
                        continue
                    
                    prospects = []
                    
                    # Platform-specific discovery
                    if channel_type == ChannelType.YOUTUBE:
                        for keyword in keywords:
                            channels_found = await channel.search_channels(keyword, max_results=50)
                            prospects.extend(channels_found)
                    
                    elif channel_type == ChannelType.REDDIT:
                        subreddits = await channel.find_relevant_subreddits(keywords, 
                                                                           min_subscribers=filters.get('min_followers', 1000))
                        prospects.extend(subreddits)
                    
                    elif channel_type == ChannelType.TIKTOK:
                        opportunities = await channel.find_collaboration_opportunities(
                            ' '.join(keywords),
                            min_followers=filters.get('min_followers', 10000),
                            max_followers=filters.get('max_followers', 1000000)
                        )
                        prospects.extend(opportunities)
                    
                    # Apply filters
                    filtered_prospects = self._apply_prospect_filters(prospects, filters)
                    all_prospects[channel_name] = filtered_prospects
                    
                except Exception as e:
                    self.logger.error(f"Error discovering prospects on {channel_name}: {str(e)}")
                    all_prospects[channel_name] = []
            
            # Aggregate results
            total_prospects = sum(len(prospects) for prospects in all_prospects.values())
            
            return {
                'discovery_summary': {
                    'total_prospects': total_prospects,
                    'platforms_searched': len(channels),
                    'keywords_used': keywords,
                    'filters_applied': filters
                },
                'prospects_by_platform': all_prospects,
                'discovered_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering prospects: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _apply_prospect_filters(self, prospects: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to prospect list"""
        filtered = prospects
        
        # Filter by follower count
        min_followers = filters.get('min_followers')
        max_followers = filters.get('max_followers')
        
        if min_followers or max_followers:
            filtered = [
                p for p in filtered
                if self._check_follower_range(p, min_followers, max_followers)
            ]
        
        # Filter by engagement rate
        min_engagement = filters.get('min_engagement_rate')
        if min_engagement:
            filtered = [
                p for p in filtered
                if p.get('engagement_rate', 0) >= min_engagement
            ]
        
        # Filter by verification status
        verified_only = filters.get('verified_only', False)
        if verified_only:
            filtered = [
                p for p in filtered
                if p.get('verified', False)
            ]
        
        return filtered
    
    def _check_follower_range(self, prospect: Dict[str, Any], min_followers: Optional[int], max_followers: Optional[int]) -> bool:
        """Check if prospect's follower count is within range"""
        follower_count = prospect.get('follower_count') or prospect.get('subscriber_count') or prospect.get('subscribers', 0)
        
        if min_followers and follower_count < min_followers:
            return False
        
        if max_followers and follower_count > max_followers:
            return False
        
        return True
    
    async def close_all_channels(self):
        """Close all channel connections"""
        for channel in self.channels.values():
            try:
                await channel.close()
            except Exception as e:
                self.logger.error(f"Error closing channel {channel.channel_type.value}: {str(e)}")
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        # Note: This won't work in async context, but provides cleanup hint
        pass
