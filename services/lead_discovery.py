from typing import List, Dict, Any
import requests
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, ProspectStatus
from config.settings import settings
import uuid
from datetime import datetime, timezone

class LeadDiscoveryService:
    def __init__(self):
        self.twitter_api_url = "https://api.twitter.com/2"
        self.linkedin_api_url = "https://api.linkedin.com/v2"
        self.twitter_bearer_token = settings.TWITTER_BEARER_TOKEN
        self.linkedin_access_token = settings.LINKEDIN_ACCESS_TOKEN
    
    def discover_twitter_prospects(self, keywords: List[str], min_followers: int = 1000, 
                                 db: Session = None) -> Dict[str, Any]:
        """Discover potential affiliates on Twitter."""
        try:
            query = " ".join(keywords) + " -is:retweet lang:en"
            headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}
            params = {
                "query": query,
                "user.fields": "id,username,name,followers_count",
                "max_results": 100
            }
            
            response = requests.get(
                f"{self.twitter_api_url}/tweets/search/recent",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Twitter API request failed: {response.text}"}
            
            users = response.json().get('includes', {}).get('users', [])
            prospects = []
            
            for user in users:
                if user.get('followers_count', 0) >= min_followers:
                    prospect_data = {
                        'email': None,
                        'first_name': user.get('name').split()[0] if user.get('name') else None,
                        'last_name': ' '.join(user.get('name').split()[1:]) if len(user.get('name').split()) > 1 else None,
                        'social_profiles': {
                            'twitter': {
                                'user_id': user.get('id'),
                                'username': user.get('username'),
                                'followers': user.get('followers_count')
                            }
                        },
                        'lead_source': 'twitter_discovery',
                        'consent_given': False
                    }
                    
                    existing = db.query(AffiliateProspect).filter(
                        AffiliateProspect.social_profiles['twitter']['username'].astext == user.get('username')
                    ).first()
                    
                    if not existing:
                        db_prospect = AffiliateProspect(
                            id=uuid.uuid4(),
                            email=prospect_data['email'],
                            first_name=prospect_data['first_name'],
                            last_name=prospect_data['last_name'],
                            social_profiles=prospect_data['social_profiles'],
                            lead_source=prospect_data['lead_source'],
                            consent_given=prospect_data['consent_given'],
                            status=ProspectStatus.NEW,
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(db_prospect)
                        prospects.append(prospect_data)
            
            db.commit()
            return {"success": True, "prospects": prospects}
        
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def discover_linkedin_prospects(self, keywords: List[str], db: Session = None) -> Dict[str, Any]:
        """Discover potential affiliates on LinkedIn."""
        try:
            headers = {"Authorization": f"Bearer {self.linkedin_access_token}"}
            params = {
                "q": "people",
                "keywords": " ".join(keywords),
                "count": 10
            }
            
            response = requests.get(
                f"{self.linkedin_api_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"LinkedIn API request failed: {response.text}"}
            
            profiles = response.json().get('elements', [])
            prospects = []
            
            for profile in profiles:
                urn = profile.get('urn')
                public_id = profile.get('publicIdentifier')
                prospect_data = {
                    'email': None,
                    'first_name': profile.get('firstName'),
                    'last_name': profile.get('lastName'),
                    'social_profiles': {
                        'linkedin': {
                            'urn': urn,
                            'public_id': public_id
                        }
                    },
                    'lead_source': 'linkedin_discovery',
                    'consent_given': False
                }
                
                existing = db.query(AffiliateProspect).filter(
                    AffiliateProspect.social_profiles['linkedin']['public_id'].astext == public_id
                ).first()
                
                if not existing:
                    db_prospect = AffiliateProspect(
                        id=uuid.uuid4(),
                        email=prospect_data['email'],
                        first_name=prospect_data['first_name'],
                        last_name=prospect_data['last_name'],
                        social_profiles=prospect_data['social_profiles'],
                        lead_source=prospect_data['lead_source'],
                        consent_given=prospect_data['consent_given'],
                        status=ProspectStatus.NEW,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(db_prospect)
                    prospects.append(prospect_data)
            
            db.commit()
            return {"success": True, "prospects": prospects}
        
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}