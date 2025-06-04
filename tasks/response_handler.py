from tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from database.models import MessageLog, AffiliateProspect, MessageTemplate, MessageType, MessageStatus
# from database.session import SessionLocal
from database.session import get_db
from services.email_service import EmailService
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime, timezone
from textblob import TextBlob
from config.settings import settings
import logging
from database.models import ProspectStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task
def handle_prospect_response(message_log_id: str, response_text: str) -> Dict[str, Any]:
    """Process a prospect's response and trigger follow-up if needed."""
    # db: Session = SessionLocal()
    db: Session = next(get_db())
    email_service = EmailService()
    
    try:
        message_log = db.query(MessageLog).filter(MessageLog.id == message_log_id).first()
        if not message_log:
            logger.error(f"Message log {message_log_id} not found")
            return {"success": False, "error": "Message log not found"}
        
        prospect = db.query(AffiliateProspect).filter(
            AffiliateProspect.id == message_log.prospect_id
        ).first()
        if not prospect:
            logger.error(f"Prospect for message log {message_log_id} not found")
            return {"success": False, "error": "Prospect not found"}
        
        # Analyze response sentiment
        analysis = TextBlob(response_text)
        sentiment = analysis.sentiment.polarity
        
        # Update message log
        message_log.replied_at = datetime.now(timezone.utc)
        message_log.status = MessageStatus.REPLIED
        db.commit()
        
        # Determine follow-up action
        follow_up_template_id = None
        if sentiment > 0.3:
            prospect.status = ProspectStatus.INTERESTED
            follow_up_template_id = settings.POSITIVE_RESPONSE_TEMPLATE_ID
            logger.info(f"Positive response detected for prospect {prospect.id}")
        elif sentiment < -0.3:
            prospect.status = ProspectStatus.DECLINED
            follow_up_template_id = settings.NEGATIVE_RESPONSE_TEMPLATE_ID
            logger.info(f"Negative response detected for prospect {prospect.id}")
        else:
            follow_up_template_id = settings.NEUTRAL_RESPONSE_TEMPLATE_ID
            logger.info(f"Neutral response detected for prospect {prospect.id}")
        
        db.commit()
        
        if follow_up_template_id:
            template = db.query(MessageTemplate).filter(
                MessageTemplate.id == follow_up_template_id
            ).first()
            if not template:
                logger.error(f"Follow-up template {follow_up_template_id} not found")
                return {"success": False, "error": "Follow-up template not found"}
            
            prospect_data = {
                'first_name': prospect.first_name,
                'last_name': prospect.last_name,
                'company': prospect.company,
                'website': prospect.website,
                'email': prospect.email
            }
            
            personalized_content = email_service.personalize_message(
                template.content, prospect_data
            )
            personalized_subject = email_service.personalize_message(
                template.subject or "Follow-up: Partnership Opportunity", prospect_data
            )
            
            success = email_service.send_email(
                prospect.email,
                personalized_subject,
                personalized_content
            )
            
            follow_up_log = MessageLog(
                id=uuid4(),
                prospect_id=prospect.id,
                campaign_id=message_log.campaign_id,
                template_id=uuid4(follow_up_template_id),
                message_type=MessageType.EMAIL,
                subject=personalized_subject,
                content=personalized_content,
                sent_at=datetime.now(timezone.utc),
                status=MessageStatus.SENT if success else MessageStatus.BOUNCED
            )
            
            db.add(follow_up_log)
            db.commit()
            logger.info(f"Follow-up sent to prospect {prospect.id}, success: {success}")
            
            return {"success": success, "follow_up_message_id": str(follow_up_log.id)}
        
        return {"success": True, "message": "Response processed, no follow-up needed"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling response for message {message_log_id}: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()