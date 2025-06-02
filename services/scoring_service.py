from typing import Dict, Any
from services.validator import DataValidator
import re

class LeadScoringService:
    def calculate_score(self, prospect_data: Dict[str, Any]) -> int:
        """Calculate prospect qualification score."""
        score = 0
        
        # Email validation (20 points max)
        if prospect_data.get('email'):
            email_validation = DataValidator.validate_email(prospect_data['email'])
            if email_validation['is_valid']:
                score += 10
                # Bonus for business email
                if not re.match(r'.*@(gmail\.com|yahoo\.com|hotmail\.com)$', prospect_data['email']):
                    score += 10
        
        # Website validation (20 points max)
        if prospect_data.get('website'):
            website_validation = DataValidator.validate_website(prospect_data['website'])
            if website_validation['is_valid']:
                score += 10
                if website_validation['is_reachable']:
                    score += 10
        
        # Social profiles (30 points max)
        social_profiles = prospect_data.get('social_profiles', {})
        if 'twitter' in social_profiles:
            followers = social_profiles['twitter'].get('followers', 0)
            if followers >= 1000:
                score += 15
        if 'linkedin' in social_profiles:
            score += 15
        
        # Company presence (30 points max)
        if prospect_data.get('company'):
            score += 20
            if prospect_data.get('website'):  # Company with website
                score += 10
        
        return min(score, 100)  # Cap at 100