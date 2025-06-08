"""
TikTok Scraper

This module implements scraping functionality for TikTok profiles and content.
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

class TikTokScraper(BaseScraper):
    """Scrapes data from TikTok profiles and content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a TikTok profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('tiktok')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-info']"))
            )
            
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'videos': await self._extract_videos(),
                'followers': await self._extract_followers(),
                'following': await self._extract_following(),
                'engagement': await self._extract_engagement()
            }
            
            logger.info(f"Successfully scraped TikTok profile: {profile_url}")
            return self._to_data_object("TikTok", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping TikTok profile {profile_url}")
            return self._to_data_object("TikTok", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping TikTok profile {profile_url}")
            return self._to_data_object("TikTok", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific TikTok content."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('tiktok')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='video-player']"))
            )
            
            content_data = await self._extract_video_details()
            logger.info(f"Successfully scraped TikTok content: {content_url}")
            return self._to_data_object("TikTok", content_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping TikTok content {content_url}")
            return self._to_data_object("TikTok", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping TikTok content {content_url}")
            return self._to_data_object("TikTok", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from a TikTok profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('tiktok')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='user-info']"))
            )
            
            network_data = {
                'followers': await self._extract_followers(),
                'following': await self._extract_following(),
                'related_accounts': await self._extract_related_accounts()
            }
            logger.info(f"Successfully scraped TikTok network: {profile_url}")
            return self._to_data_object("TikTok", network_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping TikTok network {profile_url}")
            return self._to_data_object("TikTok", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping TikTok network {profile_url}")
            return self._to_data_object("TikTok", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic profile information."""
        try:
            header = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-info']")
            basic_info = {
                'username': self._get_element_text(header, "[data-e2e='user-info-username']"),
                'nickname': self._get_element_text(header, "[data-e2e='user-info-nickname']"),
                'bio': self._get_element_text(header, "[data-e2e='user-info-bio']"),
                'profile_picture': self._get_element_attribute(header, "[data-e2e='user-info-avatar'] img", "src"),
                'verified': bool(header.find_elements(By.CSS_SELECTOR, "[data-e2e='user-info-verified']")),
                'metadata': self._extract_metadata(header)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok basic info")
            return {}
            
    async def _extract_videos(self) -> List[Dict[str, Any]]:
        """Extract videos from the profile."""
        try:
            videos = []
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-e2e='user-post-item']")
            
            for element in video_elements:
                video = {
                    'url': self._get_element_attribute(element, "a", "href"),
                    'thumbnail': self._get_element_attribute(element, "img", "src"),
                    'description': self._get_element_text(element, "[data-e2e='user-post-item-desc']"),
                    'likes': self._parse_count(self._get_element_text(element, "[data-e2e='like-count']")),
                    'comments': self._parse_count(self._get_element_text(element, "[data-e2e='comment-count']")),
                    'shares': self._parse_count(self._get_element_text(element, "[data-e2e='share-count']")),
                    'metadata': self._extract_metadata(element)
                }
                videos.append(video)
                
            return videos
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok videos")
            return []
            
    async def _extract_followers(self) -> Dict[str, Any]:
        """Extract follower information."""
        try:
            followers_section = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-info-followers']")
            followers = {
                'count': self._parse_count(followers_section.text),
                'demographics': await self._get_follower_demographics(),
                'growth_rate': await self._get_follower_growth_rate(),
                'metadata': self._extract_metadata(followers_section)
            }
            return followers
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok followers")
            return {}
            
    async def _extract_following(self) -> Dict[str, Any]:
        """Extract following information."""
        try:
            following_section = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-info-following']")
            following = {
                'count': self._parse_count(following_section.text),
                'categories': await self._get_following_categories(),
                'metadata': self._extract_metadata(following_section)
            }
            return following
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok following")
            return {}
            
    async def _extract_engagement(self) -> Dict[str, Any]:
        """Extract engagement metrics."""
        try:
            engagement = {
                'videos': await self._get_video_engagement_metrics(),
                'profile': await self._get_profile_engagement_metrics(),
                'audience': await self._get_audience_engagement_metrics()
            }
            return engagement
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok engagement")
            return {}
            
    async def _extract_video_details(self) -> Dict[str, Any]:
        """Extract detailed video information."""
        try:
            video = {
                'description': self._get_element_text(self.driver, "[data-e2e='video-desc']"),
                'likes': self._parse_count(self._get_element_text(self.driver, "[data-e2e='like-count']")),
                'comments': self._parse_count(self._get_element_text(self.driver, "[data-e2e='comment-count']")),
                'shares': self._parse_count(self._get_element_text(self.driver, "[data-e2e='share-count']")),
                'views': self._parse_count(self._get_element_text(self.driver, "[data-e2e='video-views']")),
                'sound': self._get_element_text(self.driver, "[data-e2e='video-sound']"),
                'metadata': self._extract_metadata(self.driver)
            }
            return video
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok video details")
            return {}
            
    async def _extract_related_accounts(self) -> List[Dict[str, Any]]:
        """Extract related accounts."""
        try:
            related_accounts = []
            account_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-e2e='suggested-user-item']")
            
            for element in account_elements:
                account = {
                    'username': self._get_element_text(element, "[data-e2e='suggested-user-username']"),
                    'nickname': self._get_element_text(element, "[data-e2e='suggested-user-nickname']"),
                    'followers': self._parse_count(self._get_element_text(element, "[data-e2e='suggested-user-followers']")),
                    'metadata': self._extract_metadata(element)
                }
                related_accounts.append(account)
                
            return related_accounts
            
        except Exception as e:
            self._handle_error(e, "extracting TikTok related accounts")
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
            
            # Requires TikTok Analytics API for accurate demographics
            return demographics
            
        except Exception as e:
            self._handle_error(e, "getting TikTok follower demographics")
            return {}
            
    async def _get_follower_growth_rate(self) -> float:
        """Get follower growth rate."""
        try:
            # Requires historical data
            return 0.0
            
        except Exception as e:
            self._handle_error(e, "getting TikTok follower growth rate")
            return 0.0
            
    async def _get_following_categories(self) -> List[Dict[str, Any]]:
        """Get following categories."""
        try:
            categories = []
            following_section = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-info-following']")
            category_elements = following_section.find_elements(By.CSS_SELECTOR, "[data-e2e='following-category']")
            
            for element in category_elements:
                category = {
                    'name': element.text,
                    'count': 0,  # Requires API for accurate counts
                    'metadata': self._extract_metadata(element)
                }
                categories.append(category)
                
            return categories
            
        except Exception as e:
            self._handle_error(e, "getting TikTok following categories")
            return []
            
    async def _get_video_engagement_metrics(self) -> Dict[str, float]:
        """Get video engagement metrics."""
        try:
            metrics = {
                'average_views': 0,
                'average_likes': 0,
                'average_comments': 0,
                'average_shares': 0,
                'engagement_rate': 0
            }
            
            videos = await self._extract_videos()
            if videos:
                total_views = sum(video.get('views', 0) for video in videos)
                total_likes = sum(video['likes'] for video in videos)
                total_comments = sum(video['comments'] for video in videos)
                total_shares = sum(video['shares'] for video in videos)
                
                metrics['average_views'] = total_views / len(videos)
                metrics['average_likes'] = total_likes / len(videos)
                metrics['average_comments'] = total_comments / len(videos)
                metrics['average_shares'] = total_shares / len(videos)
                
                total_engagement = total_likes + total_comments + total_shares
                metrics['engagement_rate'] = total_engagement / total_views if total_views > 0 else 0
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting TikTok video engagement metrics")
            return {}
            
    async def _get_profile_engagement_metrics(self) -> Dict[str, float]:
        """Get profile engagement metrics."""
        try:
            metrics = {
                'profile_views': 0,
                'profile_engagement_rate': 0,
                'follower_growth_rate': 0
            }
            
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-info']")
            views_element = profile.find_element(By.CSS_SELECTOR, "[data-e2e='user-info-views']")
            if views_element:
                metrics['profile_views'] = self._parse_count(views_element.text)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting TikTok profile engagement metrics")
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
            videos = await self._extract_videos()
            
            if followers and videos:
                metrics['audience_activity'] = sum(video.get('views', 0) for video in videos) / followers['count'] if followers['count'] > 0 else 0
                metrics['audience_growth_rate'] = await self._get_follower_growth_rate()
                metrics['audience_quality_score'] = min(
                    metrics['audience_activity'] * 0.7 + metrics['audience_growth_rate'] * 0.3,
                    1
                )
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting TikTok audience engagement metrics")
            return {} 