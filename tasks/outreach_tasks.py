from celery_app import celery_app
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, MessageTemplate, MessageLog, MessageType, MessageStatus
from database.session import get_db
from services.email_service import EmailService
from services.social_service import SocialService
from uuid import UUID
from datetime import datetime

@celery_app.task
def send_outreach_message(prospect_id: str, template_id: str, message_type: str, campaign_id: str = None):
    """Send personalized outreach message (email, Twitter, or LinkedIn)."""
    db = next(get_db())
    email_service = EmailService()
    social_service = SocialService()
    
    try:
        # Get prospect and template
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == UUID(prospect_id)).first()
        template = db.query(MessageTemplate).filter(MessageTemplate.id == UUID(template_id)).first()
        
        if not prospect or not template:
            return {"success": False, "error": "Prospect or template not found"}
        
        if not prospect.consent_given:
            return {"success": False, "error": "No consent given"}
        
        prospect_data = {
            "first_name": prospect.first_name,
            "last_name": prospect.last_name,
            "company": prospect.company,
            "website": prospect.website,
            "email": prospect.email,
            "social_profiles": prospect.social_profiles or {}
        }
        
        success = False
        message_id = None
        
        if message_type == "email":
            personalized_content = email_service.personalize_message(template.content, prospect_data)
            personalized_subject = email_service.personalize_message(
                template.subject or "Partnership Opportunity", prospect_data
            )
            success = email_service.send_email(
                prospect.email,
                personalized_subject,
                personalized_content
            )
            message_id = str(uuid.uuid4())
        elif message_type == "twitter":
            twitter_id = prospect_data["social_profiles"].get("twitter", {}).get("user_id")
            if not twitter_id:
                return {"success": False, "error": "Twitter user ID not found"}
            result = social_service.send_twitter_dm(prospect_id, twitter_id, template.content, 
                                                  prospect_data, campaign_id, db)
            success = result["success"]
            message_id = result.get("message_id")
        elif message_type == "linkedin":
            linkedin_urn = prospect_data["social_profiles"].get("linkedin", {}).get("urn")
            if not linkedin_urn:
                return {"success": False, "error": "LinkedIn URN not found"}
            result = social_service.send_linkedin_message(prospect_id, linkedin_urn, template.content, 
                                                        prospect_data, campaign_id, db)
            success = result["success"]
            message_id = result.get("message_id")
        else:
            return {"success": False, "error": f"Unsupported message type: {message_type}"}
        
        # Log the message
        message_log = MessageLog(
            id=UUID(message_id),
            prospect_id=UUID(prospect_id),
            campaign_id=UUID(campaign_id) if campaign_id else None,
            template_id=UUID(template_id),
            message_type=MessageType(message_type),
            subject=personalized_subject if message_type == "email" else None,
            content=personalized_content if message_type == "email" else template.content,
            sent_at=datetime.utcnow(),
            status=MessageStatus.SENT if success else MessageStatus.BOUNCED
        )
        
        db.add(message_log)
        if success:
            prospect.status = ProspectStatus.CONTACTED
        db.commit()
        
        return {"success": success, "message_id": message_id}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()