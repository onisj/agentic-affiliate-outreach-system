"""Unified outreach service for managing campaigns and lead discovery.

This service provides functionality for:
1. Multi-channel outreach campaign management
2. Lead discovery across social platforms
3. Campaign analytics and tracking
4. Message personalization and delivery
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import (
    OutreachCampaign,
    MessageTemplate,
    MessageLog,
    MessageType,
    MessageStatus,
    CampaignStatus,
    AffiliateProspect,
    ProspectStatus
)
from services.email_service import EmailService
from services.linkedin import LinkedInService
from services.twitter import TwitterService
import asyncio
from jinja2 import Template
import requests
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
from services.outreach import OutreachService

logger = logging.getLogger(__name__)

class OutreachService:
    """Unified service for outreach campaigns and lead discovery."""
    
    def __init__(self, db: Session):
        """Initialize the outreach service with database session and channel services."""
        self.db = db
        self.channels = {
            MessageType.EMAIL: EmailService(),
            MessageType.LINKEDIN: LinkedInService(),
            MessageType.TWITTER: TwitterService()
        }
        
        # API endpoints
        self.twitter_api_url = "https://api.twitter.com/2"
        self.linkedin_api_url = "https://api.linkedin.com/v2"
        self.instagram_api_url = "https://graph.instagram.com/v12.0"
        
        # API credentials
        self.twitter_bearer_token = settings.TWITTER_BEARER_TOKEN
        self.linkedin_access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.instagram_access_token = settings.INSTAGRAM_ACCESS_TOKEN

    # Campaign Management Methods
    async def create_campaign(
        self,
        name: str,
        template_id: str,
        target_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new outreach campaign."""
        try:
            campaign = OutreachCampaign(
                name=name,
                template_id=template_id,
                target_criteria=target_criteria,
                status=CampaignStatus.DRAFT
            )
            self.db.add(campaign)
            self.db.commit()
            
            return {
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status,
                "created_at": campaign.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            self.db.rollback()
            raise

    async def start_campaign(self, campaign_id: str) -> bool:
        """Start an outreach campaign."""
        try:
            campaign = self.db.query(OutreachCampaign).filter(
                OutreachCampaign.id == campaign_id
            ).first()
            
            if not campaign:
                return False
            
            if campaign.status != CampaignStatus.DRAFT:
                raise ValueError("Campaign must be in DRAFT status to start")
            
            campaign.status = CampaignStatus.ACTIVE
            self.db.commit()
            
            # Start sending messages in the background
            asyncio.create_task(self._process_campaign(campaign))
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting campaign: {e}")
            self.db.rollback()
            return False

    async def _process_campaign(self, campaign: OutreachCampaign):
        """Process an active campaign by sending messages."""
        try:
            template = self.db.query(MessageTemplate).filter(
                MessageTemplate.id == campaign.template_id
            ).first()
            
            if not template:
                logger.error(f"Template not found for campaign {campaign.id}")
                return
            
            # Get target affiliates based on criteria
            target_affiliates = await self._get_target_affiliates(campaign.target_criteria)
            
            for affiliate in target_affiliates:
                try:
                    # Personalize message
                    message_content = await self._personalize_message(
                        template.content,
                        affiliate
                    )
                    
                    # Send message through appropriate channel
                    channel = self.channels.get(template.message_type)
                    if not channel:
                        logger.error(f"Unsupported message type: {template.message_type}")
                        continue
                    
                    # Create message log entry
                    message_log = MessageLog(
                        prospect_id=affiliate["id"],
                        campaign_id=campaign.id,
                        template_id=template.id,
                        message_type=template.message_type,
                        subject=template.subject,
                        content=message_content,
                        status=MessageStatus.PENDING
                    )
                    self.db.add(message_log)
                    self.db.commit()
                    
                    # Send message
                    success = await channel.send_message(
                        to=affiliate["contact_info"],
                        subject=template.subject,
                        content=message_content
                    )
                    
                    if success:
                        message_log.status = MessageStatus.SENT
                        message_log.sent_at = datetime.now()
                    else:
                        message_log.status = MessageStatus.BOUNCED
                    
                    self.db.commit()
                    
                    # Add delay between messages to avoid rate limits
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing affiliate {affiliate['id']}: {e}")
                    continue
            
            # Mark campaign as completed
            campaign.status = CampaignStatus.COMPLETED
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing campaign {campaign.id}: {e}")
            campaign.status = CampaignStatus.PAUSED
            self.db.commit()

    async def _get_target_affiliates(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get target affiliates based on campaign criteria."""
        try:
            query = self.db.query(AffiliateProspect)
            
            # Apply filters based on criteria
            if "min_followers" in criteria:
                query = query.filter(
                    AffiliateProspect.social_profiles['twitter']['followers'].astext.cast(Integer) >= criteria["min_followers"]
                )
            
            if "status" in criteria:
                query = query.filter(AffiliateProspect.status == criteria["status"])
            
            if "lead_source" in criteria:
                query = query.filter(AffiliateProspect.lead_source == criteria["lead_source"])
            
            # Get results
            prospects = query.all()
            return [
                {
                    "id": str(p.id),
                    "email": p.email,
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "social_profiles": p.social_profiles,
                    "contact_info": self._get_contact_info(p)
                }
                for p in prospects
            ]
            
        except Exception as e:
            logger.error(f"Error getting target affiliates: {e}")
            return []

    def _get_contact_info(self, prospect: AffiliateProspect) -> Dict[str, Any]:
        """Get contact information for a prospect based on available channels."""
        contact_info = {}
        
        if prospect.email:
            contact_info["email"] = prospect.email
            
        if "twitter" in prospect.social_profiles:
            contact_info["twitter"] = prospect.social_profiles["twitter"]["user_id"]
            
        if "linkedin" in prospect.social_profiles:
            contact_info["linkedin"] = prospect.social_profiles["linkedin"]["urn"]
            
        return contact_info

    async def _personalize_message(self, template: str, affiliate: Dict[str, Any]) -> str:
        """Personalize message template with affiliate data."""
        try:
            jinja_template = Template(template)
            return jinja_template.render(**affiliate)
        except Exception as e:
            logger.error(f"Error personalizing message: {e}")
            return template

    async def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get current status of a campaign."""
        campaign = self.db.query(OutreachCampaign).filter(
            OutreachCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            return None
        
        # Get message statistics
        message_stats = self.db.query(
            MessageLog.status,
            func.count(MessageLog.id)
        ).filter(
            MessageLog.campaign_id == campaign_id
        ).group_by(MessageLog.status).all()
        
        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat(),
            "message_stats": dict(message_stats)
        }

    # Lead Discovery Methods
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def discover_twitter_prospects(
        self,
        keywords: List[str],
        min_followers: int = 1000
    ) -> Dict[str, Any]:
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
                    
                    existing = self.db.query(AffiliateProspect).filter(
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
                        self.db.add(db_prospect)
                        prospects.append(prospect_data)
            
            self.db.commit()
            return {"success": True, "prospects": prospects}
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in Twitter discovery: {str(e)}")
            return {"success": False, "error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def discover_instagram_prospects(
        self,
        keywords: List[str],
        min_followers: int = 1000
    ) -> Dict[str, Any]:
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
                        
                        existing = self.db.query(AffiliateProspect).filter(
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
                            self.db.add(db_prospect)
                            prospects.append(prospect_data)
            
            self.db.commit()
            return {"success": True, "prospects": prospects}
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in Instagram discovery: {str(e)}")
            return {"success": False, "error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def discover_linkedin_prospects(self, keywords: List[str]) -> Dict[str, Any]:
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
                
                if not urn or not public_id:
                    continue
                
                # Get detailed profile information
                profile_response = requests.get(
                    f"{self.linkedin_api_url}/people/{urn}",
                    headers=headers,
                    timeout=10
                )
                
                if profile_response.status_code != 200:
                    continue
                
                profile_data = profile_response.json()
                
                prospect_data = {
                    'email': None,
                    'first_name': profile_data.get('firstName'),
                    'last_name': profile_data.get('lastName'),
                    'social_profiles': {
                        'linkedin': {
                            'urn': urn,
                            'public_id': public_id,
                            'headline': profile_data.get('headline'),
                            'industry': profile_data.get('industry')
                        }
                    },
                    'lead_source': 'linkedin_discovery',
                    'consent_given': False
                }
                
                existing = self.db.query(AffiliateProspect).filter(
                    AffiliateProspect.social_profiles['linkedin']['urn'].astext == urn
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
                    self.db.add(db_prospect)
                    prospects.append(prospect_data)
            
            self.db.commit()
            return {"success": True, "prospects": prospects}
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in LinkedIn discovery: {str(e)}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close all channel connections."""
        for channel in self.channels.values():
            await channel.close()

    def send_outreach(self, message: str):
        print(f"Sending outreach: {message}") 