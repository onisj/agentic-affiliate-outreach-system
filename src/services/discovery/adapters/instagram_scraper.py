"""
Instagram Scraper

This module implements scraping functionality for Instagram profiles and content.
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

from services.monitoring import MonitoringService
from discovery.models.data_object import DataObject
from .base_scraper import BaseScraper
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class InstagramScraper(BaseScraper):
    """Scrapes data from Instagram profiles and content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape an Instagram profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('instagram')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "header"))
            )
            
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'posts': await self._extract_posts(),
                'followers': await self._extract_followers(),
                'following': await self._extract_following(),
                'engagement': await self._extract_engagement()
            }
            
            logger.info(f"Successfully scraped Instagram profile: {profile_url}")
            return self._to_data_object("Instagram", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping Instagram profile {profile_url}")
            return self._to_data_object("Instagram", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Instagram profile {profile_url}")
            return self._to_data_object("Instagram", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific Instagram content."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('instagram')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )
            
            content_data = await self._extract_post_details()
            logger.info(f"Successfully scraped Instagram content: {content_url}")
            return self._to_data_object("Instagram", content_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping Instagram content {content_url}")
            return self._to_data_object("Instagram", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Instagram content {content_url}")
            return self._to_data_object("Instagram", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from an Instagram profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('instagram')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "header"))
            )
            
            network_data = {
                'followers': await self._extract_followers(),
                'following': await self._extract_following(),
                'related_accounts': await self._extract_related_accounts()
            }
            logger.info(f"Successfully scraped Instagram network: {profile_url}")
            return self._to_data_object("Instagram", network_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping Instagram network {profile_url}")
            return self._to_data_object("Instagram", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Instagram network {profile_url}")
            return self._to_data_object("Instagram", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic profile information."""
        try:
            header = self.driver.find_element(By.CSS_SELECTOR, "header")
            basic_info = {
                'username': self._get_element_text(header, "h2"),
                'full_name': self._get_element_text(header, "h1"),
                'bio': self._get_element_text(header, "h1 + div"),
                'website': self._get_element_attribute(header, "a", "href"),
                'profile_picture': self._get_element_attribute(header, "img", "src"),
                'verified': bool(header.find_elements(By.CSS_SELECTOR, "svg[aria-label='Verified']")),
                'metadata': self._extract_metadata(header)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram basic info")
            return {}
            
    async def _extract_posts(self) -> List[Dict[str, Any]]:
        """Extract posts from the profile."""
        try:
            posts = []
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
            
            for element in post_elements:
                post = {
                    'url': self._get_element_attribute(element, "a", "href"),
                    'thumbnail': self._get_element_attribute(element, "img", "src"),
                    'caption': self._get_element_text(element, "div[role='button']"),
                    'likes': self._parse_count(self._get_element_text(element, "section span")),
                    'comments': self._parse_count(self._get_element_text(element, "ul li")),
                    'timestamp': self._get_element_attribute(element, "time", "datetime"),
                    'metadata': self._extract_metadata(element)
                }
                posts.append(post)
                
            return posts
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram posts")
            return []
            
    async def _extract_followers(self) -> Dict[str, Any]:
        """Extract follower information."""
        try:
            followers_section = self.driver.find_element(By.CSS_SELECTOR, "header ul li:nth-child(2)")
            followers = {
                'count': self._parse_count(followers_section.text),
                'demographics': await self._get_follower_demographics(),
                'growth_rate': await self._get_follower_growth_rate(),
                'metadata': self._extract_metadata(followers_section)
            }
            return followers
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram followers")
            return {}
            
    async def _extract_following(self) -> Dict[str, Any]:
        """Extract following information."""
        try:
            following_section = self.driver.find_element(By.CSS_SELECTOR, "header ul li:nth-child(3)")
            following = {
                'count': self._parse_count(following_section.text),
                'categories': await self._get_following_categories(),
                'metadata': self._extract_metadata(following_section)
            }
            return following
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram following")
            return {}
            
    async def _extract_engagement(self) -> Dict[str, Any]:
        """Extract engagement metrics."""
        try:
            engagement = {
                'posts': await self._get_post_engagement_metrics(),
                'profile': await self._get_profile_engagement_metrics(),
                'audience': await self._get_audience_engagement_metrics()
            }
            return engagement
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram engagement")
            return {}
            
    async def _extract_post_details(self) -> Dict[str, Any]:
        """Extract detailed post information."""
        try:
            post = {
                'caption': self._get_element_text(self.driver, "article div[role='button']"),
                'likes': self._parse_count(self._get_element_text(self.driver, "section span")),
                'comments': self._parse_count(self._get_element_text(self.driver, "ul li")),
                'timestamp': self._get_element_attribute(self.driver, "time", "datetime"),
                'location': self._get_element_text(self.driver, "a[role='link']"),
                'hashtags': await self._extract_hashtags(),
                'mentions': await self._extract_mentions(),
                'metadata': self._extract_metadata(self.driver)
            }
            return post
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram post details")
            return {}
            
    async def _extract_related_accounts(self) -> List[Dict[str, Any]]:
        """Extract related accounts."""
        try:
            related_accounts = []
            account_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] ul li")
            
            for element in account_elements:
                account = {
                    'username': self._get_element_text(element, "a"),
                    'full_name': self._get_element_text(element, "span"),
                    'profile_picture': self._get_element_attribute(element, "img", "src"),
                    'metadata': self._extract_metadata(element)
                }
                related_accounts.append(account)
                
            return related_accounts
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram related accounts")
            return []
            
    async def _extract_hashtags(self) -> List[str]:
        """Extract hashtags from a post."""
        try:
            hashtags = []
            caption = self._get_element_text(self.driver, "article div[role='button']")
            if caption:
                hashtags = [tag for tag in caption.split() if tag.startswith('#')]
            return hashtags
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram hashtags")
            return []
            
    async def _extract_mentions(self) -> List[str]:
        """Extract mentions from a post."""
        try:
            mentions = []
            caption = self._get_element_text(self.driver, "article div[role='button']")
            if caption:
                mentions = [mention for mention in caption.split() if mention.startswith('@')]
            return mentions
            
        except Exception as e:
            self._handle_error(e, "extracting Instagram mentions")
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
            
            # Requires Instagram Analytics API for accurate demographics
            return demographics
            
        except Exception as e:
            self._handle_error(e, "getting Instagram follower demographics")
            return {}
            
    async def _get_follower_growth_rate(self) -> float:
        """Get follower growth rate."""
        try:
            # Requires historical data
            return 0.0
            
        except Exception as e:
            self._handle_error(e, "getting Instagram follower growth rate")
            return 0.0
            
    async def _get_following_categories(self) -> List[Dict[str, Any]]:
        """Get following categories."""
        try:
            categories = []
            following_section = self.driver.find_element(By.CSS_SELECTOR, "header ul li:nth-child(3)")
            category_elements = following_section.find_elements(By.CSS_SELECTOR, "div[role='dialog'] ul li")
            
            for element in category_elements:
                category = {
                    'name': element.text,
                    'count': 0,  # Requires API for accurate counts
                    'metadata': self._extract_metadata(element)
                }
                categories.append(category)
                
            return categories
            
        except Exception as e:
            self._handle_error(e, "getting Instagram following categories")
            return []
            
    async def _get_post_engagement_metrics(self) -> Dict[str, float]:
        """Get post engagement metrics."""
        try:
            metrics = {
                'average_likes': 0,
                'average_comments': 0,
                'engagement_rate': 0
            }
            
            posts = await self._extract_posts()
            if posts:
                total_likes = sum(post['likes'] for post in posts)
                total_comments = sum(post['comments'] for post in posts)
                
                metrics['average_likes'] = total_likes / len(posts)
                metrics['average_comments'] = total_comments / len(posts)
                
                total_engagement = total_likes + total_comments
                total_followers = (await self._extract_followers())['count']
                metrics['engagement_rate'] = total_engagement / total_followers if total_followers > 0 else 0
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Instagram post engagement metrics")
            return {}
            
    async def _get_profile_engagement_metrics(self) -> Dict[str, float]:
        """Get profile engagement metrics."""
        try:
            metrics = {
                'profile_views': 0,
                'profile_engagement_rate': 0,
                'follower_growth_rate': 0
            }
            
            profile = self.driver.find_element(By.CSS_SELECTOR, "header")
            views_element = profile.find_element(By.CSS_SELECTOR, "div[role='button']")
            if views_element:
                metrics['profile_views'] = self._parse_count(views_element.text)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Instagram profile engagement metrics")
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
            posts = await self._extract_posts()
            
            if followers and posts:
                metrics['audience_activity'] = sum(post['likes'] + post['comments'] for post in posts) / followers['count'] if followers['count'] > 0 else 0
                metrics['audience_growth_rate'] = await self._get_follower_growth_rate()
                metrics['audience_quality_score'] = min(
                    metrics['audience_activity'] * 0.7 + metrics['audience_growth_rate'] * 0.3,
                    1
                )
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Instagram audience engagement metrics")
            return {} 