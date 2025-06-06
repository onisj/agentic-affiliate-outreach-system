"""
LinkedIn Service

This module provides functionality for:
1. LinkedIn API integration
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

class LinkedInService:
    """Service for interacting with LinkedIn API and scraping."""
    
    def __init__(self):
        self.api_key = settings.LINKEDIN_API_KEY
        self.api_secret = settings.LINKEDIN_API_SECRET
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.base_url = "https://api.linkedin.com/v2"
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
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data["access_token"]
            self._token_expires = datetime.now() + timedelta(seconds=data["expires_in"])
            
            logger.info("Successfully refreshed LinkedIn token")
        except Exception as e:
            logger.error(f"Error refreshing LinkedIn token: {str(e)}")
            raise

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        """Fetch a LinkedIn profile using API."""
        try:
            response = requests.get(
                f"{self.base_url}/people/{profile_id}",
                headers=self._get_headers(),
                params={
                    "projection": "(id,firstName,lastName,headline,industry,location,positions,skills)"
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "profile": response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching LinkedIn profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def scrape_profile(self, profile_url: str) -> Dict[str, Any]:
        """Scrape a LinkedIn profile page."""
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
                "headline": self._extract_headline(soup),
                "location": self._extract_location(soup),
                "about": self._extract_about(soup),
                "experience": self._extract_experience(soup),
                "education": self._extract_education(soup),
                "skills": self._extract_skills(soup)
            }
            
            return {
                "success": True,
                "profile": profile
            }
        except Exception as e:
            logger.error(f"Error scraping LinkedIn profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Extract name from profile page."""
        try:
            return soup.find("h1", class_="text-heading-xlarge").text.strip()
        except:
            return ""

    def _extract_headline(self, soup: BeautifulSoup) -> str:
        """Extract headline from profile page."""
        try:
            return soup.find("div", class_="text-body-medium").text.strip()
        except:
            return ""

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location from profile page."""
        try:
            return soup.find("span", class_="text-body-small").text.strip()
        except:
            return ""

    def _extract_about(self, soup: BeautifulSoup) -> str:
        """Extract about section from profile page."""
        try:
            return soup.find("div", {"data-section": "about"}).text.strip()
        except:
            return ""

    def _extract_experience(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract experience from profile page."""
        experience = []
        try:
            exp_section = soup.find("section", {"id": "experience-section"})
            if exp_section:
                for item in exp_section.find_all("li", class_="pv-entity__position-group-pager"):
                    exp = {
                        "title": self._safe_extract(item, ".pv-entity__name"),
                        "company": self._safe_extract(item, ".pv-entity__secondary-title"),
                        "duration": self._safe_extract(item, ".pv-entity__date-range"),
                        "location": self._safe_extract(item, ".pv-entity__location")
                    }
                    experience.append(exp)
        except:
            pass
        return experience

    def _extract_education(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract education from profile page."""
        education = []
        try:
            edu_section = soup.find("section", {"id": "education-section"})
            if edu_section:
                for item in edu_section.find_all("li", class_="pv-education-entity"):
                    edu = {
                        "school": self._safe_extract(item, ".pv-entity__school-name"),
                        "degree": self._safe_extract(item, ".pv-entity__degree-name"),
                        "field": self._safe_extract(item, ".pv-entity__fos"),
                        "duration": self._safe_extract(item, ".pv-entity__dates")
                    }
                    education.append(edu)
        except:
            pass
        return education

    def _extract_skills(self, soup: BeautifulSoup) -> List[str]:
        """Extract skills from profile page."""
        skills = []
        try:
            skills_section = soup.find("section", {"id": "skills-section"})
            if skills_section:
                for item in skills_section.find_all("span", class_="pv-skill-category-entity__name"):
                    skills.append(item.text.strip())
        except:
            pass
        return skills

    def _safe_extract(self, element: BeautifulSoup, selector: str) -> str:
        """Safely extract text from an element."""
        try:
            return element.select_one(selector).text.strip()
        except:
            return ""

    def send_message(self, profile_id: str, message: str) -> Dict[str, Any]:
        """Send a message to a LinkedIn profile."""
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self._get_headers(),
                json={
                    "recipients": [{"person": {"id": profile_id}}],
                    "subject": "Connection Request",
                    "body": message
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "message_id": response.json()["id"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending LinkedIn message: {str(e)}")
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
                message_type=MessageType.LINKEDIN.value,
                content=message,
                sent_at=datetime.now(),
                status=MessageStatus.SENT.value,
                external_message_id=message_id
            )
            
            db.add(message_log)
            db.commit()
            
            logger.info(f"Logged LinkedIn message for prospect {prospect_id}")
        except Exception as e:
            logger.error(f"Error logging LinkedIn message: {str(e)}")
            if db:
                db.rollback()

    async def close(self):
        """Cleanup resources."""
        pass 