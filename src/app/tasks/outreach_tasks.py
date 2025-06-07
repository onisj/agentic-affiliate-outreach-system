from typing import Dict, List
import logging
from celery import shared_task
from sqlalchemy.orm import Session
from database.session import SessionLocal
from services.outreach.outreach import OutreachService
from services.outreach.email import EmailService
from services.outreach.social import SocialMediaService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name='send_outreach_email')
def send_outreach_email(prospect_id: str, template_id: str, custom_data: Dict = None) -> Dict:
    """
    Send an outreach email asynchronously.
    
    Args:
        prospect_id: ID of the prospect to email
        template_id: ID of the email template to use
        custom_data: Optional custom data for template
        
    Returns:
        Dictionary containing email sending results
    """
    try:
        db = SessionLocal()
        outreach_service = OutreachService(db)
        email_service = EmailService()
        
        # Get prospect
        prospect = outreach_service.get_prospect(prospect_id)
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")
        
        # Send email
        result = email_service.send_email(
            to_email=prospect.email,
            template_id=template_id,
            custom_data=custom_data or {}
        )
        
        # Log outreach
        outreach_service.log_outreach(
            prospect_id=prospect_id,
            channel='email',
            status='sent' if result['success'] else 'failed',
            details=result
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending outreach email to prospect {prospect_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='send_social_outreach')
def send_social_outreach(prospect_id: str, platform: str, message: str) -> Dict:
    """
    Send a social media outreach message asynchronously.
    
    Args:
        prospect_id: ID of the prospect to message
        platform: Social media platform to use
        message: Message to send
        
    Returns:
        Dictionary containing social media sending results
    """
    try:
        db = SessionLocal()
        outreach_service = OutreachService(db)
        social_service = SocialMediaService()
        
        # Get prospect
        prospect = outreach_service.get_prospect(prospect_id)
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")
        
        # Send social media message
        result = social_service.send_message(
            platform=platform,
            recipient=prospect.social_handles.get(platform),
            message=message
        )
        
        # Log outreach
        outreach_service.log_outreach(
            prospect_id=prospect_id,
            channel=platform,
            status='sent' if result['success'] else 'failed',
            details=result
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending social outreach to prospect {prospect_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='schedule_follow_up')
def schedule_follow_up(prospect_id: str, follow_up_type: str, delay_days: int) -> Dict:
    """
    Schedule a follow-up outreach asynchronously.
    
    Args:
        prospect_id: ID of the prospect to follow up with
        follow_up_type: Type of follow-up (email, social, etc.)
        delay_days: Number of days to wait before following up
        
    Returns:
        Dictionary containing scheduling results
    """
    try:
        db = SessionLocal()
        outreach_service = OutreachService(db)
        
        # Schedule follow-up
        result = outreach_service.schedule_follow_up(
            prospect_id=prospect_id,
            follow_up_type=follow_up_type,
            delay_days=delay_days
        )
        
        return result
    except Exception as e:
        logger.error(f"Error scheduling follow-up for prospect {prospect_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='process_outreach_queue')
def process_outreach_queue() -> Dict:
    """
    Process the outreach queue asynchronously.
    
    Returns:
        Dictionary containing queue processing results
    """
    try:
        db = SessionLocal()
        outreach_service = OutreachService(db)
        
        # Process queue
        result = outreach_service.process_queue()
        
        return result
    except Exception as e:
        logger.error(f"Error processing outreach queue: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='batch_send_outreach')
def batch_send_outreach(outreach_items: List[Dict]) -> List[Dict]:
    """
    Send multiple outreach messages asynchronously.
    
    Args:
        outreach_items: List of dictionaries containing outreach details
        
    Returns:
        List of dictionaries containing sending results
    """
    try:
        db = SessionLocal()
        outreach_service = OutreachService(db)
        email_service = EmailService()
        social_service = SocialMediaService()
        
        results = []
        for item in outreach_items:
            try:
                if item['channel'] == 'email':
                    result = email_service.send_email(
                        to_email=item['email'],
                        template_id=item['template_id'],
                        custom_data=item.get('custom_data', {})
                    )
                else:
                    result = social_service.send_message(
                        platform=item['channel'],
                        recipient=item['recipient'],
                        message=item['message']
                    )
                
                # Log outreach
                outreach_service.log_outreach(
                    prospect_id=item['prospect_id'],
                    channel=item['channel'],
                    status='sent' if result['success'] else 'failed',
                    details=result
                )
                
                results.append({
                    'prospect_id': item['prospect_id'],
                    'channel': item['channel'],
                    'result': result,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error sending outreach to prospect {item['prospect_id']}: {str(e)}")
                results.append({
                    'prospect_id': item['prospect_id'],
                    'channel': item['channel'],
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    except Exception as e:
        logger.error(f"Error in batch outreach: {str(e)}")
        raise
    finally:
        db.close() 