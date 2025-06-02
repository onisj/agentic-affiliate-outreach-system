from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import requests
from jinja2 import Template
from sqlalchemy.orm import Session
from database.models import MessageLog, MessageType, MessageStatus
from config import settings

class SocialService:
    def __init__(self):
        self.twitter_api_url = "https://api.twitter.com/2"
        self.linkedin_api_url = "https://api.linkedin.com/v2"
        self.twitter_bearer_token = settings.TWITTER_BEARER_TOKEN
        self.linkedin_access_token = settings.LINKEDIN_ACCESS_TOKEN
    
    def send_twitter_dm(self, prospect_id: str, user_id: str, template: str, 
                       prospect_data: Dict[str, Any], campaign_id: Optional[str] = None, 
                       db: Session = None) -> Dict[str, Any]:
        """Send a Twitter DM to a prospect"""
        try:
            # Personalize message
            template_obj = Template(template)
            context = {
                'first_name': prospect_data.get('first_name', 'there'),
                'company': prospect_data.get('company', 'your company'),
                'company_mention': f"I noticed you work at {prospect_data.get('company', 'your company')}"
            }
            personalized_content = template_obj.render(**context)
            
            # Twitter DM payload
            payload = {
                "event": {
                    "type": "message_create",
                    "message_create": {
                        "target": {"recipient_id": user_id},
                        "message_data": {"text": personalized_content[:280]}  # Twitter DM limit
                    }
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.twitter_bearer_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.twitter_api_url}/direct_messages/events/new",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            
            # Log the message
            message_log = MessageLog(
                id=uuid.uuid4(),
                prospect_id=uuid.UUID(prospect_id),
                campaign_id=uuid.UUID(campaign_id) if campaign_id else None,
                message_type=MessageType.TWITTER,
                content=personalized_content,
                sent_at=datetime.utcnow(),
                status=MessageStatus.SENT if success else MessageStatus.BOUNCED
            )
            
            db.add(message_log)
            db.commit()
            
            return {"success": success, "message_id": str(message_log.id)}
        
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def send_linkedin_message(self, prospect_id: str, urn: str, template: str, 
                            prospect_data: Dict[str, Any], campaign_id: Optional[str] = None, 
                            db: Session = None) -> Dict[str, Any]:
        """Send a LinkedIn message to a prospect"""
        try:
            # Personalize message
            template_obj = Template(template)
            context = {
                'first_name': prospect_data.get('first_name', 'there'),
                'company': prospect_data.get('company', 'your company'),
                'company_mention': f"I noticed you work at {prospect_data.get('company', 'your company')}"
            }
            personalized_content = template_obj.render(**context)
            
            # LinkedIn message payload
            payload = {
                "recipients": [{"personUrn": f"urn:li:person:{urn}"}],
                "message": {
                    "body": personalized_content[:1000]  # LinkedIn message limit
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.linkedin_api_url}/messaging/conversations",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 201
            
            # Log the message
            message_log = MessageLog(
                id=uuid.uuid4(),
                prospect_id=uuid.UUID(prospect_id),
                campaign_id=uuid.UUID(campaign_id) if campaign_id else None,
                message_type=MessageType.LINKEDIN,
                content=personalized_content,
                sent_at=datetime.utcnow(),
                status=MessageStatus.SENT if success else MessageStatus.BOUNCED
            )
            
            db.add(message_log)
            db.commit()
            
            return {"success": success, "message_id": str(message_log.id)}
        
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}