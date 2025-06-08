#!/usr/bin/env python3
"""
Twitter Prospect Research Script

This script demonstrates how to:
1. Fetch prospect profiles
2. Analyze their tweets and engagement
3. Check follower status
4. Prepare personalized outreach
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from utils.base_script import BaseScript
from services.twitter import TwitterService

class TwitterProspectResearcher(BaseScript):
    def __init__(self):
        super().__init__("twitter_prospect_research")
        self.twitter_service = TwitterService()

    def fetch_prospect_profile(self, username: str) -> Dict[str, Any]:
        """Fetch and analyze a prospect's Twitter profile."""
        self.logger.info(f"Fetching profile for username: {username}")
        result = self.twitter_service.get_user_profile(username)
        
        if not result["success"]:
            self.logger.error(f"Failed to fetch profile: {result['error']}")
            return None
            
        profile = result["profile"]
        return self._analyze_profile(profile)

    def _analyze_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze profile data and extract relevant information."""
        metrics = profile.get("public_metrics", {})
        
        analysis = {
            "username": profile.get("username", ""),
            "name": profile.get("name", ""),
            "description": profile.get("description", ""),
            "location": profile.get("location", ""),
            "created_at": profile.get("created_at", ""),
            "metrics": {
                "followers": metrics.get("followers_count", 0),
                "following": metrics.get("following_count", 0),
                "tweets": metrics.get("tweet_count", 0),
                "listed": metrics.get("listed_count", 0)
            },
            "recent_tweets": [],
            "engagement_rate": 0
        }

        # Fetch recent tweets
        tweets_result = self.twitter_service.get_user_tweets(profile["username"])
        if tweets_result["success"]:
            analysis["recent_tweets"] = tweets_result["tweets"]
            
            # Calculate engagement rate
            total_engagement = sum(
                tweet["public_metrics"]["like_count"] + 
                tweet["public_metrics"]["retweet_count"]
                for tweet in tweets_result["tweets"]
            )
            analysis["engagement_rate"] = (
                total_engagement / len(tweets_result["tweets"])
                if tweets_result["tweets"]
                else 0
            )

        return analysis

    def check_follower_status(self, username: str) -> bool:
        """Check if we're following the prospect."""
        self.logger.info(f"Checking follower status for username: {username}")
        # Note: This would require additional API endpoints
        # For now, we'll return False
        return False

    def prepare_outreach_message(self, profile_analysis: Dict[str, Any]) -> str:
        """Prepare a personalized outreach message based on profile analysis."""
        template = f"""Hi {profile_analysis['name']},

I've been following your Twitter content and noticed your expertise in {profile_analysis['description'][:100]}...

Your engagement rate of {profile_analysis['engagement_rate']:.2f}% shows you have a strong connection with your audience, which aligns perfectly with our affiliate program's goals.

Would you be interested in learning more about our affiliate program? We offer competitive rates and a supportive community of partners.

Best regards,
[Your Name]"""

        return template

    def save_analysis(self, analysis: Dict[str, Any], filename: str):
        """Save profile analysis to a JSON file."""
        output_dir = Path("data/twitter/prospect_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        self.logger.info(f"Analysis saved to {output_file}")

    def run(self):
        """Main execution method."""
        # Example usernames (replace with actual usernames)
        prospect_usernames = [
            "example1",
            "example2"
        ]
        
        for username in prospect_usernames:
            try:
                # Fetch and analyze profile
                profile_analysis = self.fetch_prospect_profile(username)
                if not profile_analysis:
                    continue
                    
                # Check follower status
                is_following = self.check_follower_status(username)
                
                # Prepare outreach message
                message = self.prepare_outreach_message(profile_analysis)
                
                # Save analysis
                filename = f"prospect_analysis_{username}.json"
                self.save_analysis({
                    "profile": profile_analysis,
                    "is_following": is_following,
                    "outreach_message": message
                }, filename)
                
                self.logger.info(f"Analysis completed for {profile_analysis['name']}")
                
            except Exception as e:
                self.logger.error(f"Error processing prospect {username}: {str(e)}")

def main():
    script = TwitterProspectResearcher()
    script.main()

if __name__ == "__main__":
    main() 