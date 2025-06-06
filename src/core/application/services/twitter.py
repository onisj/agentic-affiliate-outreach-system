"""
Twitter Service

This module provides functionality for:
1. Twitter API integration
2. Profile scraping and analysis
3. Message sending and tracking
4. Connection management
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
import logging
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

from config.settings import settings
from database.session import get_db
from database.models import MessageLog, MessageType, MessageStatus

logger = logging.getLogger(__name__)

class TwitterService:
    """Service for interacting with Twitter API and scraping."""
    
    def __init__(self):
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.access_token = settings.TWITTER_ACCESS_TOKEN
        self.access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET
        self.base_url = "https://api.twitter.com/2"
        self.oauth_url = "https://api.twitter.com/oauth2/token"
        self._token = None
        self._token_expires = None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        if not self._token or (self._token_expires and datetime.now() >= self._token_expires):
            self._refresh_token()
        
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def _refresh_token(self):
        """Refresh OAuth 2.0 token."""
        try:
            response = requests.post(
                self.oauth_url,
                auth=(self.api_key, self.api_secret),
                data={"grant_type": "client_credentials"}
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data["access_token"]
            self._token_expires = datetime.now() + timedelta(seconds=data["expires_in"])
            
            logger.info("Successfully refreshed Twitter token")
        except Exception as e:
            logger.error(f"Error refreshing Twitter token: {str(e)}")
            raise

    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Fetch a Twitter user's profile using API."""
        try:
            response = requests.get(
                f"{self.base_url}/users/by/username/{username}",
                headers=self._get_headers(),
                params={
                    "user.fields": "description,public_metrics,created_at,location"
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "profile": response.json()["data"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Twitter profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def scrape_profile(self, profile_url: str) -> Dict[str, Any]:
        """Scrape a Twitter profile page."""
        try:
            response = requests.get(
                profile_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract profile information
            profile = {
                "name": self._extract_name(soup),
                "username": self._extract_username(soup),
                "bio": self._extract_bio(soup),
                "location": self._extract_location(soup),
                "website": self._extract_website(soup),
                "join_date": self._extract_join_date(soup),
                "tweets": self._extract_tweets(soup),
                "following": self._extract_following(soup),
                "followers": self._extract_followers(soup)
            }
            
            return {
                "success": True,
                "profile": profile
            }
        except Exception as e:
            logger.error(f"Error scraping Twitter profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Extract name from profile page."""
        try:
            return soup.find("span", class_="ProfileHeaderCard-nameLink").text.strip()
        except:
            return ""

    def _extract_username(self, soup: BeautifulSoup) -> str:
        """Extract username from profile page."""
        try:
            return soup.find("span", class_="ProfileHeaderCard-screenname").text.strip()
        except:
            return ""

    def _extract_bio(self, soup: BeautifulSoup) -> str:
        """Extract bio from profile page."""
        try:
            return soup.find("p", class_="ProfileHeaderCard-bio").text.strip()
        except:
            return ""

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location from profile page."""
        try:
            return soup.find("span", class_="ProfileHeaderCard-locationText").text.strip()
        except:
            return ""

    def _extract_website(self, soup: BeautifulSoup) -> str:
        """Extract website from profile page."""
        try:
            return soup.find("a", class_="ProfileHeaderCard-urlText").text.strip()
        except:
            return ""

    def _extract_join_date(self, soup: BeautifulSoup) -> str:
        """Extract join date from profile page."""
        try:
            return soup.find("span", class_="ProfileHeaderCard-joinDateText").text.strip()
        except:
            return ""

    def _extract_tweets(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract recent tweets from profile page."""
        tweets = []
        try:
            tweet_list = soup.find("div", class_="ProfileTimeline")
            if tweet_list:
                for tweet in tweet_list.find_all("div", class_="tweet"):
                    tweet_data = {
                        "text": self._safe_extract(tweet, ".tweet-text"),
                        "timestamp": self._safe_extract(tweet, ".tweet-timestamp"),
                        "retweets": self._safe_extract(tweet, ".retweet-count"),
                        "likes": self._safe_extract(tweet, ".like-count")
                    }
                    tweets.append(tweet_data)
        except:
            pass
        return tweets

    def _extract_following(self, soup: BeautifulSoup) -> int:
        """Extract following count from profile page."""
        try:
            return int(soup.find("a", {"href": re.compile(r"/following$")}).text.strip().replace(",", ""))
        except:
            return 0

    def _extract_followers(self, soup: BeautifulSoup) -> int:
        """Extract followers count from profile page."""
        try:
            return int(soup.find("a", {"href": re.compile(r"/followers$")}).text.strip().replace(",", ""))
        except:
            return 0

    def _safe_extract(self, element: BeautifulSoup, selector: str) -> str:
        """Safely extract text from an element."""
        try:
            return element.select_one(selector).text.strip()
        except:
            return ""

    def send_direct_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Send a direct message to a Twitter user."""
        try:
            response = requests.post(
                f"{self.base_url}/dm_conversations/with/{user_id}/messages",
                headers=self._get_headers(),
                json={"text": message}
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "message_id": response.json()["data"]["id"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Twitter DM: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_message_analytics(self, message_id: str) -> Dict[str, Any]:
        """Get analytics for a sent message."""
        try:
            response = requests.get(
                f"{self.base_url}/messages/{message_id}/analytics",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "analytics": response.json()["data"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching message analytics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_user_tweets(self, username: str, max_results: int = 10) -> Dict[str, Any]:
        """Fetch recent tweets from a user."""
        try:
            response = requests.get(
                f"{self.base_url}/users/by/username/{username}/tweets",
                headers=self._get_headers(),
                params={
                    "max_results": max_results,
                    "tweet.fields": "created_at,public_metrics"
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "tweets": response.json()["data"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user tweets: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_user_followers(self, username: str, max_results: int = 100) -> Dict[str, Any]:
        """Fetch a user's followers."""
        try:
            response = requests.get(
                f"{self.base_url}/users/by/username/{username}/followers",
                headers=self._get_headers(),
                params={
                    "max_results": max_results,
                    "user.fields": "description,public_metrics"
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "followers": response.json()["data"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user followers: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def log_message(self, prospect_id: str, message: str, message_id: str, db: Optional[Any] = None) -> None:
        """Log a sent message to the database."""
        try:
            if not db:
                db = next(get_db())
            
            message_log = MessageLog(
                prospect_id=prospect_id,
                message_type=MessageType.TWITTER.value,
                content=message,
                sent_at=datetime.now(),
                status=MessageStatus.SENT.value,
                external_message_id=message_id
            )
            
            db.add(message_log)
            db.commit()
            
            logger.info(f"Logged Twitter message for prospect {prospect_id}")
        except Exception as e:
            logger.error(f"Error logging Twitter message: {str(e)}")
            if db:
                db.rollback()

    async def close(self):
        """Cleanup resources."""
        pass 