"""
Facebook Channel Service

Provides Facebook integration for profile discovery, messaging, and engagement tracking.
Uses Facebook Graph API for business pages and Messenger Platform API.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import json

from .base_channel import (
    BaseChannelService, ChannelType, ChannelConfig, MessageRequest, 
    MessageResponse, ProfileData, EngagementMetrics, MessageStatus
)

class FacebookService(BaseChannelService):
    """Facebook channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://graph.facebook.com"
        self.api_version = "v18.0"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.FACEBOOK
    
    def _validate_config(self) -> None:
        """Validate Facebook configuration"""
        if not self.config.access_token:
            raise ValueError("Facebook access token is required")
        
        if not self.config.metadata.get('page_id'):
            raise ValueError("Facebook page ID is required for messaging")
        
        # Set default features
        default_features = {
            'messaging': True,
            'page_management': True,
            'profile_discovery': True,
            'engagement_tracking': True,
            'audience_insights': True,
            'lead_generation': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize Facebook API client"""
        self.session = None
        self.headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json'
        }
        self.page_id = self.config.metadata.get('page_id')
    
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
        """Make authenticated request to Facebook API"""
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
                    raise Exception("Facebook authentication failed")
                elif response.status == 403:
                    raise Exception("Facebook permission denied")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"Facebook API error: {error_msg}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"Facebook request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send Facebook Messenger message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="Facebook messaging is disabled"
                )
            
            # Get recipient profile to validate and personalize
            profile = await self.get_profile(request.recipient_id)
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            
            # Prepare message data for Messenger API
            message_data = {
                'recipient': {'id': request.recipient_id},
                'message': {
                    'text': personalized_content[:2000]  # Facebook message limit
                },
                'messaging_type': 'MESSAGE_TAG',
                'tag': 'CONFIRMED_EVENT_UPDATE'  # Use appropriate tag based on use case
            }
            
            # Add quick replies if specified
            if request.metadata.get('quick_replies'):
                message_data['message']['quick_replies'] = request.metadata['quick_replies']
            
            # Send via Messenger API
            endpoint = f"{self.page_id}/messages"
            response_data = await self._make_request('POST', endpoint, json=message_data)
            
            message_id = self._generate_message_id()
            response = MessageResponse(
                success=True,
                message_id=message_id,
                external_id=response_data.get('message_id'),
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'facebook',
                    'message_type': request.message_type,
                    'character_count': len(personalized_content),
                    'recipient_id': request.recipient_id
                }
            )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Get Facebook profile information"""
        try:
            if user_id == "me":
                endpoint = "me"
                params = {
                    'fields': 'id,name,email,picture,location,website,about,fan_count,followers_count'
                }
            else:
                # For other users, limited fields available due to privacy
                endpoint = f"{user_id}"
                params = {
                    'fields': 'id,name,picture'
                }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            return ProfileData(
                user_id=data['id'],
                username=data.get('id'),  # Facebook uses ID as username
                display_name=data.get('name'),
                bio=data.get('about'),
                follower_count=data.get('followers_count') or data.get('fan_count'),
                verified=False,  # Would need additional API call
                profile_url=f"https://facebook.com/{data['id']}",
                avatar_url=data.get('picture', {}).get('data', {}).get('url'),
                location=data.get('location', {}).get('name') if data.get('location') else None,
                website=data.get('website'),
                metadata={
                    'platform': 'facebook',
                    'email': data.get('email')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook profile: {str(e)}")
            return None
    
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for Facebook content"""
        try:
            # Get post insights
            endpoint = f"{content_id}/insights"
            params = {
                'metric': 'post_impressions,post_reach,post_reactions_by_type_total,post_clicks,post_shares'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            metrics = {}
            for insight in data.get('data', []):
                metrics[insight['name']] = insight.get('values', [{}])[0].get('value', 0)
            
            # Get basic post data
            post_data = await self._make_request('GET', content_id, params={
                'fields': 'likes.summary(true),comments.summary(true),shares'
            })
            
            likes = post_data.get('likes', {}).get('summary', {}).get('total_count', 0)
            comments = post_data.get('comments', {}).get('summary', {}).get('total_count', 0)
            shares = post_data.get('shares', {}).get('count', 0)
            
            return EngagementMetrics(
                views=metrics.get('post_impressions', 0),
                likes=likes,
                comments=comments,
                shares=shares,
                clicks=metrics.get('post_clicks', 0),
                reach=metrics.get('post_reach', 0),
                impressions=metrics.get('post_impressions', 0),
                engagement_rate=self._calculate_engagement_rate(likes, comments, shares, metrics.get('post_reach', 0)),
                metadata={
                    'platform': 'facebook',
                    'content_id': content_id,
                    'reactions': metrics.get('post_reactions_by_type_total', {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook engagement metrics: {str(e)}")
            return None
    
    def _calculate_engagement_rate(self, likes: int, comments: int, shares: int, reach: int) -> float:
        """Calculate engagement rate from metrics"""
        total_engagement = likes + comments + shares
        
        if reach > 0:
            return (total_engagement / reach) * 100
        return 0.0
    
    async def get_page_posts(self, page_id: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Get page's recent posts"""
        try:
            page_id = page_id or self.page_id
            endpoint = f"{page_id}/posts"
            params = {
                'fields': 'id,message,created_time,likes.summary(true),comments.summary(true),shares,permalink_url',
                'limit': limit
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook page posts: {str(e)}")
            return []
    
    async def create_lead_ad(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Facebook lead generation ad"""
        try:
            if not self.config.features.get('lead_generation', False):
                raise Exception("Lead generation feature is disabled")
            
            # This requires Facebook Marketing API access
            endpoint = f"{self.config.metadata.get('ad_account_id')}/campaigns"
            
            response_data = await self._make_request('POST', endpoint, json=campaign_data)
            
            return {
                'success': True,
                'campaign_id': response_data.get('id'),
                'platform': 'facebook'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Facebook lead ad: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_audience_insights(self, page_id: str = None) -> Dict[str, Any]:
        """Get audience insights for a Facebook page"""
        try:
            page_id = page_id or self.page_id
            endpoint = f"{page_id}/insights"
            params = {
                'metric': 'page_fans,page_fan_adds,page_fan_removes,page_impressions,page_reach',
                'period': 'day',
                'since': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'until': datetime.now().strftime('%Y-%m-%d')
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            insights = {}
            for metric in data.get('data', []):
                insights[metric['name']] = metric.get('values', [])
            
            # Get demographic data
            demo_endpoint = f"{page_id}/insights/page_fans_by_like_source_unique"
            demo_params = {'period': 'lifetime'}
            demo_data = await self._make_request('GET', demo_endpoint, params=demo_params)
            
            return {
                'metrics': insights,
                'demographics': demo_data.get('data', []),
                'platform': 'facebook',
                'page_id': page_id
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook audience insights: {str(e)}")
            return {}
    
    async def send_broadcast_message(self, message: str, audience_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send broadcast message to page followers"""
        try:
            # This requires special permissions and compliance with Facebook policies
            endpoint = f"{self.page_id}/messages"
            
            broadcast_data = {
                'message': {'text': message[:2000]},
                'messaging_type': 'MESSAGE_TAG',
                'tag': 'CONFIRMED_EVENT_UPDATE'
            }
            
            # If audience filter is provided, use it
            if audience_filter:
                broadcast_data['audience'] = audience_filter
            
            response_data = await self._make_request('POST', endpoint, json=broadcast_data)
            
            return {
                'success': True,
                'broadcast_id': response_data.get('message_id'),
                'platform': 'facebook'
            }
            
        except Exception as e:
            self.logger.error(f"Error sending Facebook broadcast: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_page_conversations(self, page_id: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Get page conversations"""
        try:
            page_id = page_id or self.page_id
            endpoint = f"{page_id}/conversations"
            params = {
                'fields': 'id,updated_time,message_count,unread_count,participants',
                'limit': limit
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook conversations: {str(e)}")
            return []
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages from a specific conversation"""
        try:
            endpoint = f"{conversation_id}/messages"
            params = {
                'fields': 'id,created_time,from,to,message',
                'limit': limit
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook conversation messages: {str(e)}")
            return []
    
    async def set_page_webhook(self, webhook_url: str, verify_token: str) -> Dict[str, Any]:
        """Set up webhook for page events"""
        try:
            endpoint = f"{self.page_id}/subscribed_apps"
            webhook_data = {
                'subscribed_fields': 'messages,messaging_postbacks,messaging_optins,message_deliveries,message_reads',
                'callback_url': webhook_url,
                'verify_token': verify_token
            }
            
            response_data = await self._make_request('POST', endpoint, json=webhook_data)
            
            return {
                'success': True,
                'webhook_id': response_data.get('id'),
                'platform': 'facebook'
            }
            
        except Exception as e:
            self.logger.error(f"Error setting Facebook webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_competitor_page(self, competitor_page_id: str) -> Dict[str, Any]:
        """Analyze competitor page (public data only)"""
        try:
            # Get public page information
            page_data = await self.get_profile(competitor_page_id)
            posts = await self.get_page_posts(competitor_page_id, limit=50)
            
            # Calculate engagement metrics
            total_engagement = 0
            total_posts = len(posts)
            
            for post in posts:
                likes = post.get('likes', {}).get('summary', {}).get('total_count', 0)
                comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                shares = post.get('shares', {}).get('count', 0)
                total_engagement += likes + comments + shares
            
            avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
            
            return {
                'page_data': page_data.__dict__ if page_data else {},
                'post_count': total_posts,
                'average_engagement': avg_engagement,
                'total_engagement': total_engagement,
                'platform': 'facebook',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Facebook competitor page: {str(e)}")
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
