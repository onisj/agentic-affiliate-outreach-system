"""
Generic Web Scraper

This module implements generic web scraping functionality for any website.
"""

from typing import Dict, List, Any
import logging
import asyncio
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

class GenericWebScraper(BaseScraper):
    """Scrapes data from any website."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a website profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('generic')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'content': await self._extract_content(),
                'metadata': await self._extract_metadata()
            }
            
            logger.info(f"Successfully scraped website profile: {profile_url}")
            return self._to_data_object("Generic", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping website profile {profile_url}")
            return self._to_data_object("Generic", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping website profile {profile_url}")
            return self._to_data_object("Generic", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific website content."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('generic')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            content_data = await self._extract_content_details()
            logger.info(f"Successfully scraped website content: {content_url}")
            return self._to_data_object("Generic", content_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping website content {content_url}")
            return self._to_data_object("Generic", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping website content {content_url}")
            return self._to_data_object("Generic", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from a website."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('generic')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            network_data = {
                'links': await self._extract_links(),
                'social_media': await self._extract_social_media(),
                'related_sites': await self._extract_related_sites()
            }
            logger.info(f"Successfully scraped website network: {profile_url}")
            return self._to_data_object("Generic", network_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping website network {profile_url}")
            return self._to_data_object("Generic", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping website network {profile_url}")
            return self._to_data_object("Generic", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic website information."""
        try:
            basic_info = {
                'title': self.driver.title,
                'description': self._get_meta_description(),
                'keywords': self._get_meta_keywords(),
                'author': self._get_meta_author(),
                'language': self._get_page_language(),
                'metadata': self._extract_metadata(self.driver)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting website basic info")
            return {}
            
    async def _extract_content(self) -> Dict[str, Any]:
        """Extract website content."""
        try:
            content = {
                'text': self._get_page_text(),
                'images': await self._extract_images(),
                'videos': await self._extract_videos(),
                'metadata': self._extract_metadata(self.driver)
            }
            return content
            
        except Exception as e:
            self._handle_error(e, "extracting website content")
            return {}
            
    async def _extract_content_details(self) -> Dict[str, Any]:
        """Extract detailed content information."""
        try:
            content = {
                'title': self.driver.title,
                'text': self._get_page_text(),
                'images': await self._extract_images(),
                'videos': await self._extract_videos(),
                'links': await self._extract_links(),
                'metadata': self._extract_metadata(self.driver)
            }
            return content
            
        except Exception as e:
            self._handle_error(e, "extracting website content details")
            return {}
            
    async def _extract_links(self) -> List[Dict[str, Any]]:
        """Extract links from the page."""
        try:
            links = []
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in link_elements:
                link = {
                    'text': element.text,
                    'url': element.get_attribute('href'),
                    'title': element.get_attribute('title'),
                    'metadata': self._extract_metadata(element)
                }
                links.append(link)
                
            return links
            
        except Exception as e:
            self._handle_error(e, "extracting website links")
            return []
            
    async def _extract_images(self) -> List[Dict[str, Any]]:
        """Extract images from the page."""
        try:
            images = []
            image_elements = self.driver.find_elements(By.TAG_NAME, "img")
            
            for element in image_elements:
                image = {
                    'src': element.get_attribute('src'),
                    'alt': element.get_attribute('alt'),
                    'title': element.get_attribute('title'),
                    'width': element.get_attribute('width'),
                    'height': element.get_attribute('height'),
                    'metadata': self._extract_metadata(element)
                }
                images.append(image)
                
            return images
            
        except Exception as e:
            self._handle_error(e, "extracting website images")
            return []
            
    async def _extract_videos(self) -> List[Dict[str, Any]]:
        """Extract videos from the page."""
        try:
            videos = []
            video_elements = self.driver.find_elements(By.TAG_NAME, "video")
            
            for element in video_elements:
                video = {
                    'src': element.get_attribute('src'),
                    'poster': element.get_attribute('poster'),
                    'width': element.get_attribute('width'),
                    'height': element.get_attribute('height'),
                    'metadata': self._extract_metadata(element)
                }
                videos.append(video)
                
            return videos
            
        except Exception as e:
            self._handle_error(e, "extracting website videos")
            return []
            
    async def _extract_social_media(self) -> List[Dict[str, Any]]:
        """Extract social media links."""
        try:
            social_media = []
            social_platforms = {
                'facebook': 'facebook.com',
                'twitter': 'twitter.com',
                'linkedin': 'linkedin.com',
                'instagram': 'instagram.com',
                'youtube': 'youtube.com',
                'tiktok': 'tiktok.com',
                'reddit': 'reddit.com'
            }
            
            for platform, domain in social_platforms.items():
                elements = self.driver.find_elements(By.CSS_SELECTOR, f"a[href*='{domain}']")
                for element in elements:
                    social = {
                        'platform': platform,
                        'url': element.get_attribute('href'),
                        'text': element.text,
                        'metadata': self._extract_metadata(element)
                    }
                    social_media.append(social)
                    
            return social_media
            
        except Exception as e:
            self._handle_error(e, "extracting website social media")
            return []
            
    async def _extract_related_sites(self) -> List[Dict[str, Any]]:
        """Extract related websites."""
        try:
            related_sites = []
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in link_elements:
                url = element.get_attribute('href')
                if url and not url.startswith(('http://', 'https://')):
                    continue
                    
                related_site = {
                    'url': url,
                    'text': element.text,
                    'title': element.get_attribute('title'),
                    'metadata': self._extract_metadata(element)
                }
                related_sites.append(related_site)
                
            return related_sites
            
        except Exception as e:
            self._handle_error(e, "extracting website related sites")
            return []
            
    def _get_meta_description(self) -> str:
        """Get meta description from the page."""
        try:
            meta = self.driver.find_element(By.CSS_SELECTOR, "meta[name='description']")
            return meta.get_attribute('content')
        except:
            return ""
            
    def _get_meta_keywords(self) -> List[str]:
        """Get meta keywords from the page."""
        try:
            meta = self.driver.find_element(By.CSS_SELECTOR, "meta[name='keywords']")
            keywords = meta.get_attribute('content')
            return [k.strip() for k in keywords.split(',')]
        except:
            return []
            
    def _get_meta_author(self) -> str:
        """Get meta author from the page."""
        try:
            meta = self.driver.find_element(By.CSS_SELECTOR, "meta[name='author']")
            return meta.get_attribute('content')
        except:
            return ""
            
    def _get_page_language(self) -> str:
        """Get page language."""
        try:
            return self.driver.find_element(By.TAG_NAME, "html").get_attribute('lang')
        except:
            return ""
            
    def _get_page_text(self) -> str:
        """Get all text content from the page."""
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except:
            return "" 