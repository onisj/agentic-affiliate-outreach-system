"""
YouTube Scraper

This module implements scraping functionality for YouTube channels and videos.
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

class YouTubeScraper(BaseScraper):
    """Scrapes data from YouTube channels and videos."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a YouTube channel."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('youtube')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#channel-header"))
            )
            
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'videos': await self._extract_videos(),
                'subscribers': await self._extract_subscribers(),
                'engagement': await self._extract_engagement()
            }
            
            logger.info(f"Successfully scraped YouTube channel: {profile_url}")
            return self._to_data_object("YouTube", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping YouTube channel {profile_url}")
            return self._to_data_object("YouTube", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping YouTube channel {profile_url}")
            return self._to_data_object("YouTube", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific YouTube video content."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('youtube')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#movie_player"))
            )
            
            content_data = await self._extract_video_details()
            logger.info(f"Successfully scraped YouTube video: {content_url}")
            return self._to_data_object("YouTube", content_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping YouTube video {content_url}")
            return self._to_data_object("YouTube", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping YouTube video {content_url}")
            return self._to_data_object("YouTube", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from a YouTube channel."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('youtube')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#channel-header"))
            )
            
            network_data = {
                'subscribers': await self._extract_subscribers(),
                'related_channels': await self._extract_related_channels()
            }
            logger.info(f"Successfully scraped YouTube network: {profile_url}")
            return self._to_data_object("YouTube", network_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping YouTube network {profile_url}")
            return self._to_data_object("YouTube", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping YouTube network {profile_url}")
            return self._to_data_object("YouTube", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic channel information."""
        try:
            header = self.driver.find_element(By.CSS_SELECTOR, "#channel-header")
            basic_info = {
                'name': self._get_element_text(header, "#channel-name"),
                'description': self._get_element_text(header, "#description"),
                'join_date': self._get_element_text(header, "#right-column yt-formatted-string"),
                'profile_picture': self._get_element_attribute(header, "#channel-header-container img", "src"),
                'banner_image': self._get_element_attribute(header, "#channel-header-container img", "src"),
                'metadata': self._extract_metadata(header)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting YouTube basic info")
            return {}
            
    async def _extract_videos(self) -> List[Dict[str, Any]]:
        """Extract videos from the channel."""
        try:
            videos = []
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "ytd-grid-video-renderer")
            
            for element in video_elements:
                video = {
                    'title': self._get_element_text(element, "#video-title"),
                    'url': self._get_element_attribute(element, "#video-title", "href"),
                    'thumbnail': self._get_element_attribute(element, "#thumbnail img", "src"),
                    'views': self._parse_count(self._get_element_text(element, "#metadata-line span")),
                    'upload_date': self._get_element_text(element, "#metadata-line span:nth-child(2)"),
                    'duration': self._get_element_text(element, "#text.ytd-thumbnail-overlay-time-status-renderer"),
                    'metadata': self._extract_metadata(element)
                }
                videos.append(video)
                
            return videos
            
        except Exception as e:
            self._handle_error(e, "extracting YouTube videos")
            return []
            
    async def _extract_subscribers(self) -> Dict[str, Any]:
        """Extract subscriber information."""
        try:
            subscribers_section = self.driver.find_element(By.CSS_SELECTOR, "#subscriber-count")
            subscribers = {
                'count': self._parse_count(subscribers_section.text),
                'demographics': await self._get_subscriber_demographics(),
                'growth_rate': await self._get_subscriber_growth_rate(),
                'metadata': self._extract_metadata(subscribers_section)
            }
            return subscribers
            
        except Exception as e:
            self._handle_error(e, "extracting YouTube subscribers")
            return {}
            
    async def _extract_engagement(self) -> Dict[str, Any]:
        """Extract engagement metrics."""
        try:
            engagement = {
                'videos': await self._get_video_engagement_metrics(),
                'channel': await self._get_channel_engagement_metrics(),
                'audience': await self._get_audience_engagement_metrics()
            }
            return engagement
            
        except Exception as e:
            self._handle_error(e, "extracting YouTube engagement")
            return {}
            
    async def _extract_video_details(self) -> Dict[str, Any]:
        """Extract detailed video information."""
        try:
            video = {
                'title': self._get_element_text(self.driver, "h1.title"),
                'description': self._get_element_text(self.driver, "#description"),
                'views': self._parse_count(self._get_element_text(self.driver, "span.view-count")),
                'likes': self._parse_count(self._get_element_text(self.driver, "#top-level-buttons-computed button")),
                'comments': self._parse_count(self._get_element_text(self.driver, "#comments #count")),
                'upload_date': self._get_element_text(self.driver, "#info-strings yt-formatted-string"),
                'duration': self._get_element_text(self.driver, "span.ytp-time-duration"),
                'metadata': self._extract_metadata(self.driver)
            }
            return video
            
        except Exception as e:
            self._handle_error(e, "extracting YouTube video details")
            return {}
            
    async def _extract_related_channels(self) -> List[Dict[str, Any]]:
        """Extract related channels."""
        try:
            related_channels = []
            channel_elements = self.driver.find_elements(By.CSS_SELECTOR, "ytd-channel-renderer")
            
            for element in channel_elements:
                channel = {
                    'name': self._get_element_text(element, "#channel-name"),
                    'url': self._get_element_attribute(element, "#channel-name", "href"),
                    'subscribers': self._parse_count(self._get_element_text(element, "#subscribers")),
                    'metadata': self._extract_metadata(element)
                }
                related_channels.append(channel)
                
            return related_channels
            
        except Exception as e:
            self._handle_error(e, "extracting YouTube related channels")
            return []
            
    async def _get_subscriber_demographics(self) -> Dict[str, Any]:
        """Get subscriber demographics."""
        try:
            demographics = {
                'age_groups': {},
                'gender': {},
                'locations': {},
                'languages': {}
            }
            
            # Requires YouTube Analytics API for accurate demographics
            return demographics
            
        except Exception as e:
            self._handle_error(e, "getting YouTube subscriber demographics")
            return {}
            
    async def _get_subscriber_growth_rate(self) -> float:
        """Get subscriber growth rate."""
        try:
            # Requires historical data
            return 0.0
            
        except Exception as e:
            self._handle_error(e, "getting YouTube subscriber growth rate")
            return 0.0
            
    async def _get_video_engagement_metrics(self) -> Dict[str, float]:
        """Get video engagement metrics."""
        try:
            metrics = {
                'average_views': 0,
                'average_likes': 0,
                'average_comments': 0,
                'engagement_rate': 0
            }
            
            videos = await self._extract_videos()
            if videos:
                total_views = sum(video['views'] for video in videos)
                total_likes = sum(video.get('likes', 0) for video in videos)
                total_comments = sum(video.get('comments', 0) for video in videos)
                
                metrics['average_views'] = total_views / len(videos)
                metrics['average_likes'] = total_likes / len(videos)
                metrics['average_comments'] = total_comments / len(videos)
                
                total_engagement = total_likes + total_comments
                metrics['engagement_rate'] = total_engagement / total_views if total_views > 0 else 0
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting YouTube video engagement metrics")
            return {}
            
    async def _get_channel_engagement_metrics(self) -> Dict[str, float]:
        """Get channel engagement metrics."""
        try:
            metrics = {
                'channel_views': 0,
                'channel_engagement_rate': 0,
                'subscriber_growth_rate': 0
            }
            
            channel = self.driver.find_element(By.CSS_SELECTOR, "#channel-header")
            views_element = channel.find_element(By.CSS_SELECTOR, "#channel-header-container yt-formatted-string")
            if views_element:
                metrics['channel_views'] = self._parse_count(views_element.text)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting YouTube channel engagement metrics")
            return {}
            
    async def _get_audience_engagement_metrics(self) -> Dict[str, float]:
        """Get audience engagement metrics."""
        try:
            metrics = {
                'audience_activity': 0,
                'audience_growth_rate': 0,
                'audience_quality_score': 0
            }
            
            subscribers = await self._extract_subscribers()
            videos = await self._extract_videos()
            
            if subscribers and videos:
                metrics['audience_activity'] = sum(video['views'] for video in videos) / subscribers['count'] if subscribers['count'] > 0 else 0
                metrics['audience_growth_rate'] = await self._get_subscriber_growth_rate()
                metrics['audience_quality_score'] = min(
                    metrics['audience_activity'] * 0.7 + metrics['audience_growth_rate'] * 0.3,
                    1
                )
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting YouTube audience engagement metrics")
            return {} 