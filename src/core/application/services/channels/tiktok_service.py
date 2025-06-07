"""
TikTok Channel Service

Provides TikTok integration for creator outreach, content analysis, and engagement tracking.
Uses TikTok Business API and TikTok for Developers API.
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

class TikTokService(BaseChannelService):
    """TikTok channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://open-api.tiktok.com"
        self.api_version = "v1.3"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.TIKTOK
    
    def _validate_config(self) -> None:
        """Validate TikTok configuration"""
        if not self.config.access_token:
            raise ValueError("TikTok access token is required")
        
        # Set default features
        default_features = {
            'profile_discovery': True,
            'video_analytics': True,
            'trend_analysis': True,
            'creator_discovery': True,
            'hashtag_analysis': True,
            'direct_messaging': False  # TikTok API has limited DM support
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize TikTok API client"""
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
        """Make authenticated request to TikTok API"""
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
                    raise Exception("TikTok authentication failed")
                elif response.status == 403:
                    raise Exception("TikTok permission denied")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"TikTok API error: {error_msg}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"TikTok request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """TikTok has limited direct messaging support"""
        return MessageResponse(
            success=False,
            error="TikTok direct messaging is not widely available through API. Use comments or other social platforms for outreach.",
            metadata={
                'platform': 'tiktok',
                'suggestion': 'Engage through comments, duets, or use other contact methods'
            }
        )
    
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Get TikTok user profile information"""
        try:
            endpoint = f"user/info/"
            params = {
                'fields': 'open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count'
            }
            
            if user_id == "me":
                # Get current user info
                data = await self._make_request('GET', endpoint, params=params)
            else:
                # For other users, we need their open_id
                params['open_id'] = user_id
                data = await self._make_request('GET', endpoint, params=params)
            
            if not data.get('data'):
                return None
            
            user_data = data['data']['user']
            
            return ProfileData(
                user_id=user_data.get('open_id', user_id),
                username=user_data.get('unique_id', ''),
                display_name=user_data.get('display_name'),
                bio=user_data.get('bio_description'),
                follower_count=user_data.get('follower_count', 0),
                following_count=user_data.get('following_count', 0),
                post_count=user_data.get('video_count', 0),
                verified=user_data.get('is_verified', False),
                profile_url=user_data.get('profile_deep_link'),
                avatar_url=user_data.get('avatar_url'),
                engagement_rate=self._calculate_profile_engagement_rate(user_data),
                metadata={
                    'platform': 'tiktok',
                    'likes_count': user_data.get('likes_count', 0),
                    'union_id': user_data.get('union_id'),
                    'profile_type': 'creator' if user_data.get('video_count', 0) > 10 else 'user'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting TikTok profile: {str(e)}")
            return None
    
    def _calculate_profile_engagement_rate(self, user_data: Dict[str, Any]) -> float:
        """Calculate engagement rate for a TikTok profile"""
        try:
            follower_count = user_data.get('follower_count', 0)
            likes_count = user_data.get('likes_count', 0)
            video_count = user_data.get('video_count', 0)
            
            if follower_count > 0 and video_count > 0:
                avg_likes_per_video = likes_count / video_count
                return (avg_likes_per_video / follower_count) * 100
            return 0.0
        except:
            return 0.0
    
    async def get_engagement_metrics(self, video_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for a TikTok video"""
        try:
            endpoint = f"video/list/"
            params = {
                'fields': 'id,title,video_description,duration,cover_image_url,embed_link,like_count,comment_count,share_count,view_count'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            # Find the specific video
            video = None
            for item in data.get('data', {}).get('videos', []):
                if item.get('id') == video_id:
                    video = item
                    break
            
            if not video:
                return None
            
            return EngagementMetrics(
                views=video.get('view_count', 0),
                likes=video.get('like_count', 0),
                comments=video.get('comment_count', 0),
                shares=video.get('share_count', 0),
                engagement_rate=self._calculate_video_engagement_rate(video),
                metadata={
                    'platform': 'tiktok',
                    'video_id': video_id,
                    'duration': video.get('duration'),
                    'title': video.get('title'),
                    'embed_link': video.get('embed_link')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting TikTok video engagement metrics: {str(e)}")
            return None
    
    def _calculate_video_engagement_rate(self, video: Dict[str, Any]) -> float:
        """Calculate engagement rate for a TikTok video"""
        try:
            view_count = video.get('view_count', 0)
            like_count = video.get('like_count', 0)
            comment_count = video.get('comment_count', 0)
            share_count = video.get('share_count', 0)
            
            total_engagement = like_count + comment_count + share_count
            
            if view_count > 0:
                return (total_engagement / view_count) * 100
            return 0.0
        except:
            return 0.0
    
    async def get_user_videos(self, user_id: str = "me", max_count: int = 20) -> List[Dict[str, Any]]:
        """Get user's recent videos"""
        try:
            endpoint = f"video/list/"
            params = {
                'fields': 'id,title,video_description,duration,cover_image_url,embed_link,like_count,comment_count,share_count,view_count,create_time',
                'max_count': min(max_count, 20)
            }
            
            if user_id != "me":
                # For other users, this might require different permissions
                params['open_id'] = user_id
            
            data = await self._make_request('GET', endpoint, params=params)
            
            videos = []
            for video in data.get('data', {}).get('videos', []):
                video_data = {
                    'video_id': video.get('id'),
                    'title': video.get('title'),
                    'description': video.get('video_description'),
                    'duration': video.get('duration'),
                    'cover_image': video.get('cover_image_url'),
                    'embed_link': video.get('embed_link'),
                    'view_count': video.get('view_count', 0),
                    'like_count': video.get('like_count', 0),
                    'comment_count': video.get('comment_count', 0),
                    'share_count': video.get('share_count', 0),
                    'created_at': video.get('create_time'),
                    'engagement_rate': self._calculate_video_engagement_rate(video)
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Error getting TikTok user videos: {str(e)}")
            return []
    
    async def search_creators(self, keyword: str, min_followers: int = 1000) -> List[Dict[str, Any]]:
        """Search for TikTok creators (limited by API availability)"""
        try:
            # Note: TikTok's public API has limited search capabilities
            # This is a placeholder for when more comprehensive search becomes available
            
            # For now, we can only get trending hashtags and work backwards
            trending_hashtags = await self.get_trending_hashtags()
            
            creators = []
            # This would need to be implemented when TikTok provides better search APIs
            # or through web scraping (which should be done carefully and ethically)
            
            return creators
            
        except Exception as e:
            self.logger.error(f"Error searching TikTok creators: {str(e)}")
            return []
    
    async def get_trending_hashtags(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get trending hashtags (if available through API)"""
        try:
            # Note: This endpoint may not be available in all TikTok API versions
            endpoint = "research/hashtag/trending/"
            params = {
                'count': min(count, 100)
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            hashtags = []
            for hashtag in data.get('data', {}).get('hashtags', []):
                hashtag_data = {
                    'hashtag': hashtag.get('hashtag_name'),
                    'view_count': hashtag.get('view_count', 0),
                    'video_count': hashtag.get('video_count', 0),
                    'trend_score': hashtag.get('trend_score', 0)
                }
                hashtags.append(hashtag_data)
            
            return hashtags
            
        except Exception as e:
            self.logger.error(f"Error getting TikTok trending hashtags: {str(e)}")
            # Return some common hashtags as fallback
            return [
                {'hashtag': 'fyp', 'view_count': 0, 'video_count': 0, 'trend_score': 0},
                {'hashtag': 'viral', 'view_count': 0, 'video_count': 0, 'trend_score': 0},
                {'hashtag': 'trending', 'view_count': 0, 'video_count': 0, 'trend_score': 0}
            ]
    
    async def analyze_hashtag_performance(self, hashtag: str, days: int = 7) -> Dict[str, Any]:
        """Analyze hashtag performance over time"""
        try:
            endpoint = "research/hashtag/videos/"
            params = {
                'hashtag_name': hashtag.replace('#', ''),
                'max_count': 100,
                'fields': 'id,like_count,comment_count,share_count,view_count,create_time'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            videos = data.get('data', {}).get('videos', [])
            
            # Calculate performance metrics
            total_views = sum(video.get('view_count', 0) for video in videos)
            total_likes = sum(video.get('like_count', 0) for video in videos)
            total_comments = sum(video.get('comment_count', 0) for video in videos)
            total_shares = sum(video.get('share_count', 0) for video in videos)
            
            avg_engagement = 0
            if videos:
                engagement_rates = [self._calculate_video_engagement_rate(video) for video in videos]
                avg_engagement = sum(engagement_rates) / len(engagement_rates)
            
            return {
                'hashtag': hashtag,
                'video_count': len(videos),
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_shares': total_shares,
                'average_engagement_rate': avg_engagement,
                'avg_views_per_video': total_views / len(videos) if videos else 0,
                'platform': 'tiktok',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing TikTok hashtag performance: {str(e)}")
            return {}
    
    async def get_creator_analytics(self, user_id: str = "me") -> Dict[str, Any]:
        """Get comprehensive creator analytics"""
        try:
            # Get profile data
            profile = await self.get_profile(user_id)
            if not profile:
                return {}
            
            # Get recent videos
            videos = await self.get_user_videos(user_id, max_count=20)
            
            # Calculate analytics
            total_views = sum(video.get('view_count', 0) for video in videos)
            total_likes = sum(video.get('like_count', 0) for video in videos)
            total_comments = sum(video.get('comment_count', 0) for video in videos)
            total_shares = sum(video.get('share_count', 0) for video in videos)
            
            avg_engagement = sum(video.get('engagement_rate', 0) for video in videos) / len(videos) if videos else 0
            
            # Analyze posting frequency
            posting_frequency = self._analyze_posting_frequency(videos)
            
            # Find best performing content
            top_videos = sorted(videos, key=lambda x: x.get('view_count', 0), reverse=True)[:5]
            
            return {
                'profile': profile.__dict__,
                'performance_metrics': {
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'average_engagement_rate': avg_engagement,
                    'video_count': len(videos)
                },
                'posting_frequency': posting_frequency,
                'top_performing_videos': top_videos,
                'content_analysis': self._analyze_content_themes(videos),
                'platform': 'tiktok',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting TikTok creator analytics: {str(e)}")
            return {}
    
    def _analyze_posting_frequency(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posting frequency from video timestamps"""
        if len(videos) < 2:
            return {'frequency': 'insufficient_data', 'posts_per_week': 0}
        
        try:
            # Convert timestamps to datetime objects
            timestamps = []
            for video in videos:
                if video.get('created_at'):
                    # Assuming timestamp is in seconds
                    timestamp = datetime.fromtimestamp(video['created_at'], tz=timezone.utc)
                    timestamps.append(timestamp)
            
            if len(timestamps) < 2:
                return {'frequency': 'insufficient_data', 'posts_per_week': 0}
            
            timestamps.sort()
            
            # Calculate average days between posts
            intervals = [(timestamps[i] - timestamps[i-1]).days for i in range(1, len(timestamps))]
            avg_interval = sum(intervals) / len(intervals)
            
            posts_per_week = 7 / avg_interval if avg_interval > 0 else 0
            
            if avg_interval <= 1:
                frequency = 'daily'
            elif avg_interval <= 3:
                frequency = 'frequent'
            elif avg_interval <= 7:
                frequency = 'weekly'
            else:
                frequency = 'irregular'
            
            return {
                'frequency': frequency,
                'posts_per_week': round(posts_per_week, 1),
                'avg_days_between_posts': round(avg_interval, 1)
            }
        except:
            return {'frequency': 'unknown', 'posts_per_week': 0}
    
    def _analyze_content_themes(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content themes from video titles and descriptions"""
        try:
            # Simple keyword analysis
            all_text = ""
            for video in videos:
                title = video.get('title', '')
                description = video.get('description', '')
                all_text += f" {title} {description}"
            
            # Basic keyword extraction (in production, use more sophisticated NLP)
            words = all_text.lower().split()
            word_freq = {}
            
            # Filter out common words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
            
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'top_keywords': [{'keyword': word, 'frequency': freq} for word, freq in top_keywords],
                'total_words_analyzed': len(words),
                'unique_words': len(word_freq)
            }
        except:
            return {'top_keywords': [], 'total_words_analyzed': 0, 'unique_words': 0}
    
    async def find_collaboration_opportunities(self, niche: str, min_followers: int = 10000, 
                                            max_followers: int = 1000000) -> List[Dict[str, Any]]:
        """Find potential collaboration opportunities on TikTok"""
        try:
            # Note: This is limited by TikTok's API search capabilities
            # In practice, this would require more sophisticated discovery methods
            
            opportunities = []
            
            # Get trending hashtags related to niche
            hashtags = await self.get_trending_hashtags()
            relevant_hashtags = [h for h in hashtags if niche.lower() in h.get('hashtag', '').lower()]
            
            # For each relevant hashtag, analyze top creators
            for hashtag_data in relevant_hashtags[:5]:  # Limit to top 5 relevant hashtags
                hashtag = hashtag_data.get('hashtag', '')
                analysis = await self.analyze_hashtag_performance(hashtag)
                
                # This would need to be expanded with actual creator discovery
                # when TikTok provides better search APIs
                
                opportunity = {
                    'hashtag': hashtag,
                    'potential_reach': hashtag_data.get('view_count', 0),
                    'video_count': hashtag_data.get('video_count', 0),
                    'collaboration_type': 'hashtag_challenge',
                    'engagement_potential': analysis.get('average_engagement_rate', 0)
                }
                
                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding TikTok collaboration opportunities: {str(e)}")
            return []
    
    async def get_content_insights(self, video_ids: List[str]) -> Dict[str, Any]:
        """Get insights for multiple videos"""
        try:
            insights = []
            
            for video_id in video_ids:
                metrics = await self.get_engagement_metrics(video_id)
                if metrics:
                    insights.append({
                        'video_id': video_id,
                        'metrics': metrics.__dict__
                    })
            
            # Calculate aggregate insights
            total_views = sum(insight['metrics']['views'] for insight in insights)
            total_engagement = sum(
                insight['metrics']['likes'] + insight['metrics']['comments'] + insight['metrics']['shares']
                for insight in insights
            )
            
            avg_engagement_rate = sum(insight['metrics']['engagement_rate'] for insight in insights) / len(insights) if insights else 0
            
            return {
                'video_insights': insights,
                'aggregate_metrics': {
                    'total_videos': len(insights),
                    'total_views': total_views,
                    'total_engagement': total_engagement,
                    'average_engagement_rate': avg_engagement_rate
                },
                'platform': 'tiktok',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting TikTok content insights: {str(e)}")
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
