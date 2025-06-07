"""
Instagram Channel Service

Provides Instagram integration for profile discovery, messaging, and engagement tracking.
Uses Instagram Basic Display API and Instagram Graph API for business accounts.
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

class InstagramService(BaseChannelService):
    """Instagram channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://graph.instagram.com"
        self.api_version = "v18.0"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.INSTAGRAM
    
    def _validate_config(self) -> None:
        """Validate Instagram configuration"""
        if not self.config.access_token:
            raise ValueError("Instagram access token is required")
        
        # Set default features
        default_features = {
            'messaging': True,
            'story_mentions': True,
            'profile_discovery': True,
            'engagement_tracking': True,
            'hashtag_analysis': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize Instagram API client"""
        self.session = None
        self.headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json'
        }
    
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
        """Make authenticated request to Instagram API"""
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
                    raise Exception("Instagram authentication failed")
                elif response.status == 403:
                    raise Exception("Instagram permission denied")
                elif response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Instagram API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"Instagram request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send Instagram direct message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="Instagram messaging is disabled"
                )
            
            # Instagram Graph API doesn't support direct messaging for personal accounts
            # This would require Instagram Business API or third-party solutions
            # For now, we'll simulate the functionality
            
            # Get recipient profile to validate
            profile = await self.get_profile(request.recipient_id)
            if not profile:
                return MessageResponse(
                    success=False,
                    error="Recipient profile not found"
                )
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            
            # For Instagram, we would typically use Instagram Messaging API
            # which requires special permissions and business verification
            message_data = {
                'recipient': {'id': request.recipient_id},
                'message': {
                    'text': personalized_content[:1000]  # Instagram message limit
                }
            }
            
            # Simulate API call (replace with actual implementation when available)
            response_data = await self._simulate_message_send(message_data)
            
            message_id = self._generate_message_id()
            response = MessageResponse(
                success=True,
                message_id=message_id,
                external_id=response_data.get('message_id'),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'instagram',
                    'message_type': request.message_type,
                    'character_count': len(personalized_content)
                }
            )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    async def _simulate_message_send(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate message sending (replace with actual API call)"""
        # This is a placeholder for the actual Instagram Messaging API call
        # In production, you would implement the actual API integration
        return {
            'message_id': f"ig_msg_{datetime.now().timestamp()}",
            'status': 'sent'
        }
    
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Get Instagram profile information"""
        try:
            if user_id == "me":
                endpoint = "me"
                params = {
                    'fields': 'id,username,account_type,media_count,followers_count,follows_count'
                }
            else:
                # For other users, we need to use Instagram Basic Display API
                # or have them connected to our business account
                endpoint = f"{user_id}"
                params = {
                    'fields': 'id,username,media_count'
                }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            return ProfileData(
                user_id=data['id'],
                username=data.get('username'),
                display_name=data.get('username'),  # Instagram doesn't separate display name
                follower_count=data.get('followers_count'),
                following_count=data.get('follows_count'),
                post_count=data.get('media_count'),
                verified=False,  # Would need additional API call to determine
                profile_url=f"https://instagram.com/{data.get('username', '')}",
                metadata={
                    'account_type': data.get('account_type'),
                    'platform': 'instagram'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Instagram profile: {str(e)}")
            return None
    
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for Instagram content"""
        try:
            # Get media insights
            endpoint = f"{content_id}/insights"
            params = {
                'metric': 'impressions,reach,likes,comments,shares,saves'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            metrics = {}
            for insight in data.get('data', []):
                metrics[insight['name']] = insight.get('values', [{}])[0].get('value', 0)
            
            return EngagementMetrics(
                views=metrics.get('impressions', 0),
                likes=metrics.get('likes', 0),
                comments=metrics.get('comments', 0),
                shares=metrics.get('shares', 0),
                saves=metrics.get('saves', 0),
                reach=metrics.get('reach', 0),
                impressions=metrics.get('impressions', 0),
                engagement_rate=self._calculate_engagement_rate(metrics),
                metadata={
                    'platform': 'instagram',
                    'content_id': content_id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Instagram engagement metrics: {str(e)}")
            return None
    
    def _calculate_engagement_rate(self, metrics: Dict[str, int]) -> float:
        """Calculate engagement rate from metrics"""
        total_engagement = (
            metrics.get('likes', 0) + 
            metrics.get('comments', 0) + 
            metrics.get('shares', 0) + 
            metrics.get('saves', 0)
        )
        reach = metrics.get('reach', 0)
        
        if reach > 0:
            return (total_engagement / reach) * 100
        return 0.0
    
    async def get_user_media(self, user_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Get user's recent media posts"""
        try:
            endpoint = f"{user_id}/media"
            params = {
                'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                'limit': limit
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Instagram user media: {str(e)}")
            return []
    
    async def search_hashtag(self, hashtag: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for posts by hashtag"""
        try:
            # This requires Instagram Graph API with specific permissions
            endpoint = f"ig_hashtag_search"
            params = {
                'user_id': 'me',  # Business account ID
                'q': hashtag
            }
            
            # First get hashtag ID
            hashtag_data = await self._make_request('GET', endpoint, params=params)
            
            if not hashtag_data.get('data'):
                return []
            
            hashtag_id = hashtag_data['data'][0]['id']
            
            # Get recent media for hashtag
            endpoint = f"{hashtag_id}/recent_media"
            params = {
                'user_id': 'me',
                'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                'limit': limit
            }
            
            media_data = await self._make_request('GET', endpoint, params=params)
            return media_data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error searching Instagram hashtag: {str(e)}")
            return []
    
    async def get_story_mentions(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get mentions in Instagram stories"""
        try:
            endpoint = "me/stories"
            params = {
                'fields': 'id,media_type,media_url,timestamp',
                'limit': limit
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Instagram story mentions: {str(e)}")
            return []
    
    async def analyze_audience(self, user_id: str = "me") -> Dict[str, Any]:
        """Analyze audience demographics and insights"""
        try:
            endpoint = f"{user_id}/insights"
            params = {
                'metric': 'audience_gender_age,audience_locale,audience_country',
                'period': 'lifetime'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            audience_data = {}
            for insight in data.get('data', []):
                audience_data[insight['name']] = insight.get('values', [{}])[0].get('value', {})
            
            return {
                'demographics': audience_data,
                'total_followers': await self._get_follower_count(user_id),
                'engagement_rate': await self._get_average_engagement_rate(user_id),
                'platform': 'instagram'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Instagram audience: {str(e)}")
            return {}
    
    async def _get_follower_count(self, user_id: str) -> int:
        """Get current follower count"""
        try:
            profile = await self.get_profile(user_id)
            return profile.follower_count if profile else 0
        except:
            return 0
    
    async def _get_average_engagement_rate(self, user_id: str) -> float:
        """Calculate average engagement rate from recent posts"""
        try:
            media = await self.get_user_media(user_id, limit=10)
            if not media:
                return 0.0
            
            total_engagement = 0
            total_reach = 0
            
            for post in media:
                likes = post.get('like_count', 0)
                comments = post.get('comments_count', 0)
                total_engagement += likes + comments
                
                # Estimate reach (would need insights API for actual reach)
                total_reach += likes * 10  # Rough estimation
            
            if total_reach > 0:
                return (total_engagement / total_reach) * 100
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating Instagram engagement rate: {str(e)}")
            return 0.0
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This won't work in async context, but provides cleanup hint
            pass
