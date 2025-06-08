"""
LinkedIn Scraper

This module implements scraping functionality for LinkedIn profiles and content.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
from bs4 import BeautifulSoup
import aiohttp
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

class LinkedInScraper(BaseScraper):
    """Scrapes data from LinkedIn profiles and content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a LinkedIn profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('linkedin')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            # Normalize URL
            profile_url = self._normalize_url(profile_url)
            
            # Load profile page
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            # Wait for profile content to load
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card"))
            )
            
            # Extract profile data
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'experience': await self._extract_experience(),
                'education': await self._extract_education(),
                'skills': await self._extract_skills(),
                'content': await self._extract_content(),
                'connections': await self._extract_connections()
            }
            
            logger.info(f"Successfully scraped LinkedIn profile: {profile_url}")
            return self._to_data_object("LinkedIn", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping LinkedIn profile {profile_url}")
            return self._to_data_object("LinkedIn", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping LinkedIn profile {profile_url}")
            return self._to_data_object("LinkedIn", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific LinkedIn content (e.g., posts, articles)."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('linkedin')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CLASS_NAME, "feed-shared-update-v2"))
            )
            
            content_data = await self._extract_content()
            logger.info(f"Successfully scraped LinkedIn content: {content_url}")
            return self._to_data_object("LinkedIn", {'content': content_data})
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping LinkedIn content {content_url}")
            return self._to_data_object("LinkedIn", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping LinkedIn content {content_url}")
            return self._to_data_object("LinkedIn", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from a LinkedIn profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('linkedin')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.ID, "connections-section"))
            )
            
            network_data = await self._extract_connections()
            logger.info(f"Successfully scraped LinkedIn network: {profile_url}")
            return self._to_data_object("LinkedIn", {'connections': network_data})
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping LinkedIn network {profile_url}")
            return self._to_data_object("LinkedIn", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping LinkedIn network {profile_url}")
            return self._to_data_object("LinkedIn", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic profile information."""
        try:
            header = self.driver.find_element(By.CLASS_NAME, "pv-top-card")
            basic_info = {
                'name': self._get_element_text(header, ".text-heading-xlarge"),
                'headline': self._get_element_text(header, ".text-body-medium"),
                'location': self._get_element_text(header, ".text-body-small"),
                'about': self._get_element_text(header, ".pv-shared-text-with-see-more"),
                'profile_picture': self._get_element_attribute(
                    header, ".pv-top-card-profile-picture__image", "src"
                ),
                'metadata': self._extract_metadata(header)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting LinkedIn basic info")
            return {}
            
    async def _extract_experience(self) -> List[Dict[str, Any]]:
        """Extract work experience information."""
        try:
            experience_section = self.driver.find_element(By.ID, "experience-section")
            experience_items = experience_section.find_elements(
                By.CLASS_NAME, "pv-entity__position-group-pager"
            )
            
            experiences = []
            for item in experience_items:
                experience = {
                    'title': self._get_element_text(item, ".pv-entity__name"),
                    'company': self._get_element_text(item, ".pv-entity__secondary-title"),
                    'duration': self._get_element_text(item, ".pv-entity__date-range"),
                    'location': self._get_element_text(item, ".pv-entity__location"),
                    'description': self._get_element_text(item, ".pv-entity__description"),
                    'metadata': self._extract_metadata(item)
                }
                experiences.append(experience)
                
            return experiences
            
        except Exception as e:
            self._handle_error(e, "extracting LinkedIn experience")
            return []
            
    async def _extract_education(self) -> List[Dict[str, Any]]:
        """Extract education information."""
        try:
            education_section = self.driver.find_element(By.ID, "education-section")
            education_items = education_section.find_elements(
                By.CLASS_NAME, "pv-education-entity"
            )
            
            education = []
            for item in education_items:
                edu = {
                    'school': self._get_element_text(item, ".pv-entity__school-name"),
                    'degree': self._get_element_text(item, ".pv-entity__degree-name"),
                    'field': self._get_element_text(item, ".pv-entity__fos"),
                    'duration': self._get_element_text(item, ".pv-entity__dates"),
                    'description': self._get_element_text(item, ".pv-entity__description"),
                    'metadata': self._extract_metadata(item)
                }
                education.append(edu)
                
            return education
            
        except Exception as e:
            self._handle_error(e, "extracting LinkedIn education")
            return []
            
    async def _extract_skills(self) -> List[Dict[str, Any]]:
        """Extract skills information."""
        try:
            skills_section = self.driver.find_element(By.ID, "skills-section")
            skill_items = skills_section.find_elements(
                By.CLASS_NAME, "pv-skill-category-entity"
            )
            
            skills = []
            for item in skill_items:
                skill = {
                    'name': self._get_element_text(item, ".pv-skill-category-entity__name"),
                    'endorsements': self._parse_count(
                        self._get_element_text(item, ".pv-skill-category-entity__endorsement-count")
                    ),
                    'metadata': self._extract_metadata(item)
                }
                skills.append(skill)
                
            return skills
            
        except Exception as e:
            self._handle_error(e, "extracting LinkedIn skills")
            return []
            
    async def _extract_content(self) -> List[Dict[str, Any]]:
        """Extract profile content and posts."""
        try:
            content_section = self.driver.find_element(By.ID, "content-section")
            content_items = content_section.find_elements(
                By.CLASS_NAME, "pv-shared-text-with-see-more"
            )
            
            content = []
            for item in content_items:
                post = {
                    'text': item.text,
                    'timestamp': self._get_element_attribute(item, "time", "datetime"),
                    'engagement': self._get_engagement_metrics(item),
                    'metadata': self._extract_metadata(item)
                }
                content.append(post)
                
            return content
            
        except Exception as e:
            self._handle_error(e, "extracting LinkedIn content")
            return []
            
    async def _extract_connections(self) -> Dict[str, Any]:
        """Extract connection information."""
        try:
            connections_section = self.driver.find_element(By.ID, "connections-section")
            connections = {
                'count': self._parse_count(
                    self._get_element_text(connections_section, ".pv-top-card--list-bullet")
                ),
                'industries': await self._get_connection_industries(connections_section),
                'locations': await self._get_connection_locations(connections_section),
                'metadata': self._extract_metadata(connections_section)
            }
            return connections
            
        except Exception as e:
            self._handle_error(e, "extracting LinkedIn connections")
            return {}
            
    async def _get_connection_industries(self, section: Any) -> List[Dict[str, Any]]:
        """Get connection industries from the connections section."""
        try:
            industries = []
            industry_elements = section.find_elements(
                By.CLASS_NAME, "pv-top-card--list-bullet"
            )
            
            for element in industry_elements:
                industry = {
                    'name': element.text,
                    'count': self._parse_count(element.get_attribute('data-count') or '0'),
                    'metadata': self._extract_metadata(element)
                }
                industries.append(industry)
                
            return industries
            
        except Exception as e:
            self._handle_error(e, "getting LinkedIn connection industries")
            return []
            
    async def _get_connection_locations(self, section: Any) -> List[Dict[str, Any]]:
        """Get connection locations from the connections section."""
        try:
            locations = []
            location_elements = section.find_elements(
                By.CLASS_NAME, "pv-top-card--list-bullet"
            )
            
            for element in location_elements:
                location = {
                    'name': element.text,
                    'count': self._parse_count(element.get_attribute('data-count') or '0'),
                    'metadata': self._extract_metadata(element)
                }
                locations.append(location)
                
            return locations
            
        except Exception as e:
            self._handle_error(e, "getting LinkedIn connection locations")
            return [] 