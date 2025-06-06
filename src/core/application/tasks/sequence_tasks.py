from app.tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from database.models import Sequence, MessageLog, AffiliateProspect, MessageTemplate, MessageType, MessageStatus, ABTest, ABTestResult
from database.session import get_db
from app.services.email_service import EmailService
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task
def process_sequence_step(prospect_id: str, campaign_id: str):
    """Process the next step in an email sequence for a prospect."""
    db = next(get_db())
    email_service = EmailService()
    
    try:
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
        if not prospect or not prospect.consent_given:
            logger.error(f"Prospect {prospect_id} not found or no consent")
            return {"success": False, "error": "Prospect not found or no consent"}
        
        # Find the last message sent for this campaign
        last_message = db.query(MessageLog).filter(
            MessageLog.prospect_id == prospect_id,
            MessageLog.campaign_id == campaign_id
        ).order_by(MessageLog.sent_at.desc()).first()
        
        last_step = last_message.step_number if last_message else 0
        
        # Get the next sequence step
        next_step = db.query(Sequence).filter(
            Sequence.campaign_id == campaign_id,
            Sequence.step_number == last_step + 1
        ).first()
        
        if not next_step:
            logger.info(f"No further steps for prospect {prospect_id} in campaign {campaign_id}")
            return {"success": True, "message": "No further steps"}
        
        # Check condition (e.g., no response)
        if next_step.condition.get("no_response"):
            if last_message and last_message.status == MessageStatus.REPLIED:
                logger.info(f"Prospect {prospect_id} responded, skipping step")
                return {"success": True, "message": "Prospect responded"}
        
        # Check delay
        if last_message:
            delay = timedelta(days=next_step.delay_days)
            if datetime.now(timezone.utc) < last_message.sent_at + delay:
                logger.info(f"Delay not met for prospect {prospect_id}")
                return {"success": True, "message": "Delay not met"}
        
        # Check for A/B test
        ab_test = db.query(ABTest).filter(ABTest.campaign_id == campaign_id).first()
        template_id = next_step.template_id
        variant_id = None
        
        if ab_test:
            variants = ab_test.variants
            variant = random.choice(variants)  # Randomly select variant
            template_id = variant["template_id"]
            variant_id = variant["variant_id"]
            
            # Update A/B test results
            result = db.query(ABTestResult).filter(
                ABTestResult.ab_test_id == ab_test.id,
                ABTestResult.variant_id == variant_id
            ).first()
            if not result:
                result = ABTestResult(
                    id=uuid4(),
                    ab_test_id=ab_test.id,
                    variant_id=variant_id,
                    sent_count=0,
                    open_rate=0.0,
                    click_rate=0.0,
                    reply_rate=0.0,
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(result)
            result.sent_count += 1
            db.commit()
        
        # Send message
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if not template:
            logger.error(f"Template {template_id} not found")
            return {"success": False, "error": "Template not found"}
        
        prospect_data = {
            "first_name": prospect.first_name,
            "last_name": prospect.last_name,
            "company": prospect.company,
            "website": prospect.website,
            "email": prospect.email
        }
        
        personalized_content = email_service.personalize_message(template.content, prospect_data)
        personalized_subject = email_service.personalize_message(
            template.subject or "Follow-up", prospect_data
        )
        
        success = email_service.send_email(
            prospect.email,
            personalized_subject,
            personalized_content
        )
        
        message_log = MessageLog(
            id=uuid4(),
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            template_id=template_id,
            message_type=MessageType.EMAIL,
            subject=personalized_subject,
            content=personalized_content,
            sent_at=datetime.now(timezone.utc),
            status=MessageStatus.SENT if success else MessageStatus.BOUNCED,
            step_number=next_step.step_number,
            ab_test_variant=variant_id
        )
        
        db.add(message_log)
        db.commit()
        
        # Update A/B test metrics
        if ab_test:
            update_ab_test_metrics(str(ab_test.id), variant_id)
        
        # Schedule next step if applicable
        next_next_step = db.query(Sequence).filter(
            Sequence.campaign_id == campaign_id,
            Sequence.step_number == next_step.step_number + 1
        ).first()
        
        if next_next_step:
            process_sequence_step.apply_async(
                args=[prospect_id, campaign_id],
                countdown=next_next_step.delay_days * 24 * 60 * 60
            )
        
        logger.info(f"Sequence step {next_step.step_number} sent to prospect {prospect_id}")
        return {"success": success, "message_id": str(message_log.id)}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing sequence for prospect {prospect_id}: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task
def update_ab_test_metrics(ab_test_id: str, variant_id: str):
    """Update A/B test metrics."""
    db = next(get_db())
    try:
        result = db.query(ABTestResult).filter(
            ABTestResult.ab_test_id == ab_test_id,
            ABTestResult.variant_id == variant_id
        ).first()
        
        if not result:
            return
        
        messages = db.query(MessageLog).filter(
            MessageLog.campaign_id == db.query(ABTest).filter(ABTest.id == ab_test_id).first().campaign_id,
            MessageLog.ab_test_variant == variant_id
        ).all()
        
        sent = result.sent_count
        opened = sum(1 for m in messages if m.status == MessageStatus.OPENED)
        clicked = sum(1 for m in messages if m.status == MessageStatus.CLICKED)
        replied = sum(1 for m in messages if m.status == MessageStatus.REPLIED)
        
        result.open_rate = (opened / sent * 100) if sent > 0 else 0.0
        result.click_rate = (clicked / sent * 100) if sent > 0 else 0.0
        result.reply_rate = (replied / sent * 100) if sent > 0 else 0.0
        result.updated_at = datetime.now(timezone.utc)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating A/B test metrics: {str(e)}")
    finally:
        db.close()