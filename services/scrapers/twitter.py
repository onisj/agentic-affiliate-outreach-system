from typing import List, Dict, Any
import logging
from .base import BaseScraper
from config.settings import settings
import aiohttp
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TwitterScraper(BaseScraper):
    """Twitter scraper for discovering potential affiliates."""
    
    def __init__(self):
        super().__init__("twitter")
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.base_url = "https://api.twitter.com/2"
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
        """Discover potential affiliates on Twitter."""
        session = await self._get_session()
        
        # Build search query based on criteria
        query = {
            "query": " OR ".join(search_criteria.get("keywords", ["affiliate marketing"])),
            "max_results": 100,
            "tweet.fields": "created_at,public_metrics",
            "user.fields": "description,public_metrics,location"
        }
        
        try:
            # Search for users matching criteria
            async with session.get(
                f"{self.base_url}/users/search",
                params=query
            ) as response:
                if response.status != 200:
                    logger.error(f"Twitter API error: {response.status}")
                    return []
                
                data = await response.json()
                return data.get("data", [])
                
        except Exception as e:
            logger.error(f"Error discovering affiliates on Twitter: {e}")
            return []
    
    async def extract_affiliate_data(self, affiliate_id: str) -> Dict[str, Any]:
        """Extract detailed data about a Twitter user."""
        session = await self._get_session()
        
        try:
            # Get user profile
            async with session.get(
                f"{self.base_url}/users/{affiliate_id}",
                params={
                    "user.fields": "description,public_metrics,location,created_at",
                    "tweet.fields": "created_at,public_metrics"
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Error fetching Twitter profile: {response.status}")
                    return {}
                
                profile_data = await response.json()
                
                # Get recent tweets
                tweets = await self._get_recent_tweets(affiliate_id)
                
                return {
                    "id": affiliate_id,
                    "platform": "twitter",
                    "name": profile_data.get("name"),
                    "username": profile_data.get("username"),
                    "description": profile_data.get("description"),
                    "location": profile_data.get("location"),
                    "followers_count": profile_data.get("public_metrics", {}).get("followers_count"),
                    "following_count": profile_data.get("public_metrics", {}).get("following_count"),
                    "tweet_count": profile_data.get("public_metrics", {}).get("tweet_count"),
                    "recent_tweets": tweets,
                    "discovered_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error extracting Twitter data: {e}")
            return {}
    
    async def validate_affiliate(self, affiliate_data: Dict[str, Any]) -> bool:
        """Validate if the Twitter user meets our criteria."""
        if not affiliate_data:
            return False
        
        # Check for required fields
        required_fields = ["name", "username", "description"]
        if not all(field in affiliate_data for field in required_fields):
            return False
        
        # Check follower count
        min_followers = 1000  # Minimum followers threshold
        followers_count = affiliate_data.get("followers_count", 0)
        if followers_count < min_followers:
            return False
        
        # Check for marketing-related content
        description = affiliate_data.get("description", "").lower()
        recent_tweets = affiliate_data.get("recent_tweets", [])
        
        has_marketing_content = (
            "marketing" in description or
            "affiliate" in description or
            any("marketing" in tweet.get("text", "").lower() or
                "affiliate" in tweet.get("text", "").lower()
                for tweet in recent_tweets)
        )
        
        return has_marketing_content
    
    async def _get_recent_tweets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent tweets from a user."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/users/{user_id}/tweets",
                params={
                    "max_results": 10,
                    "tweet.fields": "created_at,public_metrics"
                }
            ) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching recent tweets: {e}")
            return []
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close() 