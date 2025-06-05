from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import (
    OutreachCampaign,
    MessageTemplate,
    MessageLog,
    MessageType,
    MessageStatus,
    CampaignStatus
)
from services.email import EmailService
from services.linkedin import LinkedInService
from services.twitter import TwitterService
import asyncio
from jinja2 import Template

logger = logging.getLogger(__name__)

class OutreachService:
    """Service for managing multi-channel outreach campaigns."""
    
    def __init__(self, db: Session):
        self.db = db
        self.channels = {
            MessageType.EMAIL: EmailService(),
            MessageType.LINKEDIN: LinkedInService(),
            MessageType.TWITTER: TwitterService()
        }
    
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
        # TODO: Implement affiliate targeting logic
        return []
    
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
    
    async def close(self):
        """Close all channel connections."""
        for channel in self.channels.values():
            await channel.close() 