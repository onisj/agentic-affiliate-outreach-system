"""
Base Scraper

This module defines the base scraper class that all platform-specific scrapers inherit from.
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from discovery.models.data_object import DataObject
from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for all platform-specific scrapers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.session = None
        self.driver = None
        self._validate_config()
        
    def _validate_config(self):
        """Validate configuration parameters."""
        required_keys = ['timeout', 'user_agent']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

    async def __aenter__(self):
        """Enter context manager, initialize resources."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, close resources."""
        await self.close()

    async def initialize(self):
        """Initialize the scraper with session and browser."""
        try:
            # Initialize aiohttp session
            self.session = aiohttp.ClientSession(
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
            )
            
            # Initialize Selenium WebDriver
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={self.config.get("user_agent")}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("BaseScraper initialized successfully")
            
        except Exception as e:
            self._handle_error(e, "initializing scraper")
            raise
            
    async def close(self):
        """Close the scraper's session and browser."""
        try:
            if self.session:
                await self.session.close()
                logger.info("aiohttp session closed")
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
        except Exception as e:
            self._handle_error(e, "closing scraper")
            
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a profile from the platform."""
        raise NotImplementedError
        
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape content from the platform."""
        raise NotImplementedError
        
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from the platform."""
        raise NotImplementedError
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for HTTP requests."""
        return {
            'User-Agent': self.config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    def _get_element_text(self, element: Any, selector: str) -> str:
        """Get text from an element by CSS selector."""
        try:
            text = element.find_element(By.CSS_SELECTOR, selector).text
            logger.debug(f"Extracted text from {selector}: {text[:50]}...")
            return text
        except Exception as e:
            self._handle_error(e, f"getting element text for selector {selector}")
            return ""
            
    def _get_element_attribute(self, element: Any, selector: str, attribute: str) -> str:
        """Get attribute value from an element by CSS selector."""
        try:
            value = element.find_element(By.CSS_SELECTOR, selector).get_attribute(attribute)
            logger.debug(f"Extracted {attribute} from {selector}: {value[:50]}...")
            return value
        except Exception as e:
            self._handle_error(e, f"getting element attribute {attribute} for selector {selector}")
            return ""
            
    def _parse_count(self, count_str: str) -> int:
        """Parse count string to integer."""
        try:
            count_str = count_str.lower().strip()
            if 'k' in count_str:
                return int(float(count_str.replace('k', '')) * 1000)
            elif 'm' in count_str:
                return int(float(count_str.replace('m', '')) * 1000000)
            else:
                return int(count_str)
        except Exception as e:
            self._handle_error(e, "parsing count")
            return 0
            
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure consistent format."""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            normalized = url.rstrip('/')
            logger.debug(f"Normalized URL: {normalized}")
            return normalized
        except Exception as e:
            self._handle_error(e, "normalizing URL")
            return url
            
    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            is_valid = all([result.scheme, result.netloc])
            logger.debug(f"URL validation for {url}: {'Valid' if is_valid else 'Invalid'}")
            return is_valid
        except Exception as e:
            self._handle_error(e, "validating URL")
            return False
            
    async def _handle_rate_limit(self, retry_after: int):
        """Handle rate limiting by waiting for the specified time."""
        self.monitoring.log_warning(f"Rate limit hit, waiting {retry_after} seconds")
        logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
        await asyncio.sleep(retry_after)
        
    def _handle_error(self, error: Exception, context: str):
        """Handle errors with proper logging and monitoring."""
        error_msg = f"Error in {context}: {str(error)}"
        self.monitoring.log_error(error_msg)
        logger.error(error_msg)
        
    def _extract_metadata(self, element: Any) -> Dict[str, Any]:
        """Extract metadata from an element."""
        try:
            metadata = {
                'id': element.get_attribute('id') or '',
                'class': element.get_attribute('class') or '',
                'data_attributes': {
                    attr: element.get_attribute(f'data-{attr}') or ''
                    for attr in ['testid', 'type', 'role']
                }
            }
            logger.debug(f"Extracted metadata: {metadata}")
            return metadata
        except Exception as e:
            self._handle_error(e, "extracting metadata")
            return {}
            
    def _to_data_object(self, source: str, raw_data: Dict[str, Any]) -> DataObject:
        """Convert raw data to DataObject."""
        return DataObject(
            source=source,
            raw_data=raw_data,
            processed_data={},
            metadata={'timestamp': datetime.utcnow().isoformat()}
        )