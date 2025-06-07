"""
Reddit Channel Service

Provides Reddit integration for community engagement, content discovery, and outreach.
Uses Reddit API (PRAW) for subreddit analysis and user engagement.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import json
import base64

from .base_channel import (
    BaseChannelService, ChannelType, ChannelConfig, MessageRequest, 
    MessageResponse, ProfileData, EngagementMetrics, MessageStatus
)

class RedditService(BaseChannelService):
    """Reddit channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.base_url = "https://oauth.reddit.com"
        self.auth_url = "https://www.reddit.com/api/v1/access_token"
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.REDDIT
    
    def _validate_config(self) -> None:
        """Validate Reddit configuration"""
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("Reddit client ID and secret are required")
        
        if not self.config.metadata.get('username') or not self.config.metadata.get('password'):
            raise ValueError("Reddit username and password are required")
        
        # Set default features
        default_features = {
            'messaging': True,
            'subreddit_analysis': True,
            'post_engagement': True,
            'comment_tracking': True,
            'user_discovery': True,
            'trend_analysis': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize Reddit API client"""
        self.session = None
        self.access_token = None
        self.headers = {
            'User-Agent': f'AffiliateOutreach/1.0 by {self.config.metadata.get("username", "bot")}'
        }
        self.client_id = self.config.api_key
        self.client_secret = self.config.api_secret
        self.username = self.config.metadata.get('username')
        self.password = self.config.metadata.get('password')
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
        return self.session
    
    async def _authenticate(self) -> bool:
        """Authenticate with Reddit API"""
        try:
            session = await self._get_session()
            
            # Prepare authentication data
            auth_data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password
            }
            
            # Create basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            auth_headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'User-Agent': self.headers['User-Agent']
            }
            
            async with session.post(self.auth_url, data=auth_data, headers=auth_headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get('access_token')
                    
                    # Update session headers
                    self.headers['Authorization'] = f'Bearer {self.access_token}'
                    return True
                else:
                    self.logger.error(f"Reddit authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error authenticating with Reddit: {str(e)}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Reddit API"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        # Ensure we're authenticated
        if not self.access_token:
            if not await self._authenticate():
                raise Exception("Reddit authentication failed")
        
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        # Update headers with auth token
        headers = {**self.headers, 'Authorization': f'Bearer {self.access_token}'}
        
        try:
            self._record_request()
            async with session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 429:
                    raise Exception("Rate limit exceeded")
                elif response.status == 401:
                    # Try to re-authenticate
                    if await self._authenticate():
                        headers['Authorization'] = f'Bearer {self.access_token}'
                        async with session.request(method, url, headers=headers, **kwargs) as retry_response:
                            if retry_response.status >= 400:
                                raise Exception("Reddit authentication failed after retry")
                            return await retry_response.json()
                    else:
                        raise Exception("Reddit authentication failed")
                elif response.status == 403:
                    raise Exception("Reddit permission denied")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                    raise Exception(f"Reddit API error: {error_msg}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise Exception(f"Reddit request failed: {str(e)}")
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send Reddit private message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="Reddit messaging is disabled"
                )
            
            # Get recipient profile for personalization
            profile = await self.get_profile(request.recipient_id)
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            
            # Prepare message data
            message_data = {
                'to': request.recipient_id,
                'subject': request.subject or 'Partnership Opportunity',
                'text': personalized_content[:10000],  # Reddit message limit
                'api_type': 'json'
            }
            
            # Send message
            endpoint = "api/compose"
            response_data = await self._make_request('POST', endpoint, data=message_data)
            
            # Check for errors in response
            errors = response_data.get('json', {}).get('errors', [])
            if errors:
                error_msg = '; '.join([error[1] for error in errors])
                return MessageResponse(
                    success=False,
                    error=f"Reddit API error: {error_msg}"
                )
            
            message_id = self._generate_message_id()
            response = MessageResponse(
                success=True,
                message_id=message_id,
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'reddit',
                    'message_type': request.message_type,
                    'character_count': len(personalized_content),
                    'recipient': request.recipient_id,
                    'subject': request.subject
                }
            )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    async def get_profile(self, username: str) -> Optional[ProfileData]:
        """Get Reddit user profile information"""
        try:
            if username == "me":
                endpoint = "api/v1/me"
            else:
                endpoint = f"user/{username}/about"
            
            data = await self._make_request('GET', endpoint)
            
            if username == "me":
                user_data = data
            else:
                user_data = data.get('data', {})
            
            if not user_data:
                return None
            
            return ProfileData(
                user_id=user_data.get('name', username),
                username=user_data.get('name', username),
                display_name=user_data.get('subreddit', {}).get('display_name') or user_data.get('name', username),
                bio=user_data.get('subreddit', {}).get('public_description'),
                post_count=user_data.get('link_karma', 0),
                verified=user_data.get('verified', False),
                profile_url=f"https://reddit.com/u/{user_data.get('name', username)}",
                avatar_url=user_data.get('icon_img', '').split('?')[0] if user_data.get('icon_img') else None,
                created_at=datetime.fromtimestamp(user_data.get('created_utc', 0), tz=timezone.utc) if user_data.get('created_utc') else None,
                metadata={
                    'platform': 'reddit',
                    'comment_karma': user_data.get('comment_karma', 0),
                    'link_karma': user_data.get('link_karma', 0),
                    'total_karma': user_data.get('total_karma', 0),
                    'is_gold': user_data.get('is_gold', False),
                    'is_mod': user_data.get('is_mod', False),
                    'has_verified_email': user_data.get('has_verified_email', False),
                    'account_age_days': (datetime.now(timezone.utc) - datetime.fromtimestamp(user_data.get('created_utc', 0), tz=timezone.utc)).days if user_data.get('created_utc') else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit profile: {str(e)}")
            return None
    
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for Reddit post or comment"""
        try:
            # Determine if it's a post or comment based on ID format
            if content_id.startswith('t3_'):
                # It's a post
                post_id = content_id[3:]  # Remove 't3_' prefix
                endpoint = f"comments/{post_id}"
            else:
                # Assume it's a post ID without prefix
                endpoint = f"comments/{content_id}"
            
            data = await self._make_request('GET', endpoint)
            
            if not data or len(data) < 1:
                return None
            
            post_data = data[0]['data']['children'][0]['data']
            
            return EngagementMetrics(
                views=post_data.get('view_count', 0),
                likes=post_data.get('ups', 0),
                comments=post_data.get('num_comments', 0),
                shares=0,  # Reddit doesn't provide share count
                engagement_rate=self._calculate_engagement_rate(post_data),
                metadata={
                    'platform': 'reddit',
                    'content_id': content_id,
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'downs': post_data.get('downs', 0),
                    'subreddit': post_data.get('subreddit'),
                    'gilded': post_data.get('gilded', 0),
                    'awards': len(post_data.get('all_awardings', []))
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit engagement metrics: {str(e)}")
            return None
    
    def _calculate_engagement_rate(self, post_data: Dict[str, Any]) -> float:
        """Calculate engagement rate for Reddit content"""
        try:
            score = post_data.get('score', 0)
            num_comments = post_data.get('num_comments', 0)
            view_count = post_data.get('view_count', 0)
            
            total_engagement = score + num_comments
            
            if view_count > 0:
                return (total_engagement / view_count) * 100
            elif score > 0:
                # Estimate engagement based on score
                return min((total_engagement / max(score * 10, 100)) * 100, 100)
            return 0.0
        except:
            return 0.0
    
    async def get_subreddit_info(self, subreddit_name: str) -> Dict[str, Any]:
        """Get subreddit information and statistics"""
        try:
            endpoint = f"r/{subreddit_name}/about"
            data = await self._make_request('GET', endpoint)
            
            subreddit_data = data.get('data', {})
            
            return {
                'name': subreddit_data.get('display_name'),
                'title': subreddit_data.get('title'),
                'description': subreddit_data.get('public_description'),
                'subscribers': subreddit_data.get('subscribers', 0),
                'active_users': subreddit_data.get('active_user_count', 0),
                'created_at': datetime.fromtimestamp(subreddit_data.get('created_utc', 0), tz=timezone.utc).isoformat() if subreddit_data.get('created_utc') else None,
                'nsfw': subreddit_data.get('over18', False),
                'submission_type': subreddit_data.get('submission_type'),
                'subreddit_type': subreddit_data.get('subreddit_type'),
                'url': f"https://reddit.com/r/{subreddit_name}",
                'rules': await self._get_subreddit_rules(subreddit_name),
                'platform': 'reddit'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit subreddit info: {str(e)}")
            return {}
    
    async def _get_subreddit_rules(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """Get subreddit rules"""
        try:
            endpoint = f"r/{subreddit_name}/about/rules"
            data = await self._make_request('GET', endpoint)
            
            rules = []
            for rule in data.get('rules', []):
                rules.append({
                    'short_name': rule.get('short_name'),
                    'description': rule.get('description'),
                    'kind': rule.get('kind'),
                    'violation_reason': rule.get('violation_reason')
                })
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Error getting subreddit rules: {str(e)}")
            return []
    
    async def get_subreddit_posts(self, subreddit_name: str, sort: str = 'hot', 
                                limit: int = 25, time_filter: str = 'day') -> List[Dict[str, Any]]:
        """Get posts from a subreddit"""
        try:
            endpoint = f"r/{subreddit_name}/{sort}"
            params = {
                'limit': min(limit, 100),
                't': time_filter  # hour, day, week, month, year, all
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            posts = []
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                
                post_info = {
                    'id': post_data.get('id'),
                    'title': post_data.get('title'),
                    'author': post_data.get('author'),
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc'),
                    'url': post_data.get('url'),
                    'permalink': f"https://reddit.com{post_data.get('permalink')}",
                    'selftext': post_data.get('selftext', ''),
                    'is_self': post_data.get('is_self', False),
                    'gilded': post_data.get('gilded', 0),
                    'awards': len(post_data.get('all_awardings', [])),
                    'flair': post_data.get('link_flair_text'),
                    'nsfw': post_data.get('over_18', False)
                }
                
                posts.append(post_info)
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit subreddit posts: {str(e)}")
            return []
    
    async def search_subreddits(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search for subreddits"""
        try:
            endpoint = "subreddits/search"
            params = {
                'q': query,
                'limit': min(limit, 100),
                'type': 'sr'
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            subreddits = []
            for subreddit in data.get('data', {}).get('children', []):
                sr_data = subreddit.get('data', {})
                
                subreddit_info = {
                    'name': sr_data.get('display_name'),
                    'title': sr_data.get('title'),
                    'description': sr_data.get('public_description'),
                    'subscribers': sr_data.get('subscribers', 0),
                    'active_users': sr_data.get('active_user_count', 0),
                    'nsfw': sr_data.get('over18', False),
                    'url': f"https://reddit.com/r/{sr_data.get('display_name')}",
                    'icon': sr_data.get('icon_img', '').split('?')[0] if sr_data.get('icon_img') else None
                }
                
                subreddits.append(subreddit_info)
            
            return subreddits
            
        except Exception as e:
            self.logger.error(f"Error searching Reddit subreddits: {str(e)}")
            return []
    
    async def get_user_posts(self, username: str, sort: str = 'new', limit: int = 25) -> List[Dict[str, Any]]:
        """Get posts by a specific user"""
        try:
            endpoint = f"user/{username}/submitted"
            params = {
                'sort': sort,
                'limit': min(limit, 100)
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            posts = []
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                
                post_info = {
                    'id': post_data.get('id'),
                    'title': post_data.get('title'),
                    'subreddit': post_data.get('subreddit'),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc'),
                    'url': post_data.get('url'),
                    'permalink': f"https://reddit.com{post_data.get('permalink')}",
                    'selftext': post_data.get('selftext', ''),
                    'gilded': post_data.get('gilded', 0)
                }
                
                posts.append(post_info)
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit user posts: {str(e)}")
            return []
    
    async def get_user_comments(self, username: str, sort: str = 'new', limit: int = 25) -> List[Dict[str, Any]]:
        """Get comments by a specific user"""
        try:
            endpoint = f"user/{username}/comments"
            params = {
                'sort': sort,
                'limit': min(limit, 100)
            }
            
            data = await self._make_request('GET', endpoint, params=params)
            
            comments = []
            for comment in data.get('data', {}).get('children', []):
                comment_data = comment.get('data', {})
                
                comment_info = {
                    'id': comment_data.get('id'),
                    'body': comment_data.get('body', ''),
                    'subreddit': comment_data.get('subreddit'),
                    'score': comment_data.get('score', 0),
                    'created_utc': comment_data.get('created_utc'),
                    'permalink': f"https://reddit.com{comment_data.get('permalink')}",
                    'parent_id': comment_data.get('parent_id'),
                    'link_id': comment_data.get('link_id'),
                    'gilded': comment_data.get('gilded', 0)
                }
                
                comments.append(comment_info)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit user comments: {str(e)}")
            return []
    
    async def analyze_user_activity(self, username: str) -> Dict[str, Any]:
        """Analyze user's Reddit activity and engagement patterns"""
        try:
            # Get user profile
            profile = await self.get_profile(username)
            if not profile:
                return {}
            
            # Get recent posts and comments
            posts = await self.get_user_posts(username, limit=50)
            comments = await self.get_user_comments(username, limit=50)
            
            # Analyze activity patterns
            total_posts = len(posts)
            total_comments = len(comments)
            
            # Calculate karma metrics
            post_karma = sum(post.get('score', 0) for post in posts)
            comment_karma = sum(comment.get('score', 0) for comment in comments)
            
            # Analyze subreddit activity
            subreddit_activity = {}
            for post in posts:
                subreddit = post.get('subreddit')
                if subreddit:
                    subreddit_activity[subreddit] = subreddit_activity.get(subreddit, 0) + 1
            
            for comment in comments:
                subreddit = comment.get('subreddit')
                if subreddit:
                    subreddit_activity[subreddit] = subreddit_activity.get(subreddit, 0) + 1
            
            # Get top subreddits
            top_subreddits = sorted(subreddit_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate activity frequency
            activity_frequency = self._calculate_activity_frequency(posts + comments)
            
            return {
                'profile': profile.__dict__,
                'activity_summary': {
                    'total_posts': total_posts,
                    'total_comments': total_comments,
                    'post_karma': post_karma,
                    'comment_karma': comment_karma,
                    'avg_post_score': post_karma / total_posts if total_posts > 0 else 0,
                    'avg_comment_score': comment_karma / total_comments if total_comments > 0 else 0
                },
                'subreddit_activity': {
                    'top_subreddits': [{'subreddit': sr, 'activity_count': count} for sr, count in top_subreddits],
                    'total_subreddits': len(subreddit_activity)
                },
                'activity_frequency': activity_frequency,
                'engagement_score': self._calculate_user_engagement_score(profile, posts, comments),
                'platform': 'reddit',
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Reddit user activity: {str(e)}")
            return {}
    
    def _calculate_activity_frequency(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate user activity frequency"""
        if len(activities) < 2:
            return {'frequency': 'insufficient_data', 'posts_per_week': 0}
        
        try:
            # Convert timestamps to datetime objects
            timestamps = []
            for activity in activities:
                if activity.get('created_utc'):
                    timestamp = datetime.fromtimestamp(activity['created_utc'], tz=timezone.utc)
                    timestamps.append(timestamp)
            
            if len(timestamps) < 2:
                return {'frequency': 'insufficient_data', 'posts_per_week': 0}
            
            timestamps.sort()
            
            # Calculate average days between activities
            intervals = [(timestamps[i] - timestamps[i-1]).days for i in range(1, len(timestamps))]
            avg_interval = sum(intervals) / len(intervals)
            
            activities_per_week = 7 / avg_interval if avg_interval > 0 else 0
            
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
                'activities_per_week': round(activities_per_week, 1),
                'avg_days_between_activities': round(avg_interval, 1)
            }
        except:
            return {'frequency': 'unknown', 'activities_per_week': 0}
    
    def _calculate_user_engagement_score(self, profile: ProfileData, posts: List[Dict], comments: List[Dict]) -> float:
        """Calculate user engagement score"""
        try:
            # Base score from karma
            total_karma = profile.metadata.get('total_karma', 0)
            karma_score = min(total_karma / 10000, 10)  # Max 10 points
            
            # Activity score
            total_activities = len(posts) + len(comments)
            activity_score = min(total_activities / 100, 10)  # Max 10 points
            
            # Account age score (older accounts are more valuable)
            account_age_days = profile.metadata.get('account_age_days', 0)
            age_score = min(account_age_days / 365, 5)  # Max 5 points for 1+ year old accounts
            
            # Engagement quality score
            avg_post_score = sum(post.get('score', 0) for post in posts) / len(posts) if posts else 0
            avg_comment_score = sum(comment.get('score', 0) for comment in comments) / len(comments) if comments else 0
            quality_score = min((avg_post_score + avg_comment_score) / 10, 5)  # Max 5 points
            
            total_score = karma_score + activity_score + age_score + quality_score
            return round(total_score, 2)
        except:
            return 0.0
    
    async def find_relevant_subreddits(self, keywords: List[str], min_subscribers: int = 1000) -> List[Dict[str, Any]]:
        """Find subreddits relevant to given keywords"""
        try:
            relevant_subreddits = []
            
            for keyword in keywords:
                subreddits = await self.search_subreddits(keyword, limit=20)
                
                for subreddit in subreddits:
                    if (subreddit.get('subscribers', 0) >= min_subscribers and 
                        subreddit not in relevant_subreddits):
                        
                        # Get additional info
                        detailed_info = await self.get_subreddit_info(subreddit['name'])
                        subreddit.update(detailed_info)
                        
                        relevant_subreddits.append(subreddit)
            
            # Sort by subscriber count
            relevant_subreddits.sort(key=lambda x: x.get('subscribers', 0), reverse=True)
            
            return relevant_subreddits[:50]  # Return top 50
            
        except Exception as e:
            self.logger.error(f"Error finding relevant subreddits: {str(e)}")
            return []
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This won't work in async context, but provides cleanup hint
            pass
