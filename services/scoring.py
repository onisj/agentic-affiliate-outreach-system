from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
import re

class LeadScoringService:
    def __init__(self):
        self.max_score = 100
    
    def calculate_score(self, prospect_data: Dict[str, Any]) -> int:
        """Calculate lead score based on various factors"""
        score = 0
        
        # Email domain scoring (free vs business email)
        email = prospect_data.get('email', '')
        if self._is_business_email(email):
            score += 15
        
        # Website presence
        website = prospect_data.get('website')
        if website:
            score += 20
            # Additional points for website quality
            website_score = self._analyze_website(website)
            score += website_score
        
        # Company information
        if prospect_data.get('company'):
            score += 10
        
        # Social media presence
        social_profiles = prospect_data.get('social_profiles', {})
        score += self._score_social_presence(social_profiles)
        
        # Name completeness
        if prospect_data.get('first_name') and prospect_data.get('last_name'):
            score += 5
        
        return min(score, self.max_score)
    
    def _is_business_email(self, email: str) -> bool:
        """Check if email is from a business domain"""
        free_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com'
        ]
        domain = email.split('@')[-1].lower()
        return domain not in free_domains
    
    def _analyze_website(self, website: str) -> int:
        """Analyze website quality and return score"""
        try:
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            
            response = requests.get(website, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; AffiliateBot/1.0)'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                score = 0
                # Has title
                if soup.title:
                    score += 5
                
                # Has meta description
                if soup.find('meta', attrs={'name': 'description'}):
                    score += 5
                
                # Content length (indicates active site)
                content_length = len(soup.get_text())
                if content_length > 1000:
                    score += 10
                elif content_length > 500:
                    score += 5
                
                return score
            
        except Exception:
            pass
        
        return 0
    
    def _score_social_presence(self, social_profiles: Dict[str, Any]) -> int:
        """Score based on social media presence"""
        score = 0
        
        for platform, profile in social_profiles.items():
            if profile and isinstance(profile, dict):
                # Has profile
                score += 5
                
                # Follower count
                followers = profile.get('followers', 0)
                if followers > 10000:
                    score += 15
                elif followers > 1000:
                    score += 10
                elif followers > 100:
                    score += 5
        
        return min(score, 25)  # Max 25 points for social