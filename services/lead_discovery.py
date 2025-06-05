from typing import List, Dict, Any
import requests
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, ProspectStatus
from config.settings import settings
import uuid
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from database.base import Base

logger = logging.getLogger(__name__)

class LeadDiscoveryService:
    def __init__(self):
        self.twitter_api_url = "https://api.twitter.com/2"
        self.linkedin_api_url = "https://api.linkedin.com/v2"
        self.instagram_api_url = "https://graph.instagram.com/v12.0"
        self.twitter_bearer_token = settings.TWITTER_BEARER_TOKEN
        self.linkedin_access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.instagram_access_token = settings.INSTAGRAM_ACCESS_TOKEN
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def discover_twitter_prospects(self, keywords: List[str], min_followers: int = 1000, 
                                 db: Session = None) -> Dict[str, Any]:
        """Discover potential affiliates on Twitter with rate limiting."""
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
            logger.error(f"Error in Twitter discovery: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def discover_instagram_prospects(self, keywords: List[str], min_followers: int = 1000, 
                                   db: Session = None) -> Dict[str, Any]:
        """Discover potential affiliates on Instagram with rate limiting."""
        try:
            headers = {"Authorization": f"Bearer {self.instagram_access_token}"}
            query = " ".join(keywords)
            
            # Search for hashtags first
            hashtag_response = requests.get(
                f"{self.instagram_api_url}/hashtag/search",
                headers=headers,
                params={"q": query},
                timeout=10
            )
            
            if hashtag_response.status_code != 200:
                return {"success": False, "error": f"Instagram hashtag search failed: {hashtag_response.text}"}
            
            hashtags = hashtag_response.json().get('data', [])
            prospects = []
            
            for hashtag in hashtags[:5]:  # Limit to top 5 hashtags
                # Get recent media for each hashtag
                media_response = requests.get(
                    f"{self.instagram_api_url}/hashtag/{hashtag['id']}/recent_media",
                    headers=headers,
                    params={"fields": "id,username,media_count,followers_count"},
                    timeout=10
                )
                
                if media_response.status_code != 200:
                    continue
                
                users = media_response.json().get('data', [])
                
                for user in users:
                    if user.get('followers_count', 0) >= min_followers:
                        prospect_data = {
                            'email': None,
                            'first_name': None,  # Instagram doesn't provide first/last name
                            'last_name': None,
                            'social_profiles': {
                                'instagram': {
                                    'user_id': user.get('id'),
                                    'username': user.get('username'),
                                    'followers': user.get('followers_count'),
                                    'media_count': user.get('media_count')
                                }
                            },
                            'lead_source': 'instagram_discovery',
                            'consent_given': False
                        }
                        
                        existing = db.query(AffiliateProspect).filter(
                            AffiliateProspect.social_profiles['instagram']['username'].astext == user.get('username')
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
            logger.error(f"Error in Instagram discovery: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def discover_linkedin_prospects(self, keywords: List[str], db: Session = None) -> Dict[str, Any]:
        """Discover potential affiliates on LinkedIn with rate limiting."""
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
            logger.error(f"Error in LinkedIn discovery: {str(e)}")
            return {"success": False, "error": str(e)}