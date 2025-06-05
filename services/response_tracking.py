from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database.models import (
    MessageLog, MessageStatus, MessageType,
    AffiliateProspect, ProspectStatus,
    ABTest, ABTestResult, WebhookEventType
)
from textblob import TextBlob
import re
from uuid import UUID
from services.webhook_service import WebhookService

logger = logging.getLogger(__name__)

class ResponseTrackingService:
    """Service for tracking and analyzing message responses."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_service = WebhookService(db)
    
    async def track_message_open(
        self,
        message_id: str,
        external_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track when a message is opened."""
        try:
            message = self.db.query(MessageLog).filter(
                MessageLog.id == message_id
            ).first()
            
            if not message:
                return {"success": False, "error": "Message not found"}
            
            message.status = MessageStatus.OPENED
            message.opened_at = datetime.now(timezone.utc)
            
            if external_message_id:
                message.external_message_id = external_message_id
            
            self.db.commit()
            
            # Trigger webhook
            await self.webhook_service.trigger_webhook(
                event_type=WebhookEventType.MESSAGE_OPENED,
                payload={
                    "message_id": str(message.id),
                    "prospect_id": str(message.prospect_id),
                    "campaign_id": str(message.campaign_id) if message.campaign_id else None,
                    "opened_at": message.opened_at.isoformat(),
                    "external_message_id": message.external_message_id
                }
            )
            
            return {"success": True, "message": "Open tracked successfully"}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking message open: {e}")
            return {"success": False, "error": str(e)}
    
    async def track_message_click(
        self,
        message_id: str,
        click_url: str
    ) -> Dict[str, Any]:
        """Track when a message link is clicked."""
        try:
            message = self.db.query(MessageLog).filter(
                MessageLog.id == message_id
            ).first()
            
            if not message:
                return {"success": False, "error": "Message not found"}
            
            message.status = MessageStatus.CLICKED
            message.clicked_at = datetime.now(timezone.utc)
            
            # Store click data in message metadata
            if not message.message_metadata:
                message.message_metadata = {}
            if "clicks" not in message.message_metadata:
                message.message_metadata["clicks"] = []
            message.message_metadata["clicks"].append({
                "url": click_url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.db.commit()
            
            # Trigger webhook
            await self.webhook_service.trigger_webhook(
                event_type=WebhookEventType.MESSAGE_CLICKED,
                payload={
                    "message_id": str(message.id),
                    "prospect_id": str(message.prospect_id),
                    "campaign_id": str(message.campaign_id) if message.campaign_id else None,
                    "clicked_at": message.clicked_at.isoformat(),
                    "click_url": click_url
                }
            )
            
            return {"success": True, "message": "Click tracked successfully"}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking message click: {e}")
            return {"success": False, "error": str(e)}
    
    async def track_message_reply(
        self,
        message_id: str,
        reply_content: str,
        external_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track and analyze a message reply."""
        try:
            message = self.db.query(MessageLog).filter(
                MessageLog.id == message_id
            ).first()
            
            if not message:
                return {"success": False, "error": "Message not found"}
            
            # Update message status
            message.status = MessageStatus.REPLIED
            message.replied_at = datetime.now(timezone.utc)
            
            if external_message_id:
                message.external_message_id = external_message_id
            
            # Analyze reply content
            analysis = TextBlob(reply_content)
            sentiment = analysis.sentiment.polarity
            
            # Extract key information
            is_positive = sentiment > 0.3
            is_negative = sentiment < -0.3
            contains_questions = bool(re.search(r'\?', reply_content))
            contains_contact = bool(re.search(r'email|phone|contact', reply_content.lower()))
            
            # Update prospect status based on reply
            prospect = message.prospect
            old_status = prospect.status
            if is_positive:
                prospect.status = ProspectStatus.INTERESTED
            elif is_negative:
                prospect.status = ProspectStatus.DECLINED
            else:
                prospect.status = ProspectStatus.ENGAGED
            
            # Store reply analysis in message metadata
            if not message.message_metadata:
                message.message_metadata = {}
            message.message_metadata["reply_analysis"] = {
                "sentiment": sentiment,
                "is_positive": is_positive,
                "is_negative": is_negative,
                "contains_questions": contains_questions,
                "contains_contact": contains_contact,
                "content": reply_content
            }
            
            # Update A/B test results if applicable
            if message.ab_test_variant:
                await self._update_ab_test_results(message)
            
            self.db.commit()
            
            # Trigger webhooks
            await self.webhook_service.trigger_webhook(
                event_type=WebhookEventType.MESSAGE_REPLIED,
                payload={
                    "message_id": str(message.id),
                    "prospect_id": str(message.prospect_id),
                    "campaign_id": str(message.campaign_id) if message.campaign_id else None,
                    "replied_at": message.replied_at.isoformat(),
                    "reply_analysis": message.message_metadata["reply_analysis"]
                }
            )
            
            # Trigger prospect status change webhook if status changed
            if old_status != prospect.status:
                await self.webhook_service.trigger_webhook(
                    event_type=WebhookEventType.PROSPECT_STATUS_CHANGED,
                    payload={
                        "prospect_id": str(prospect.id),
                        "old_status": old_status,
                        "new_status": prospect.status,
                        "changed_at": datetime.now(timezone.utc).isoformat(),
                        "triggered_by": "message_reply"
                    }
                )
            
            return {
                "success": True,
                "message": "Reply tracked successfully",
                "analysis": message.message_metadata["reply_analysis"]
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking message reply: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_ab_test_results(self, message: MessageLog) -> None:
        """Update A/B test results based on message response."""
        try:
            result = self.db.query(ABTestResult).filter(
                ABTestResult.ab_test_id == message.campaign.ab_test_id,
                ABTestResult.variant_id == message.ab_test_variant
            ).first()
            
            if not result:
                return
            
            # Update engagement metrics
            result.reply_rate = (
                self.db.query(func.count(MessageLog.id))
                .filter(
                    MessageLog.campaign_id == message.campaign_id,
                    MessageLog.ab_test_variant == message.ab_test_variant,
                    MessageLog.status == MessageStatus.REPLIED
                ).scalar() * 100.0 /
                self.db.query(func.count(MessageLog.id))
                .filter(
                    MessageLog.campaign_id == message.campaign_id,
                    MessageLog.ab_test_variant == message.ab_test_variant
                ).scalar()
            )
            
            # Update positive response rate
            positive_responses = self.db.query(func.count(MessageLog.id)).filter(
                MessageLog.campaign_id == message.campaign_id,
                MessageLog.ab_test_variant == message.ab_test_variant,
                MessageLog.status == MessageStatus.REPLIED,
                MessageLog.message_metadata['reply_analysis']['is_positive'].astext == 'true'
            ).scalar()
            
            total_responses = self.db.query(func.count(MessageLog.id)).filter(
                MessageLog.campaign_id == message.campaign_id,
                MessageLog.ab_test_variant == message.ab_test_variant,
                MessageLog.status == MessageStatus.REPLIED
            ).scalar()
            
            if total_responses > 0:
                result.positive_response_rate = (positive_responses / total_responses) * 100
            
            result.updated_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error updating A/B test results: {e}")
            raise
    
    async def get_response_analytics(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive response analytics."""
        try:
            query = self.db.query(MessageLog)
            
            if campaign_id:
                query = query.filter(MessageLog.campaign_id == campaign_id)
            if start_date:
                query = query.filter(MessageLog.sent_at >= start_date)
            if end_date:
                query = query.filter(MessageLog.sent_at <= end_date)
            
            # Get basic metrics
            total_messages = query.count()
            opened_messages = query.filter(MessageLog.status == MessageStatus.OPENED).count()
            clicked_messages = query.filter(MessageLog.status == MessageStatus.CLICKED).count()
            replied_messages = query.filter(MessageLog.status == MessageStatus.REPLIED).count()
            
            # Get sentiment analysis
            positive_responses = query.filter(
                MessageLog.status == MessageStatus.REPLIED,
                MessageLog.message_metadata['reply_analysis']['is_positive'].astext == 'true'
            ).count()
            
            negative_responses = query.filter(
                MessageLog.status == MessageStatus.REPLIED,
                MessageLog.message_metadata['reply_analysis']['is_negative'].astext == 'true'
            ).count()
            
            # Calculate rates
            open_rate = (opened_messages / total_messages * 100) if total_messages > 0 else 0
            click_rate = (clicked_messages / total_messages * 100) if total_messages > 0 else 0
            reply_rate = (replied_messages / total_messages * 100) if total_messages > 0 else 0
            positive_rate = (positive_responses / replied_messages * 100) if replied_messages > 0 else 0
            
            # Get response time metrics
            response_times = query.filter(
                MessageLog.status == MessageStatus.REPLIED,
                MessageLog.replied_at.isnot(None),
                MessageLog.sent_at.isnot(None)
            ).with_entities(
                func.extract('epoch', MessageLog.replied_at - MessageLog.sent_at)
            ).all()
            
            avg_response_time = sum(t[0] for t in response_times) / len(response_times) if response_times else 0
            
            return {
                "total_messages": total_messages,
                "opens": opened_messages,
                "clicks": clicked_messages,
                "replies": replied_messages,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "reply_rate": reply_rate,
                "positive_responses": positive_responses,
                "negative_responses": negative_responses,
                "positive_rate": positive_rate,
                "avg_response_time": avg_response_time,
                "response_time_breakdown": {
                    "under_1h": sum(1 for t in response_times if t[0] < 3600),
                    "under_24h": sum(1 for t in response_times if t[0] < 86400),
                    "over_24h": sum(1 for t in response_times if t[0] >= 86400)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting response analytics: {e}")
            return {"success": False, "error": str(e)} 