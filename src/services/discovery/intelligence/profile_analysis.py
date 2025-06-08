"""
Profile Analysis AI

This module implements AI-powered profile analysis for Twitter and Reddit data
to support affiliate discovery.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import re
from collections import Counter, defaultdict
import numpy as np
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

from services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class ProfileAnalysisAI:
    """AI-powered profile analysis for Twitter and Reddit data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {str(e)}")
            
        # Initialize NLTK components
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
    async def analyze_profile(self, profile_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Analyze profile from Twitter or Reddit."""
        try:
            if platform.lower() == 'twitter':
                return await self._analyze_twitter_profile(profile_data)
            elif platform.lower() == 'reddit':
                return await self._analyze_reddit_profile(profile_data)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing profile: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def _analyze_twitter_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Twitter profile."""
        try:
            # Assess profile quality
            profile_quality = await self._assess_profile_quality(profile_data)
            
            # Calculate engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics(profile_data)
            
            # Analyze content patterns
            content_analysis = await self._analyze_content_patterns(profile_data)
            
            # Calculate influence score
            influence_score = await self._calculate_influence_score(profile_data)
            
            # Assess affiliate potential
            affiliate_potential = await self._assess_affiliate_potential(profile_data)
            
            # Analyze audience
            audience_analysis = await self._analyze_audience(profile_data)
            
            return {
                'profile_quality': profile_quality,
                'engagement_metrics': engagement_metrics,
                'content_analysis': content_analysis,
                'influence_score': influence_score,
                'affiliate_potential': affiliate_potential,
                'audience_analysis': audience_analysis
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing Twitter profile: {str(e)}")
            raise
            
    async def _analyze_reddit_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Reddit profile."""
        try:
            # Assess profile quality
            profile_quality = await self._assess_profile_quality(profile_data)
            
            # Calculate engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics(profile_data)
            
            # Analyze content patterns
            content_analysis = await self._analyze_content_patterns(profile_data)
            
            # Calculate influence score
            influence_score = await self._calculate_influence_score(profile_data)
            
            # Assess affiliate potential
            affiliate_potential = await self._assess_affiliate_potential(profile_data)
            
            # Analyze subreddit activity
            subreddit_analysis = await self._analyze_subreddit_activity(profile_data)
            
            return {
                'profile_quality': profile_quality,
                'engagement_metrics': engagement_metrics,
                'content_analysis': content_analysis,
                'influence_score': influence_score,
                'affiliate_potential': affiliate_potential,
                'subreddit_analysis': subreddit_analysis
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing Reddit profile: {str(e)}")
            raise
            
    async def _assess_profile_quality(self, profile_data: Dict[str, Any]) -> Dict[str, float]:
        """Assess profile quality metrics."""
        try:
            # Calculate completeness score
            completeness_score = self._calculate_completeness_score(profile_data)
            
            # Check verification status
            is_verified = profile_data.get('verified', False)
            
            # Calculate account age
            account_age = self._calculate_account_age(profile_data)
            
            # Calculate activity level
            activity_level = await self._calculate_activity_level(profile_data)
            
            # Calculate overall quality score
            quality_score = (
                0.3 * completeness_score +
                0.2 * (1 if is_verified else 0) +
                0.3 * min(account_age / 365, 1) +  # Normalize to 0-1
                0.2 * activity_level
            )
            
            return {
                'completeness_score': completeness_score,
                'is_verified': is_verified,
                'account_age_days': account_age,
                'activity_level': activity_level,
                'quality_score': quality_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error assessing profile quality: {str(e)}")
            return {
                'completeness_score': 0,
                'is_verified': False,
                'account_age_days': 0,
                'activity_level': 0,
                'quality_score': 0
            }
            
    def _calculate_completeness_score(self, profile_data: Dict[str, Any]) -> float:
        """Calculate profile completeness score."""
        try:
            required_fields = [
                'username', 'bio', 'location', 'website',
                'profile_image', 'banner_image'
            ]
            
            filled_fields = sum(1 for field in required_fields if profile_data.get(field))
            return filled_fields / len(required_fields)
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating completeness score: {str(e)}")
            return 0
            
    def _calculate_account_age(self, profile_data: Dict[str, Any]) -> int:
        """Calculate account age in days."""
        try:
            created_at = profile_data.get('created_at')
            if not created_at:
                return 0
                
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age = datetime.now(created_date.tzinfo) - created_date
            return age.days
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating account age: {str(e)}")
            return 0
            
    async def _calculate_activity_level(self, profile_data: Dict[str, Any]) -> float:
        """Calculate profile activity level."""
        try:
            # Get recent activity
            recent_posts = profile_data.get('recent_posts', [])
            recent_comments = profile_data.get('recent_comments', [])
            
            # Calculate post frequency
            post_count = len(recent_posts)
            comment_count = len(recent_comments)
            
            # Calculate activity score
            activity_score = min((post_count + comment_count) / 100, 1.0)
            
            return activity_score
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating activity level: {str(e)}")
            return 0
            
    async def _calculate_engagement_metrics(self, profile_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate engagement metrics."""
        try:
            # Extract metrics
            followers = profile_data.get('followers', 1)  # Avoid division by zero
            following = profile_data.get('following', 0)
            likes = profile_data.get('likes', 0)
            comments = profile_data.get('comments', 0)
            shares = profile_data.get('shares', 0)
            
            # Calculate engagement rates
            engagement_rate = (likes + comments + shares) / followers
            comment_rate = comments / followers
            share_rate = shares / followers
            
            # Calculate interaction quality
            interaction_quality = (
                0.4 * (likes / followers) +
                0.4 * (comments / followers) +
                0.2 * (shares / followers)
            )
            
            return {
                'engagement_rate': engagement_rate,
                'comment_rate': comment_rate,
                'share_rate': share_rate,
                'interaction_quality': interaction_quality,
                'follower_ratio': following / followers if followers > 0 else 0
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating engagement metrics: {str(e)}")
            return {
                'engagement_rate': 0,
                'comment_rate': 0,
                'share_rate': 0,
                'interaction_quality': 0,
                'follower_ratio': 0
            }
            
    async def _analyze_content_patterns(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content patterns."""
        try:
            # Get recent content
            recent_posts = profile_data.get('recent_posts', [])
            
            # Analyze content types
            content_types = self._analyze_content_types(recent_posts)
            
            # Calculate posting frequency
            posting_frequency = self._calculate_posting_frequency(recent_posts)
            
            # Analyze topic diversity
            topic_diversity = await self._analyze_topic_diversity(recent_posts)
            
            # Check for affiliate-related content
            affiliate_content = self._has_affiliate_content(recent_posts)
            
            return {
                'content_types': content_types,
                'posting_frequency': posting_frequency,
                'topic_diversity': topic_diversity,
                'has_affiliate_content': affiliate_content
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing content patterns: {str(e)}")
            return {
                'content_types': {},
                'posting_frequency': 0,
                'topic_diversity': 0,
                'has_affiliate_content': False
            }
            
    def _analyze_content_types(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze content types in posts."""
        try:
            content_types = defaultdict(int)
            
            for post in posts:
                if post.get('is_video'):
                    content_types['video'] += 1
                elif post.get('is_image'):
                    content_types['image'] += 1
                elif post.get('is_link'):
                    content_types['link'] += 1
                else:
                    content_types['text'] += 1
                    
            return dict(content_types)
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing content types: {str(e)}")
            return {}
            
    def _calculate_posting_frequency(self, posts: List[Dict[str, Any]]) -> float:
        """Calculate average posts per day."""
        try:
            if not posts:
                return 0
                
            # Get post dates
            post_dates = [
                datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
                for p in posts
                if 'created_at' in p
            ]
            
            if not post_dates:
                return 0
                
            # Calculate date range
            date_range = max(post_dates) - min(post_dates)
            days = max(date_range.days, 1)  # Avoid division by zero
            
            return len(posts) / days
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating posting frequency: {str(e)}")
            return 0
            
    async def _analyze_topic_diversity(self, posts: List[Dict[str, Any]]) -> float:
        """Analyze topic diversity in posts."""
        try:
            if not posts:
                return 0
                
            # Extract text from posts
            texts = [p.get('text', '') for p in posts]
            combined_text = ' '.join(texts)
            
            # Extract topics
            topics = await self._extract_topics(combined_text)
            
            # Calculate diversity score
            unique_topics = len(set(topics))
            total_topics = len(topics)
            
            return unique_topics / total_topics if total_topics > 0 else 0
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing topic diversity: {str(e)}")
            return 0
            
    def _has_affiliate_content(self, posts: List[Dict[str, Any]]) -> bool:
        """Check for affiliate-related content."""
        try:
            affiliate_terms = [
                'affiliate', 'commission', 'referral', 'partner',
                'sponsored', 'promotion', 'discount', 'code',
                'link', 'click', 'buy', 'purchase'
            ]
            
            for post in posts:
                text = post.get('text', '').lower()
                if any(term in text for term in affiliate_terms):
                    return True
                    
            return False
            
        except Exception as e:
            self.monitoring.log_error(f"Error checking affiliate content: {str(e)}")
            return False
            
    async def _calculate_influence_score(self, profile_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate influence score."""
        try:
            # Extract metrics
            followers = profile_data.get('followers', 0)
            engagement_rate = profile_data.get('engagement_rate', 0)
            content_quality = profile_data.get('content_quality', 0)
            
            # Calculate influence components
            follower_quality = min(followers / 10000, 1.0)  # Normalize to 0-1
            engagement_quality = min(engagement_rate * 10, 1.0)  # Normalize to 0-1
            
            # Calculate overall influence score
            influence_score = (
                0.4 * follower_quality +
                0.4 * engagement_quality +
                0.2 * content_quality
            )
            
            return {
                'follower_quality': follower_quality,
                'engagement_quality': engagement_quality,
                'content_quality': content_quality,
                'influence_score': influence_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating influence score: {str(e)}")
            return {
                'follower_quality': 0,
                'engagement_quality': 0,
                'content_quality': 0,
                'influence_score': 0
            }
            
    async def _assess_affiliate_potential(self, profile_data: Dict[str, Any]) -> Dict[str, float]:
        """Assess affiliate marketing potential."""
        try:
            # Extract metrics
            followers = profile_data.get('followers', 0)
            engagement_rate = profile_data.get('engagement_rate', 0)
            content_quality = profile_data.get('content_quality', 0)
            has_affiliate_content = profile_data.get('has_affiliate_content', False)
            
            # Calculate potential components
            audience_size = min(followers / 1000, 1.0)  # Normalize to 0-1
            engagement_potential = min(engagement_rate * 10, 1.0)  # Normalize to 0-1
            content_relevance = 0.5 if has_affiliate_content else 0.2
            
            # Calculate overall potential score
            potential_score = (
                0.3 * audience_size +
                0.3 * engagement_potential +
                0.2 * content_quality +
                0.2 * content_relevance
            )
            
            return {
                'audience_size': audience_size,
                'engagement_potential': engagement_potential,
                'content_relevance': content_relevance,
                'potential_score': potential_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error assessing affiliate potential: {str(e)}")
            return {
                'audience_size': 0,
                'engagement_potential': 0,
                'content_relevance': 0,
                'potential_score': 0
            }
            
    async def _analyze_audience(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience characteristics."""
        try:
            # Extract audience data
            audience = profile_data.get('audience', {})
            
            # Analyze demographics
            demographics = self._analyze_demographics(audience)
            
            # Analyze interests
            interests = self._analyze_interests(audience)
            
            # Analyze engagement patterns
            engagement_patterns = self._analyze_engagement_patterns(audience)
            
            # Calculate audience affinity
            affinity_score = self._calculate_audience_affinity(demographics, interests)
            
            return {
                'demographics': demographics,
                'interests': interests,
                'engagement_patterns': engagement_patterns,
                'affinity_score': affinity_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing audience: {str(e)}")
            return {
                'demographics': {},
                'interests': {},
                'engagement_patterns': {},
                'affinity_score': 0
            }
            
    def _analyze_demographics(self, audience: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience demographics."""
        try:
            demographics = audience.get('demographics', {})
            
            return {
                'age_groups': demographics.get('age_groups', {}),
                'gender_distribution': demographics.get('gender_distribution', {}),
                'location_distribution': demographics.get('location_distribution', {}),
                'language_distribution': demographics.get('language_distribution', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing demographics: {str(e)}")
            return {}
            
    def _analyze_interests(self, audience: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience interests."""
        try:
            interests = audience.get('interests', {})
            
            return {
                'top_interests': interests.get('top_interests', []),
                'interest_categories': interests.get('interest_categories', {}),
                'brand_affinities': interests.get('brand_affinities', [])
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing interests: {str(e)}")
            return {}
            
    def _analyze_engagement_patterns(self, audience: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience engagement patterns."""
        try:
            engagement = audience.get('engagement', {})
            
            return {
                'active_hours': engagement.get('active_hours', {}),
                'engagement_frequency': engagement.get('engagement_frequency', {}),
                'content_preferences': engagement.get('content_preferences', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement patterns: {str(e)}")
            return {}
            
    def _calculate_audience_affinity(
        self,
        demographics: Dict[str, Any],
        interests: Dict[str, Any]
    ) -> float:
        """Calculate audience affinity score."""
        try:
            # Define target demographics and interests
            target_demographics = {
                'age_groups': ['25-34', '35-44'],
                'gender_distribution': {'male': 0.4, 'female': 0.6}
            }
            
            target_interests = [
                'technology', 'business', 'marketing',
                'entrepreneurship', 'e-commerce'
            ]
            
            # Calculate demographic match
            demo_score = 0
            if 'age_groups' in demographics:
                age_match = sum(
                    demographics['age_groups'].get(age, 0)
                    for age in target_demographics['age_groups']
                )
                demo_score += age_match * 0.5
                
            if 'gender_distribution' in demographics:
                gender_match = sum(
                    abs(demographics['gender_distribution'].get(gender, 0) - target)
                    for gender, target in target_demographics['gender_distribution'].items()
                )
                demo_score += (1 - gender_match) * 0.5
                
            # Calculate interest match
            interest_score = 0
            if 'top_interests' in interests:
                interest_match = sum(
                    1 for interest in interests['top_interests']
                    if interest.lower() in target_interests
                )
                interest_score = interest_match / len(target_interests)
                
            # Calculate overall affinity score
            affinity_score = 0.4 * demo_score + 0.6 * interest_score
            
            return affinity_score
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating audience affinity: {str(e)}")
            return 0
            
    async def _analyze_subreddit_activity(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze subreddit activity for Reddit profiles."""
        try:
            # Extract subreddit data
            subreddits = profile_data.get('subreddits', [])
            
            # Analyze active subreddits
            active_subreddits = self._analyze_active_subreddits(subreddits)
            
            # Analyze subreddit engagement
            subreddit_engagement = self._analyze_subreddit_engagement(subreddits)
            
            # Analyze topic distribution
            topic_distribution = self._analyze_topic_distribution(subreddits)
            
            # Check moderation status
            moderation_status = self._check_moderation_status(subreddits)
            
            return {
                'active_subreddits': active_subreddits,
                'subreddit_engagement': subreddit_engagement,
                'topic_distribution': topic_distribution,
                'moderation_status': moderation_status
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing subreddit activity: {str(e)}")
            return {
                'active_subreddits': [],
                'subreddit_engagement': {},
                'topic_distribution': {},
                'moderation_status': False
            }
            
    def _analyze_active_subreddits(self, subreddits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze active subreddits."""
        try:
            active_subreddits = []
            
            for subreddit in subreddits:
                if subreddit.get('post_count', 0) > 0 or subreddit.get('comment_count', 0) > 0:
                    active_subreddits.append({
                        'name': subreddit.get('name'),
                        'post_count': subreddit.get('post_count', 0),
                        'comment_count': subreddit.get('comment_count', 0),
                        'karma': subreddit.get('karma', 0)
                    })
                    
            return sorted(
                active_subreddits,
                key=lambda x: x['post_count'] + x['comment_count'],
                reverse=True
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing active subreddits: {str(e)}")
            return []
            
    def _analyze_subreddit_engagement(self, subreddits: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze subreddit engagement metrics."""
        try:
            engagement_metrics = {
                'total_karma': 0,
                'avg_karma_per_post': 0,
                'avg_karma_per_comment': 0,
                'engagement_rate': 0
            }
            
            total_posts = sum(s.get('post_count', 0) for s in subreddits)
            total_comments = sum(s.get('comment_count', 0) for s in subreddits)
            total_karma = sum(s.get('karma', 0) for s in subreddits)
            
            if total_posts > 0:
                engagement_metrics['avg_karma_per_post'] = total_karma / total_posts
            if total_comments > 0:
                engagement_metrics['avg_karma_per_comment'] = total_karma / total_comments
                
            engagement_metrics['total_karma'] = total_karma
            engagement_metrics['engagement_rate'] = (total_posts + total_comments) / len(subreddits) if subreddits else 0
            
            return engagement_metrics
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing subreddit engagement: {str(e)}")
            return {
                'total_karma': 0,
                'avg_karma_per_post': 0,
                'avg_karma_per_comment': 0,
                'engagement_rate': 0
            }
            
    def _analyze_topic_distribution(self, subreddits: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze topic distribution across subreddits."""
        try:
            topic_counts = Counter()
            
            for subreddit in subreddits:
                if 'topics' in subreddit:
                    topic_counts.update(subreddit['topics'])
                    
            total_topics = sum(topic_counts.values())
            
            return {
                topic: count / total_topics
                for topic, count in topic_counts.most_common(10)
            } if total_topics > 0 else {}
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing topic distribution: {str(e)}")
            return {}
            
    def _check_moderation_status(self, subreddits: List[Dict[str, Any]]) -> bool:
        """Check if user is a moderator in any subreddit."""
        try:
            return any(s.get('is_moderator', False) for s in subreddits)
            
        except Exception as e:
            self.monitoring.log_error(f"Error checking moderation status: {str(e)}")
            return False 