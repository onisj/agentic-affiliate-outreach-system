from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Affiliate, AffiliateStatus
from services.scrapers.linkedin import LinkedInScraper
from services.scrapers.twitter import TwitterScraper
from services.cache import cache_result
import asyncio

logger = logging.getLogger(__name__)

class AffiliateDiscoveryService:
    """Service for discovering and managing potential affiliates."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scrapers = {
            "linkedin": LinkedInScraper(),
            "twitter": TwitterScraper()
        }
    
    async def discover_affiliates(
        self,
        platform: str,
        search_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Discover potential affiliates on a specific platform."""
        if platform not in self.scrapers:
            raise ValueError(f"Unsupported platform: {platform}")
        
        scraper = self.scrapers[platform]
        try:
            # Discover and validate affiliates
            discovered_affiliates = await scraper.scrape(search_criteria)
            
            # Store discovered affiliates
            for affiliate_data in discovered_affiliates:
                await self._store_affiliate(affiliate_data)
            
            return discovered_affiliates
            
        except Exception as e:
            logger.error(f"Error discovering affiliates on {platform}: {e}")
            raise
    
    @cache_result(ttl=3600)  # Cache for 1 hour
    async def get_affiliate(self, affiliate_id: str) -> Optional[Dict[str, Any]]:
        """Get affiliate details from database."""
        affiliate = self.db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
        if not affiliate:
            return None
        
        return {
            "id": affiliate.id,
            "name": affiliate.name,
            "platform": affiliate.platform,
            "status": affiliate.status,
            "contact_info": affiliate.contact_info,
            "discovered_at": affiliate.discovered_at.isoformat(),
            "last_updated": affiliate.last_updated.isoformat()
        }
    
    async def update_affiliate_status(
        self,
        affiliate_id: str,
        status: AffiliateStatus,
        notes: Optional[str] = None
    ) -> bool:
        """Update affiliate status."""
        try:
            affiliate = self.db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
            if not affiliate:
                return False
            
            affiliate.status = status
            if notes:
                affiliate.notes = notes
            affiliate.last_updated = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating affiliate status: {e}")
            self.db.rollback()
            return False
    
    async def _store_affiliate(self, affiliate_data: Dict[str, Any]) -> bool:
        """Store discovered affiliate in database."""
        try:
            # Check if affiliate already exists
            existing = self.db.query(Affiliate).filter(
                Affiliate.id == affiliate_data["id"]
            ).first()
            
            if existing:
                # Update existing affiliate
                existing.name = affiliate_data["name"]
                existing.contact_info = affiliate_data["contact_info"]
                existing.last_updated = datetime.now()
            else:
                # Create new affiliate
                new_affiliate = Affiliate(
                    id=affiliate_data["id"],
                    name=affiliate_data["name"],
                    platform=affiliate_data["platform"],
                    status=AffiliateStatus.UNKNOWN,
                    contact_info=affiliate_data["contact_info"],
                    discovered_at=datetime.fromisoformat(affiliate_data["discovered_at"]),
                    last_updated=datetime.now()
                )
                self.db.add(new_affiliate)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing affiliate: {e}")
            self.db.rollback()
            return False
    
    async def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get metrics about the discovery process."""
        metrics = {}
        for platform, scraper in self.scrapers.items():
            metrics[platform] = scraper.get_metrics()
        return metrics
    
    async def close(self):
        """Close all scraper sessions."""
        for scraper in self.scrapers.values():
            await scraper.close() 