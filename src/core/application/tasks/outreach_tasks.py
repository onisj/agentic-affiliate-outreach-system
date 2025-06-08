from services.email_service import EmailService
from services.social_service import SocialService
from database.models import AffiliateProspect, MessageTemplate, MessageLog, MessageStatus, MessageType, OutreachCampaign, CampaignStatus
from database.models import ABTest, ABTestResult
from sqlalchemy.orm import Session
from database.session import get_db
from celery import shared_task
from typing import Dict, Any
from uuid import UUID
from datetime import datetime
import pytz
from uuid import uuid4
import logging
import random
from app.tasks.sequence_tasks import update_ab_test_metrics
from services.outreach import OutreachService


logger = logging.getLogger(__name__)

@shared_task
def send_outreach_message(prospect_id: str, template_id: str, message_type: str) -> Dict[str, Any]:
    try:
        message_type = message_type.upper()
        if message_type not in ["EMAIL", "TWITTER", "LINKEDIN"]:
            return {"success": False, "error": f"Invalid message type: {message_type}"}

        db: Session = next(get_db())
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == UUID(prospect_id)).first()
        if not prospect:
            return {"success": False, "error": "Prospect not found"}

        if not prospect.consent_given:
            return {"success": False, "error": "Consent not given"}

        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == UUID(template_id),
            MessageTemplate.message_type == MessageType[message_type],
            MessageTemplate.is_active == True
        ).first()
        if not template:
            return {"success": False, "error": "Template not found or invalid for message type"}

        prospect_data = {
            "first_name": prospect.first_name or "",
            "last_name": prospect.last_name or "",
            "company": prospect.company or "",
            "email": prospect.email
        }

        if message_type == "EMAIL":
            email_service = EmailService()
            personalized_content = email_service.personalize_message(template.content, prospect_data)
            subject = template.subject or "Affiliate Program Outreach"
            success = email_service.send_email(prospect.email, subject, personalized_content)
            if not success:
                return {"success": False, "error": "Failed to send email"}
            message_content = personalized_content
            message_subject = subject
        elif message_type == "TWITTER":
            twitter_id = prospect.social_profiles.get("twitter", {}).get("user_id")
            if not twitter_id:
                return {"success": False, "error": "Twitter user ID not found"}
            social_service = SocialService()
            result = social_service.send_twitter_dm(prospect_id, twitter_id, template.content, prospect_data, db)
            if not result["success"]:
                return {"success": False, "error": result["error"]}
            message_content = template.content
            message_subject = None
        elif message_type == "LINKEDIN":
            linkedin_urn = prospect.social_profiles.get("linkedin", {}).get("urn")
            if not linkedin_urn:
                return {"success": False, "error": "LinkedIn URN not found"}
            social_service = SocialService()
            result = social_service.send_linkedin_message(prospect_id, linkedin_urn, template.content, prospect_data, db)
            if not result["success"]:
                return {"success": False, "error": result["error"]}
            message_content = template.content
            message_subject = None

        # Log the message
        message_log = MessageLog(
            id=UUID(str(uuid4())),
            prospect_id=UUID(prospect_id),
            template_id=UUID(template_id),
            message_type=MessageType[message_type],
            subject=message_subject,
            content=message_content,
            status=MessageStatus.SENT,
            sent_at=datetime.now(pytz.UTC)
        )
        db.add(message_log)
        db.commit()

        return {"success": True, "message_id": str(message_log.id)}

    except Exception as e:
        logger.error(f"Error in send_outreach_message: {str(e)}")
        return {"success": False, "error": str(e)}
    
    

@shared_task
def send_ab_test_message(prospect_id: str, campaign_id: str, ab_test_id: str) -> Dict[str, Any]:
    """Send an A/B test message to a prospect for a specific campaign and A/B test."""
    db: Session = next(get_db())
    email_service = EmailService()
    social_service = SocialService()
    
    try:
        # Validate inputs
        try:
            prospect_uuid = UUID(prospect_id)
            campaign_uuid = UUID(campaign_id)
            ab_test_uuid = UUID(ab_test_id)
        except ValueError:
            logger.error("Invalid UUID format for prospect_id, campaign_id, or ab_test_id")
            return {"success": False, "error": "Invalid UUID format"}

        # Fetch prospect
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_uuid).first()
        if not prospect:
            logger.error(f"Prospect {prospect_id} not found")
            return {"success": False, "error": "Prospect not found"}
        if not prospect.consent_given:
            logger.error(f"Prospect {prospect_id} has not given consent")
            return {"success": False, "error": "Consent not given"}

        # Fetch campaign
        campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_uuid).first()
        if not campaign or campaign.status != CampaignStatus.ACTIVE:
            logger.error(f"Campaign {campaign_id} not found or not active")
            return {"success": False, "error": "Campaign not found or not active"}

        # Fetch A/B test
        ab_test = db.query(ABTest).filter(ABTest.id == ab_test_uuid, ABTest.campaign_id == campaign_uuid).first()
        if not ab_test:
            logger.error(f"A/B test {ab_test_id} not found for campaign {campaign_id}")
            return {"success": False, "error": "A/B test not found"}

        # Select random variant
        variant = random.choice(ab_test.variants)
        template_id = variant["template_id"]
        variant_id = variant["variant_id"]

        # Fetch template
        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == UUID(template_id),
            MessageTemplate.is_active == True
        ).first()
        if not template:
            logger.error(f"Template {template_id} not found or inactive")
            return {"success": False, "error": "Template not found or inactive"}

        # Prepare prospect data
        prospect_data = {
            "first_name": prospect.first_name or "",
            "last_name": prospect.last_name or "",
            "company": prospect.company or "",
            "email": prospect.email,
            "website": prospect.website or ""
        }

        # Send message based on template type
        message_content = None
        message_subject = None
        success = False

        if template.message_type == MessageType.EMAIL:
            message_content = email_service.personalize_message(template.content, prospect_data)
            message_subject = email_service.personalize_message(
                template.subject or "Affiliate Program Outreach", prospect_data
            )
            success = email_service.send_email(prospect.email, message_subject, message_content)
        elif template.message_type == MessageType.TWITTER:
            twitter_id = prospect.social_profiles.get("twitter", {}).get("user_id")
            if not twitter_id:
                logger.error(f"Twitter user ID not found for prospect {prospect_id}")
                return {"success": False, "error": "Twitter user ID not found"}
            result = social_service.send_twitter_dm(prospect_id, twitter_id, template.content, prospect_data, db=db)
            success = result["success"]
            message_content = template.content
            if not success:
                logger.error(f"Twitter DM failed: {result['error']}")
                return result
        elif template.message_type == MessageType.LINKEDIN:
            linkedin_urn = prospect.social_profiles.get("linkedin", {}).get("urn")
            if not linkedin_urn:
                logger.error(f"LinkedIn URN not found for prospect {prospect_id}")
                return {"success": False, "error": "LinkedIn URN not found"}
            result = social_service.send_linkedin_message(prospect_id, linkedin_urn, template.content, prospect_data, db=db)
            success = result["success"]
            message_content = template.content
            if not success:
                logger.error(f"LinkedIn message failed: {result['error']}")
                return result

        # Log the message
        message_log = MessageLog(
            id=UUID(str(uuid4())),
            prospect_id=prospect_uuid,
            campaign_id=campaign_uuid,
            template_id=UUID(template_id),
            message_type=template.message_type,
            subject=message_subject,
            content=message_content,
            status=MessageStatus.SENT if success else MessageStatus.BOUNCED,
            sent_at=datetime.now(pytz.UTC),
            ab_test_variant=variant_id
        )
        db.add(message_log)

        # Update A/B test results
        result = db.query(ABTestResult).filter(
            ABTestResult.ab_test_id == ab_test_uuid,
            ABTestResult.variant_id == variant_id
        ).first()
        if not result:
            result = ABTestResult(
                id=uuid4(),
                ab_test_id=ab_test_uuid,
                variant_id=variant_id,
                sent_count=0,
                open_rate=0.0,
                click_rate=0.0,
                reply_rate=0.0,
                updated_at=datetime.now(pytz.UTC)
            )
            db.add(result)
        result.sent_count += 1
        db.commit()

        # Trigger metrics update
        update_ab_test_metrics.delay(str(ab_test_uuid), variant_id)

        logger.info(f"A/B test message sent to prospect {prospect_id} for campaign {campaign_id}, variant {variant_id}")
        return {"success": success, "message_id": str(message_log.id)}

    except Exception as e:
        db.rollback()
        logger.error(f"Error sending A/B test message for prospect {prospect_id}: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def send_outreach_message(message: str):
    outreach_service = OutreachService()
    outreach_service.send_outreach(message)