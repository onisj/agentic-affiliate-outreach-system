"""
Twitter Scraper

This module implements scraping functionality for Twitter profiles and content.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from aiohttp import ClientResponseError

from src.services.monitoring.monitoring import MonitoringService
from discovery.models.data_object import DataObject
from .base_scraper import BaseScraper
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class TwitterScraper(BaseScraper):
    """Scrapes data from Twitter profiles and content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a Twitter profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('twitter')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserProfileHeader']"))
            )
            
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'tweets': await self._extract_tweets(),
                'followers': await self._extract_followers(),
                'following': await self._extract_following(),
                'engagement': await self._extract_engagement()
            }
            
            logger.info(f"Successfully scraped Twitter profile: {profile_url}")
            return self._to_data_object("Twitter", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping Twitter profile {profile_url}")
            return self._to_data_object("Twitter", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Twitter profile {profile_url}")
            return self._to_data_object("Twitter", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific Twitter content (e.g., tweets)."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('twitter')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweet']"))
            )
            
            content_data = await self._extract_tweets()
            logger.info(f"Successfully scraped Twitter content: {content_url}")
            return self._to_data_object("Twitter", {'tweets': content_data})
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping Twitter content {content_url}")
            return self._to_data_object("Twitter", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Twitter content {content_url}")
            return self._to_data_object("Twitter", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from a Twitter profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('twitter')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserProfileStats']"))
            )
            
            network_data = {
                'followers': await self._extract_followers(),
                'following': await self._extract_following()
            }
            logger.info(f"Successfully scraped Twitter network: {profile_url}")
            return self._to_data_object("Twitter", network_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping Twitter network {profile_url}")
            return self._to_data_object("Twitter", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Twitter network {profile_url}")
            return self._to_data_object("Twitter", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic profile information."""
        try:
            header = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileHeader']")
            basic_info = {
                'name': self._get_element_text(header, "[data-testid='UserName']"),
                'username': self._get_element_text(header, "[data-testid='UserName'] span"),
                'bio': self._get_element_text(header, "[data-testid='UserDescription']"),
                'location': self._get_element_text(header, "[data-testid='UserProfileHeader_Items']"),
                'website': self._get_element_attribute(
                    header, "[data-testid='UserProfileHeader_Items'] a", "href"
                ),
                'join_date': self._get_element_text(header, "[data-testid='UserJoinDate']"),
                'profile_picture': self._get_element_attribute(
                    header, "[data-testid='UserAvatar'] img", "src"
                ),
                'metadata': self._extract_metadata(header)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting Twitter basic info")
            return {}
            
    async def _extract_tweets(self) -> List[Dict[str, Any]]:
        """Extract tweets from the profile."""
        try:
            tweets = []
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")
            
            for element in tweet_elements:
                tweet = {
                    'text': self._get_element_text(element, "[data-testid='tweetText']"),
                    'timestamp': self._get_element_attribute(element, "time", "datetime"),
                    'engagement': await self._get_tweet_engagement(element),
                    'media': await self._get_tweet_media(element),
                    'metadata': self._extract_metadata(element)
                }
                tweets.append(tweet)
                
            return tweets
            
        except Exception as e:
            self._handle_error(e, "extracting Twitter tweets")
            return []
            
    async def _extract_followers(self) -> Dict[str, Any]:
        """Extract follower information."""
        try:
            followers_section = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileStats']")
            followers = {
                'count': self._parse_count(
                    self._get_element_text(followers_section, "[data-testid='UserProfileStats_Item']").split()[0]
                ),
                'demographics': await self._get_follower_demographics(),
                'interests': await self._get_follower_interests(),
                'metadata': self._extract_metadata(followers_section)
            }
            return followers
            
        except Exception as e:
            self._handle_error(e, "extracting Twitter followers")
            return {}
            
    async def _extract_following(self) -> Dict[str, Any]:
        """Extract following information."""
        try:
            following_section = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileStats']")
            following = {
                'count': self._parse_count(
                    self._get_element_text(following_section, "[data-testid='UserProfileStats_Item']").split()[0]
                ),
                'categories': await self._get_following_categories(),
                'metadata': self._extract_metadata(following_section)
            }
            return following
            
        except Exception as e:
            self._handle_error(e, "extracting Twitter following")
            return {}
            
    async def _extract_engagement(self) -> Dict[str, Any]:
        """Extract engagement metrics."""
        try:
            engagement = {
                'tweets': await self._get_tweet_engagement_metrics(),
                'profile': await self._get_profile_engagement_metrics(),
                'audience': await self._get_audience_engagement_metrics()
            }
            return engagement
            
        except Exception as e:
            self._handle_error(e, "extracting Twitter engagement")
            return {}
            
    async def _get_tweet_engagement(self, element: Any) -> Dict[str, int]:
        """Get engagement metrics for a tweet."""
        try:
            metrics = {
                'replies': 0,
                'retweets': 0,
                'likes': 0
            }
            
            replies_element = element.find_element(By.CSS_SELECTOR, "[data-testid='reply']")
            if replies_element:
                metrics['replies'] = self._parse_count(replies_element.text)
                
            retweets_element = element.find_element(By.CSS_SELECTOR, "[data-testid='retweet']")
            if retweets_element:
                metrics['retweets'] = self._parse_count(retweets_element.text)
                
            likes_element = element.find_element(By.CSS_SELECTOR, "[data-testid='like']")
            if likes_element:
                metrics['likes'] = self._parse_count(likes_element.text)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Twitter tweet engagement")
            return {'replies': 0, 'retweets': 0, 'likes': 0}
            
    async def _get_tweet_media(self, element: Any) -> List[Dict[str, Any]]:
        """Get media from a tweet."""
        try:
            media = []
            media_elements = element.find_elements(By.CSS_SELECTOR, "[data-testid='tweetPhoto']")
            
            for media_element in media_elements:
                media_item = {
                    'type': 'image',
                    'url': media_element.get_attribute('src'),
                    'metadata': self._extract_metadata(media_element)
                }
                media.append(media_item)
                
            return media
            
        except Exception as e:
            self._handle_error(e, "getting Twitter tweet media")
            return []
            
    async def _get_follower_demographics(self) -> Dict[str, Any]:
        """Get follower demographics."""
        try:
            demographics = {
                'age_groups': {},
                'gender': {},
                'locations': {},
                'languages': {}
            }
            
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileHeader']")
            location_elements = profile.find_elements(By.CSS_SELECTOR, "[data-testid='UserProfileHeader_Items']")
            for element in location_elements:
                location = element.text
                demographics['locations'][location] = demographics['locations'].get(location, 0) + 1
                
            return demographics
            
        except Exception as e:
            self._handle_error(e, "getting Twitter follower demographics")
            return {}
            
    async def _get_follower_interests(self) -> List[Dict[str, Any]]:
        """Get follower interests."""
        try:
            interests = []
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileHeader']")
            topic_elements = profile.find_elements(By.CSS_SELECTOR, "[data-testid='UserDescription'] a")
            
            for element in topic_elements:
                interest = {
                    'name': element.text,
                    'type': 'hashtag' if element.text.startswith('#') else 'topic',
                    'metadata': self._extract_metadata(element)
                }
                interests.append(interest)
                
            return interests
            
        except Exception as e:
            self._handle_error(e, "getting Twitter follower interests")
            return []
            
    async def _get_following_categories(self) -> List[Dict[str, Any]]:
        """Get following categories."""
        try:
            categories = []
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileHeader']")
            category_elements = profile.find_elements(By.CSS_SELECTOR, "[data-testid='UserProfileHeader_Items']")
            
            for element in category_elements:
                category = {
                    'name': element.text,
                    'count': 0,  # Requires API for accurate counts
                    'metadata': self._extract_metadata(element)
                }
                categories.append(category)
                
            return categories
            
        except Exception as e:
            self._handle_error(e, "getting Twitter following categories")
            return []
            
    async def _get_tweet_engagement_metrics(self) -> Dict[str, float]:
        """Get tweet engagement metrics."""
        try:
            metrics = {
                'average_replies': 0,
                'average_retweets': 0,
                'average_likes': 0,
                'engagement_rate': 0
            }
            
            tweets = await self._extract_tweets()
            if tweets:
                total_replies = sum(tweet['engagement']['replies'] for tweet in tweets)
                total_retweets = sum(tweet['engagement']['retweets'] for tweet in tweets)
                total_likes = sum(tweet['engagement']['likes'] for tweet in tweets)
                
                metrics['average_replies'] = total_replies / len(tweets)
                metrics['average_retweets'] = total_retweets / len(tweets)
                metrics['average_likes'] = total_likes / len(tweets)
                
                total_engagement = total_replies + total_retweets + total_likes
                total_impressions = len(tweets) * 1000  # Estimated
                metrics['engagement_rate'] = total_engagement / total_impressions if total_impressions > 0 else 0
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Twitter tweet engagement metrics")
            return {}
            
    async def _get_profile_engagement_metrics(self) -> Dict[str, float]:
        """Get profile engagement metrics."""
        try:
            metrics = {
                'profile_views': 0,
                'profile_engagement_rate': 0,
                'follower_growth_rate': 0
            }
            
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileHeader']")
            views_element = profile.find_element(By.CSS_SELECTOR, "[data-testid='UserProfileStats_Item']")
            if views_element:
                metrics['profile_views'] = self._parse_count(views_element.text.split()[0])
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Twitter profile engagement metrics")
            return {}
            
    async def _get_audience_engagement_metrics(self) -> Dict[str, float]:
        """Get audience engagement metrics."""
        try:
            metrics = {
                'audience_activity': 0,
                'audience_growth_rate': 0,
                'audience_quality_score': 0
            }
            
            followers = await self._extract_followers()
            following = await self._extract_following()
            
            if followers and following:
                metrics['audience_activity'] = followers['count'] / following['count'] if following['count'] > 0 else 0
                metrics['audience_growth_rate'] = 0  # Requires historical data
                metrics['audience_quality_score'] = min(
                    metrics['audience_activity'] * 0.7 + metrics['audience_growth_rate'] * 0.3,
                    1
                )
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Twitter audience engagement metrics")
            return {} 