"""
YouTube Channel Service

Provides YouTube integration for creator outreach, channel analysis, and engagement tracking.
Uses YouTube Data API v3 for channel discovery and analytics.
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

class YouTubeService(BaseChannelService):
    """YouTube channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://www.googleapis.com/youtube/v3"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.YOUTUBE
    
    def _validate_config(self) -> None:
        """Validate YouTube configuration"""
        if not self.config.api_key:
            raise ValueError("YouTube API key is required")
        
        # Set default features
        default_features = {
            'channel_analysis': True,
            'video_analytics': True,
            'comment_engagement': True,
            'creator_discovery': True,
            'trend_analysis': True,
            'collaboration_outreach': False  # YouTube doesn't have direct messaging API
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize YouTube API client"""
        self.session = None
        self.headers = {
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
        """Make authenticated request to YouTube API"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        session = await self._get_session()
        
        # Add API key to params
        params = kwargs.get('params', {})
        params['key'] = self.config.api_key
        kwargs['params'] = params
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            self._record_request()
            async with session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    raise Exception("Rate limit exceeded")
                elif response.status == 401:
                    raise Exception("YouTube authentication failed")
                elif response.status == 403:
                    raise Exception("YouTube permission denied or quota exceeded")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"YouTube API error: {error_msg}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"YouTube request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """YouTube doesn't support direct messaging through API"""
        return MessageResponse(
            success=False,
            error="YouTube does not support direct messaging through API. Use email or social media for outreach.",
            metadata={
                'platform': 'youtube',
                'suggestion': 'Use channel email or social media links for outreach'
            }
        )
    
    async def get_profile(self, channel_id: str) -> Optional[ProfileData]:
        """Get YouTube channel information"""
        try:
            endpoint = "channels"
            params = {
                'part': 'snippet,statistics,brandingSettings,status',
                'id': channel_id
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            if not data.get('items'):
                return None
            
            channel = data['items'][0]
            snippet = channel.get('snippet', {})
            statistics = channel.get('statistics', {})
            branding = channel.get('brandingSettings', {}).get('channel', {})
            
            return ProfileData(
                user_id=channel['id'],
                username=snippet.get('customUrl', '').replace('@', ''),
                display_name=snippet.get('title'),
                bio=snippet.get('description'),
                follower_count=int(statistics.get('subscriberCount', 0)),
                post_count=int(statistics.get('videoCount', 0)),
                verified=False,  # Would need additional check
                profile_url=f"https://youtube.com/channel/{channel['id']}",
                avatar_url=snippet.get('thumbnails', {}).get('high', {}).get('url'),
                website=branding.get('unsubscribedTrailer'),
                created_at=datetime.fromisoformat(snippet.get('publishedAt', '').replace('Z', '+00:00')) if snippet.get('publishedAt') else None,
                engagement_rate=self._calculate_channel_engagement_rate(statistics),
                metadata={
                    'platform': 'youtube',
                    'view_count': int(statistics.get('viewCount', 0)),
                    'video_count': int(statistics.get('videoCount', 0)),
                    'subscriber_count': int(statistics.get('subscriberCount', 0)),
                    'country': snippet.get('country'),
                    'keywords': branding.get('keywords'),
                    'custom_url': snippet.get('customUrl')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting YouTube channel profile: {str(e)}")
            return None
    
    def _calculate_channel_engagement_rate(self, statistics: Dict[str, Any]) -> float:
        """Calculate engagement rate for a channel"""
        try:
            view_count = int(statistics.get('viewCount', 0))
            subscriber_count = int(statistics.get('subscriberCount', 0))
            video_count = int(statistics.get('videoCount', 0))
            
            if subscriber_count > 0 and video_count > 0:
                avg_views_per_video = view_count / video_count
                return (avg_views_per_video / subscriber_count) * 100
            return 0.0
        except:
            return 0.0
    
    async def get_engagement_metrics(self, video_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for a YouTube video"""
        try:
            endpoint = "videos"
            params = {
                'part': 'statistics,snippet',
                'id': video_id
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            if not data.get('items'):
                return None
            
            video = data['items'][0]
            statistics = video.get('statistics', {})
            
            return EngagementMetrics(
                views=int(statistics.get('viewCount', 0)),
                likes=int(statistics.get('likeCount', 0)),
                comments=int(statistics.get('commentCount', 0)),
                shares=0,  # YouTube doesn't provide share count via API
                engagement_rate=self._calculate_video_engagement_rate(statistics),
                metadata={
                    'platform': 'youtube',
                    'video_id': video_id,
                    'favorite_count': int(statistics.get('favoriteCount', 0)),
                    'duration': video.get('snippet', {}).get('duration'),
                    'published_at': video.get('snippet', {}).get('publishedAt')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting YouTube video engagement metrics: {str(e)}")
            return None
    
    def _calculate_video_engagement_rate(self, statistics: Dict[str, Any]) -> float:
        """Calculate engagement rate for a video"""
        try:
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            total_engagement = like_count + comment_count
            
            if view_count > 0:
                return (total_engagement / view_count) * 100
            return 0.0
        except:
            return 0.0
    
    async def search_channels(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for YouTube channels"""
        try:
            endpoint = "search"
            params = {
                'part': 'snippet',
                'type': 'channel',
                'q': query,
                'maxResults': min(max_results, 50),
                'order': 'relevance'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            channels = []
            for item in data.get('items', []):
                channel_data = {
                    'channel_id': item['snippet']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'published_at': item['snippet']['publishedAt']
                }
                
                # Get detailed channel info
                detailed_profile = await self.get_profile(item['snippet']['channelId'])
                if detailed_profile:
                    channel_data.update({
                        'subscriber_count': detailed_profile.follower_count,
                        'video_count': detailed_profile.post_count,
                        'view_count': detailed_profile.metadata.get('view_count', 0),
                        'engagement_rate': detailed_profile.engagement_rate
                    })
                
                channels.append(channel_data)
            
            return channels
            
        except Exception as e:
            self.logger.error(f"Error searching YouTube channels: {str(e)}")
            return []
    
    async def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get recent videos from a channel"""
        try:
            endpoint = "search"
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'type': 'video',
                'order': 'date',
                'maxResults': min(max_results, 50)
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            videos = []
            for item in data.get('items', []):
                video_data = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle']
                }
                
                # Get detailed video metrics
                metrics = await self.get_engagement_metrics(item['id']['videoId'])
                if metrics:
                    video_data.update({
                        'view_count': metrics.views,
                        'like_count': metrics.likes,
                        'comment_count': metrics.comments,
                        'engagement_rate': metrics.engagement_rate
                    })
                
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Error getting YouTube channel videos: {str(e)}")
            return []
    
    async def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get comments from a video"""
        try:
            endpoint = "commentThreads"
            params = {
                'part': 'snippet,replies',
                'videoId': video_id,
                'maxResults': min(max_results, 100),
                'order': 'relevance'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            comments = []
            for item in data.get('items', []):
                top_comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'comment_id': item['snippet']['topLevelComment']['id'],
                    'text': top_comment['textDisplay'],
                    'author': top_comment['authorDisplayName'],
                    'author_channel_id': top_comment.get('authorChannelId', {}).get('value'),
                    'like_count': top_comment['likeCount'],
                    'published_at': top_comment['publishedAt'],
                    'updated_at': top_comment['updatedAt'],
                    'reply_count': item['snippet']['totalReplyCount']
                }
                
                # Add replies if available
                if item.get('replies'):
                    comment_data['replies'] = [
                        {
                            'text': reply['snippet']['textDisplay'],
                            'author': reply['snippet']['authorDisplayName'],
                            'published_at': reply['snippet']['publishedAt']
                        }
                        for reply in item['replies']['comments']
                    ]
                
                comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error getting YouTube video comments: {str(e)}")
            return []
    
    async def analyze_trending_videos(self, category_id: str = None, region_code: str = 'US') -> List[Dict[str, Any]]:
        """Get trending videos for analysis"""
        try:
            endpoint = "videos"
            params = {
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': region_code,
                'maxResults': 50
            }
            
            if category_id:
                params['videoCategoryId'] = category_id
            
            data = await self._make_request('GET', endpoint, params=params)
            
            trending_videos = []
            for item in data.get('items', []):
                snippet = item.get('snippet', {})
                statistics = item.get('statistics', {})
                
                video_data = {
                    'video_id': item['id'],
                    'title': snippet.get('title'),
                    'channel_id': snippet.get('channelId'),
                    'channel_title': snippet.get('channelTitle'),
                    'description': snippet.get('description'),
                    'published_at': snippet.get('publishedAt'),
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0)),
                    'category_id': snippet.get('categoryId'),
                    'tags': snippet.get('tags', []),
                    'engagement_rate': self._calculate_video_engagement_rate(statistics)
                }
                
                trending_videos.append(video_data)
            
            return trending_videos
            
        except Exception as e:
            self.logger.error(f"Error analyzing YouTube trending videos: {str(e)}")
            return []
    
    async def get_channel_analytics(self, channel_id: str) -> Dict[str, Any]:
        """Get comprehensive channel analytics"""
        try:
            # Get channel profile
            profile = await self.get_profile(channel_id)
            if not profile:
                return {}
            
            # Get recent videos
            videos = await self.get_channel_videos(channel_id, 25)
            
            # Calculate analytics
            total_views = sum(video.get('view_count', 0) for video in videos)
            total_likes = sum(video.get('like_count', 0) for video in videos)
            total_comments = sum(video.get('comment_count', 0) for video in videos)
            avg_engagement = sum(video.get('engagement_rate', 0) for video in videos) / len(videos) if videos else 0
            
            # Analyze upload frequency
            upload_dates = [video.get('published_at') for video in videos if video.get('published_at')]
            upload_frequency = self._calculate_upload_frequency(upload_dates)
            
            return {
                'channel_profile': profile.__dict__,
                'recent_performance': {
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'average_engagement_rate': avg_engagement,
                    'video_count': len(videos)
                },
                'upload_frequency': upload_frequency,
                'top_videos': sorted(videos, key=lambda x: x.get('view_count', 0), reverse=True)[:5],
                'platform': 'youtube',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting YouTube channel analytics: {str(e)}")
            return {}
    
    def _calculate_upload_frequency(self, upload_dates: List[str]) -> Dict[str, Any]:
        """Calculate upload frequency from dates"""
        if len(upload_dates) < 2:
            return {'frequency': 'insufficient_data', 'days_between_uploads': 0}
        
        try:
            dates = [datetime.fromisoformat(date.replace('Z', '+00:00')) for date in upload_dates]
            dates.sort()
            
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            avg_interval = sum(intervals) / len(intervals)
            
            if avg_interval <= 1:
                frequency = 'daily'
            elif avg_interval <= 7:
                frequency = 'weekly'
            elif avg_interval <= 30:
                frequency = 'monthly'
            else:
                frequency = 'irregular'
            
            return {
                'frequency': frequency,
                'days_between_uploads': round(avg_interval, 1),
                'total_uploads_analyzed': len(upload_dates)
            }
        except:
            return {'frequency': 'unknown', 'days_between_uploads': 0}
    
    async def find_collaboration_opportunities(self, niche: str, min_subscribers: int = 1000, 
                                            max_subscribers: int = 1000000) -> List[Dict[str, Any]]:
        """Find potential collaboration opportunities"""
        try:
            # Search for channels in the niche
            channels = await self.search_channels(niche, max_results=50)
            
            # Filter by subscriber count and engagement
            opportunities = []
            for channel in channels:
                subscriber_count = channel.get('subscriber_count', 0)
                engagement_rate = channel.get('engagement_rate', 0)
                
                if (min_subscribers <= subscriber_count <= max_subscribers and 
                    engagement_rate > 2.0):  # Good engagement threshold
                    
                    # Get additional analysis
                    analytics = await self.get_channel_analytics(channel['channel_id'])
                    
                    opportunity = {
                        'channel_id': channel['channel_id'],
                        'channel_name': channel['title'],
                        'subscriber_count': subscriber_count,
                        'engagement_rate': engagement_rate,
                        'collaboration_score': self._calculate_collaboration_score(channel, analytics),
                        'contact_suggestions': await self._get_contact_suggestions(channel['channel_id']),
                        'recent_performance': analytics.get('recent_performance', {}),
                        'upload_frequency': analytics.get('upload_frequency', {})
                    }
                    
                    opportunities.append(opportunity)
            
            # Sort by collaboration score
            opportunities.sort(key=lambda x: x['collaboration_score'], reverse=True)
            
            return opportunities[:20]  # Return top 20 opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding YouTube collaboration opportunities: {str(e)}")
            return []
    
    def _calculate_collaboration_score(self, channel: Dict[str, Any], analytics: Dict[str, Any]) -> float:
        """Calculate collaboration potential score"""
        try:
            subscriber_count = channel.get('subscriber_count', 0)
            engagement_rate = channel.get('engagement_rate', 0)
            upload_frequency = analytics.get('upload_frequency', {}).get('frequency', 'unknown')
            
            # Base score from subscribers (normalized)
            subscriber_score = min(subscriber_count / 100000, 10)  # Max 10 points
            
            # Engagement score
            engagement_score = min(engagement_rate, 10)  # Max 10 points
            
            # Consistency score
            consistency_scores = {
                'daily': 10,
                'weekly': 8,
                'monthly': 5,
                'irregular': 2,
                'unknown': 1
            }
            consistency_score = consistency_scores.get(upload_frequency, 1)
            
            total_score = (subscriber_score + engagement_score + consistency_score) / 3
            return round(total_score, 2)
        except:
            return 0.0
    
    async def _get_contact_suggestions(self, channel_id: str) -> List[str]:
        """Get contact suggestions for a channel"""
        try:
            profile = await self.get_profile(channel_id)
            if not profile:
                return []
            
            suggestions = []
            
            # Check channel description for contact info
            description = profile.bio or ""
            if 'email' in description.lower() or '@' in description:
                suggestions.append("Check channel description for email")
            
            if profile.website:
                suggestions.append(f"Visit website: {profile.website}")
            
            # Check recent videos for contact info
            videos = await self.get_channel_videos(channel_id, 5)
            for video in videos:
                if 'contact' in video.get('description', '').lower():
                    suggestions.append(f"Check video description: {video['title']}")
                    break
            
            # Default suggestions
            suggestions.extend([
                "Comment on recent videos",
                "Check social media links in channel about section",
                "Look for business inquiry information"
            ])
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting contact suggestions: {str(e)}")
            return ["Check channel about section for contact information"]
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This won't work in async context, but provides cleanup hint
            pass
