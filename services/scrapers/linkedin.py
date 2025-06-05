from typing import List, Dict, Any
import logging
from .base import BaseScraper
from config.settings import settings
import aiohttp
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    """LinkedIn scraper for discovering potential affiliates."""
    
    def __init__(self):
        super().__init__("linkedin")
        self.api_key = settings.LINKEDIN_API_KEY
        self.api_secret = settings.LINKEDIN_API_SECRET
        self.base_url = "https://api.linkedin.com/v2"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def discover_affiliates(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover potential affiliates on LinkedIn."""
        session = await self._get_session()
        
        # Build search query based on criteria
        query = {
            "keywords": search_criteria.get("keywords", "affiliate marketing"),
            "industry": search_criteria.get("industry", "Marketing and Advertising"),
            "experience": search_criteria.get("experience", "2+ years"),
            "location": search_criteria.get("location", "United States")
        }
        
        try:
            # Search for people matching criteria
            async with session.get(
                f"{self.base_url}/people-search",
                params=query
            ) as response:
                if response.status != 200:
                    logger.error(f"LinkedIn API error: {response.status}")
                    return []
                
                data = await response.json()
                return data.get("elements", [])
                
        except Exception as e:
            logger.error(f"Error discovering affiliates on LinkedIn: {e}")
            return []
    
    async def extract_affiliate_data(self, affiliate_id: str) -> Dict[str, Any]:
        """Extract detailed data about a LinkedIn user."""
        session = await self._get_session()
        
        try:
            # Get basic profile
            async with session.get(
                f"{self.base_url}/people/{affiliate_id}"
            ) as response:
                if response.status != 200:
                    logger.error(f"Error fetching LinkedIn profile: {response.status}")
                    return {}
                
                profile_data = await response.json()
                
                # Get additional data
                contact_info = await self._get_contact_info(affiliate_id)
                activity_data = await self._get_activity_data(affiliate_id)
                
                return {
                    "id": affiliate_id,
                    "platform": "linkedin",
                    "name": profile_data.get("firstName") + " " + profile_data.get("lastName"),
                    "headline": profile_data.get("headline"),
                    "summary": profile_data.get("summary"),
                    "location": profile_data.get("location", {}).get("name"),
                    "industry": profile_data.get("industry"),
                    "experience": profile_data.get("experience"),
                    "education": profile_data.get("education"),
                    "contact_info": contact_info,
                    "activity": activity_data,
                    "discovered_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error extracting LinkedIn data: {e}")
            return {}
    
    async def validate_affiliate(self, affiliate_data: Dict[str, Any]) -> bool:
        """Validate if the LinkedIn user meets our criteria."""
        if not affiliate_data:
            return False
        
        # Check for required fields
        required_fields = ["name", "headline", "contact_info"]
        if not all(field in affiliate_data for field in required_fields):
            return False
        
        # Check for marketing experience
        experience = affiliate_data.get("experience", [])
        has_marketing_exp = any(
            "marketing" in exp.get("title", "").lower() or
            "affiliate" in exp.get("title", "").lower()
            for exp in experience
        )
        
        # Check for recent activity
        activity = affiliate_data.get("activity", {})
        recent_posts = activity.get("posts", [])
        has_recent_activity = any(
            datetime.fromisoformat(post.get("created_at", "")) > datetime.now() - timedelta(days=30)
            for post in recent_posts
        )
        
        return has_marketing_exp and has_recent_activity
    
    async def _get_contact_info(self, affiliate_id: str) -> Dict[str, Any]:
        """Get contact information for a LinkedIn user."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/people/{affiliate_id}/contact-info"
            ) as response:
                if response.status != 200:
                    return {}
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching contact info: {e}")
            return {}
    
    async def _get_activity_data(self, affiliate_id: str) -> Dict[str, Any]:
        """Get recent activity data for a LinkedIn user."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/people/{affiliate_id}/activity"
            ) as response:
                if response.status != 200:
                    return {}
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching activity data: {e}")
            return {}
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close() 