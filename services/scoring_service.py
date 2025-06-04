# services/scoring_service.py
from typing import Dict, Any
import re
import requests
from bs4 import BeautifulSoup
from services.validator import DataValidator

class LeadScoringService:
    def __init__(self):
        self.max_score = 100
        self.validator = DataValidator()

    def calculate_score(self, prospect_data: Dict[str, Any]) -> int:
        """Calculate prospect qualification score based on email, website, social profiles, and company."""
        score = 0

        # Email scoring (20 points max)
        email = prospect_data.get("email", "")
        if self.validator.validate_email(email)["is_valid"]:
            score += 20 if self._is_business_email(email) else 10

        # Website scoring (20 points max)
        website = prospect_data.get("website")
        if website and self.validator.validate_website(website)["is_valid"]:
            score += 15
            # Bonus for website quality
            website_bonus = self._analyze_website(website)
            score += website_bonus

        # Social profiles scoring (30 points max)
        social_profiles = prospect_data.get("social_profiles", {})
        if social_profiles.get("twitter", {}).get("followers", 0) > 1000:
            score += 30

        # Company scoring (30 points max)
        if prospect_data.get("company"):
            score += 30

        return min(score, self.max_score)

    def _is_business_email(self, email: str) -> bool:
        """Check if email is from a business domain."""
        free_domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "aol.com", "icloud.com", "protonmail.com"
        ]
        if not email:
            return False
        domain = email.split("@")[-1].lower()
        return domain not in free_domains

    def _analyze_website(self, website: str) -> int:
        """Analyze website quality for bonus points (up to 5)."""
        try:
            if not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            response = requests.head(website, timeout=5, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AffiliateBot/1.0)"
            })
            if response.status_code >= 400:
                return 0

            # Perform light content analysis
            response = requests.get(website, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                score = 0
                if soup.title and soup.title.string:
                    score += 3
                if soup.find("meta", attrs={"name": "description"}):
                    score += 2
                return score
        except (requests.exceptions.RequestException, ValueError):
            return 0
        return 0