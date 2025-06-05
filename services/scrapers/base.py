from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from api.middleware.metrics import record_db_operation
import time

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all platform scrapers."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.last_scrape_time: Optional[datetime] = None
        self.scrape_count = 0
    
    @abstractmethod
    async def discover_affiliates(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover potential affiliates based on search criteria."""
        pass
    
    @abstractmethod
    async def extract_affiliate_data(self, affiliate_id: str) -> Dict[str, Any]:
        """Extract detailed data about a specific affiliate."""
        pass
    
    @abstractmethod
    async def validate_affiliate(self, affiliate_data: Dict[str, Any]) -> bool:
        """Validate if the discovered affiliate meets our criteria."""
        pass
    
    async def scrape(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main scraping method that coordinates the discovery and extraction process."""
        start_time = time.time()
        try:
            # Discover potential affiliates
            potential_affiliates = await self.discover_affiliates(search_criteria)
            logger.info(f"Discovered {len(potential_affiliates)} potential affiliates on {self.platform_name}")
            
            # Extract and validate data for each affiliate
            valid_affiliates = []
            for affiliate in potential_affiliates:
                try:
                    detailed_data = await self.extract_affiliate_data(affiliate['id'])
                    if await self.validate_affiliate(detailed_data):
                        valid_affiliates.append(detailed_data)
                except Exception as e:
                    logger.error(f"Error processing affiliate {affiliate['id']}: {e}")
            
            # Update metrics
            duration = time.time() - start_time
            record_db_operation(
                f"scrape_{self.platform_name}",
                duration
            )
            
            self.last_scrape_time = datetime.now()
            self.scrape_count += 1
            
            return valid_affiliates
            
        except Exception as e:
            logger.error(f"Error during scraping on {self.platform_name}: {e}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get scraper metrics."""
        return {
            'platform': self.platform_name,
            'last_scrape_time': self.last_scrape_time,
            'scrape_count': self.scrape_count
        } 