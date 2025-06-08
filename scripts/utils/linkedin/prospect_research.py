#!/usr/bin/env python3
"""
LinkedIn Prospect Research Script

This script demonstrates how to:
1. Fetch prospect profiles
2. Analyze their professional background
3. Check connection status
4. Prepare personalized outreach
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from utils.base_script import BaseScript
from services.social_service import SocialService

class ProspectResearcher(BaseScript):
    def __init__(self):
        super().__init__("linkedin_prospect_research")
        self.social_service = SocialService()

    def fetch_prospect_profile(self, urn: str) -> Dict[str, Any]:
        """Fetch and analyze a prospect's LinkedIn profile."""
        self.logger.info(f"Fetching profile for URN: {urn}")
        result = self.social_service.get_linkedin_profile(urn)
        
        if not result["success"]:
            self.logger.error(f"Failed to fetch profile: {result['error']}")
            return None
            
        profile = result["profile"]
        return self._analyze_profile(profile)

    def _analyze_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze profile data and extract relevant information."""
        analysis = {
            "name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}",
            "headline": profile.get("headline", ""),
            "industry": profile.get("industry", ""),
            "location": profile.get("location", {}).get("name", ""),
            "current_position": None,
            "company": None,
            "experience_years": 0,
            "skills": [],
            "education": []
        }

        # Extract current position
        positions = profile.get("positions", {}).get("values", [])
        for position in positions:
            if position.get("isCurrent", False):
                analysis["current_position"] = position.get("title", "")
                analysis["company"] = position.get("company", {}).get("name", "")
                break

        # Calculate experience years
        for position in positions:
            start_date = position.get("startDate", {})
            if start_date:
                start_year = start_date.get("year", datetime.now().year)
                analysis["experience_years"] += (datetime.now().year - start_year)

        # Extract skills
        skills = profile.get("skills", {}).get("values", [])
        analysis["skills"] = [skill.get("name", "") for skill in skills]

        # Extract education
        education = profile.get("educations", {}).get("values", [])
        analysis["education"] = [
            {
                "school": edu.get("schoolName", ""),
                "degree": edu.get("degree", ""),
                "field": edu.get("fieldOfStudy", "")
            }
            for edu in education
        ]

        return analysis

    def check_connection_status(self, urn: str) -> bool:
        """Check if we're connected with the prospect."""
        self.logger.info(f"Checking connection status for URN: {urn}")
        result = self.social_service.get_linkedin_connections()
        
        if not result["success"]:
            self.logger.error(f"Failed to fetch connections: {result['error']}")
            return False
            
        connections = result["connections"]
        return any(conn.get("id") == urn for conn in connections)

    def prepare_outreach_message(self, profile_analysis: Dict[str, Any]) -> str:
        """Prepare a personalized outreach message based on profile analysis."""
        template = f"""Hi {profile_analysis['name'].split()[0]},

I noticed you're a {profile_analysis['current_position']} at {profile_analysis['company']} with {profile_analysis['experience_years']} years of experience in {profile_analysis['industry']}.

Your background in {', '.join(profile_analysis['skills'][:3])} caught my attention, as we're looking for partners who share our commitment to excellence.

Would you be interested in learning more about our affiliate program? We offer competitive rates and a supportive community of partners.

Best regards,
[Your Name]"""

        return template

    def save_analysis(self, analysis: Dict[str, Any], filename: str):
        """Save profile analysis to a JSON file."""
        output_dir = Path("data/linkedin/prospect_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        self.logger.info(f"Analysis saved to {output_file}")

    def run(self):
        """Main execution method."""
        # Example URNs (replace with actual URNs)
        prospect_urns = [
            "urn:li:person:123",
            "urn:li:person:456"
        ]
        
        for urn in prospect_urns:
            try:
                # Fetch and analyze profile
                profile_analysis = self.fetch_prospect_profile(urn)
                if not profile_analysis:
                    continue
                    
                # Check connection status
                is_connected = self.check_connection_status(urn)
                
                # Prepare outreach message
                message = self.prepare_outreach_message(profile_analysis)
                
                # Save analysis
                filename = f"prospect_analysis_{urn.split(':')[-1]}.json"
                self.save_analysis({
                    "profile": profile_analysis,
                    "is_connected": is_connected,
                    "outreach_message": message
                }, filename)
                
                self.logger.info(f"Analysis completed for {profile_analysis['name']}")
                
            except Exception as e:
                self.logger.error(f"Error processing prospect {urn}: {str(e)}")

def main():
    script = ProspectResearcher()
    script.main()

if __name__ == "__main__":
    main() 