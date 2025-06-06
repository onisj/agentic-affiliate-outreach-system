"""
Unified service for handling message responses and tracking.
Handles:
- Response tracking and analysis
- Automated response handling
- Sentiment analysis
- A/B test result tracking
- Response analytics and reporting
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import (
    MessageLog,
    ABTest, ABTestResult,
    AffiliateProspect, OutreachCampaign, MessageTemplate,
    MessageStatus, MessageResponse
)
from app.services.webhook_service import WebhookService
from app.services.email_service import EmailService
from app.services.social_service import SocialService
from textblob import TextBlob
import json
import asyncio
from pydantic import BaseModel, ConfigDict
from app.services.response_tracking import ResponseTrackingService

logger = logging.getLogger(__name__)

class ResponseConfig(BaseModel):
    """Configuration for response handling."""
    enable_auto_reply: bool = True
    auto_reply_delay: int = 300  # 5 minutes
    sentiment_threshold: float = 0.2
    max_retries: int = 3
    webhook_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ResponseService:
    """Service for handling message responses and tracking."""
    
    def __init__(
        self,
        db: Session,
        webhook_service: WebhookService,
        email_service: EmailService,
        social_service: SocialService,
        config: Optional[ResponseConfig] = None
    ):
        self.db = db
        self.webhook_service = webhook_service
        self.email_service = email_service
        self.social_service = social_service
        self.config = config or ResponseConfig()
    
    async def track_message_open(
        self,
        message_id: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track when a message is opened."""
        try:
            message = self.db.query(MessageLog).filter(MessageLog.id == message_id).first()
            if not message:
                logger.error(f"Message {message_id} not found")
                return
            
            # Update message status
            message.status = "opened"
            message.opened_at = datetime.now(timezone.utc)
            message.open_metadata = metadata or {}
            
            # Create response record
            response = MessageResponse(
                message_id=message_id,
                response_type="open",
                platform=platform,
                metadata=metadata or {},
                timestamp=datetime.now(timezone.utc)
            )
            self.db.add(response)
            self.db.commit()
            
            # Trigger webhook
            if self.config.webhook_url:
                await self.webhook_service.trigger_webhook(
                    event_type="message_opened",
                    payload={
                        "message_id": message_id,
                        "platform": platform,
                        "metadata": metadata,
                        "timestamp": response.timestamp.isoformat()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error tracking message open: {e}")
            self.db.rollback()
    
    async def track_message_click(
        self,
        message_id: str,
        platform: str,
        link_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track when a message link is clicked."""
        try:
            message = self.db.query(MessageLog).filter(MessageLog.id == message_id).first()
            if not message:
                logger.error(f"Message {message_id} not found")
                return
            
            # Update message status
            message.status = "clicked"
            message.clicked_at = datetime.now(timezone.utc)
            message.click_metadata = {
                "link_url": link_url,
                **(metadata or {})
            }
            
            # Create response record
            response = MessageResponse(
                message_id=message_id,
                response_type="click",
                platform=platform,
                metadata={
                    "link_url": link_url,
                    **(metadata or {})
                },
                timestamp=datetime.now(timezone.utc)
            )
            self.db.add(response)
            self.db.commit()
            
            # Trigger webhook
            if self.config.webhook_url:
                await self.webhook_service.trigger_webhook(
                    event_type="message_clicked",
                    payload={
                        "message_id": message_id,
                        "platform": platform,
                        "link_url": link_url,
                        "metadata": metadata,
                        "timestamp": response.timestamp.isoformat()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error tracking message click: {e}")
            self.db.rollback()
    
    async def track_message_reply(
        self,
        message_id: str,
        platform: str,
        reply_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track and analyze a reply to a message."""
        try:
            message = self.db.query(MessageLog).filter(MessageLog.id == message_id).first()
            if not message:
                logger.error(f"Message {message_id} not found")
                return
            
            # Analyze sentiment
            sentiment = TextBlob(reply_text).sentiment.polarity
            
            # Update message status
            message.status = "replied"
            message.replied_at = datetime.now(timezone.utc)
            message.reply_metadata = {
                "reply_text": reply_text,
                "sentiment": sentiment,
                **(metadata or {})
            }
            
            # Create response record
            response = MessageResponse(
                message_id=message_id,
                response_type="reply",
                platform=platform,
                metadata={
                    "reply_text": reply_text,
                    "sentiment": sentiment,
                    **(metadata or {})
                },
                timestamp=datetime.now(timezone.utc)
            )
            self.db.add(response)
            
            # Update prospect status based on sentiment
            prospect = self.db.query(AffiliateProspect).filter(AffiliateProspect.id == message.prospect_id).first()
            if prospect:
                if sentiment > self.config.sentiment_threshold:
                    prospect.status = "interested"
                elif sentiment < -self.config.sentiment_threshold:
                    prospect.status = "not_interested"
                else:
                    prospect.status = "neutral"
            
            self.db.commit()
            
            # Update A/B test results
            await self._update_ab_test_results(message, response)
            
            # Handle automated response if enabled
            if self.config.enable_auto_reply:
                await self._handle_automated_response(message, response)
            
            # Trigger webhook
            if self.config.webhook_url:
                await self.webhook_service.trigger_webhook(
                    event_type="message_replied",
                    payload={
                        "message_id": message_id,
                        "platform": platform,
                        "reply_text": reply_text,
                        "sentiment": sentiment,
                        "metadata": metadata,
                        "timestamp": response.timestamp.isoformat()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error tracking message reply: {e}")
            self.db.rollback()
    
    async def _update_ab_test_results(self, message: MessageLog, response: MessageResponse) -> None:
        """Update A/B test results based on message response."""
        try:
            # Get the A/B test for this message
            ab_test = self.db.query(ABTest).filter(
                ABTest.campaign_id == message.campaign_id,
                ABTest.status == "active"
            ).first()
            
            if not ab_test:
                return
            
            # Get the template variant used
            template = self.db.query(MessageTemplate).filter(
                MessageTemplate.id == message.template_id
            ).first()
            
            if not template:
                return
            
            # Create or update test result
            result = self.db.query(ABTestResult).filter(
                ABTestResult.test_id == ab_test.id,
                ABTestResult.template_id == template.id
            ).first()
            
            if not result:
                result = ABTestResult(
                    test_id=ab_test.id,
                    template_id=template.id,
                    responses=0,
                    opens=0,
                    clicks=0,
                    replies=0,
                    positive_replies=0,
                    negative_replies=0
                )
                self.db.add(result)
            
            # Update metrics
            if response.response_type == "open":
                result.opens += 1
            elif response.response_type == "click":
                result.clicks += 1
            elif response.response_type == "reply":
                result.replies += 1
                sentiment = response.metadata.get("sentiment", 0)
                if sentiment > self.config.sentiment_threshold:
                    result.positive_replies += 1
                elif sentiment < -self.config.sentiment_threshold:
                    result.negative_replies += 1
            
            result.responses += 1
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating A/B test results: {e}")
            self.db.rollback()
    
    async def _handle_automated_response(
        self,
        message: MessageLog,
        response: MessageResponse
    ) -> None:
        """Handle automated response to a message reply."""
        try:
            # Extract questions from the reply
            questions = self._extract_questions(response.metadata.get("reply_text", ""))
            
            if not questions:
                return
            
            # Get campaign and template
            campaign = self.db.query(OutreachCampaign).filter(
                OutreachCampaign.id == message.campaign_id
            ).first()
            
            if not campaign:
                return
            
            # Wait for configured delay
            await asyncio.sleep(self.config.auto_reply_delay)
            
            # Send automated response based on platform
            if message.platform == "email":
                await self.email_service.send_email(
                    to_email=message.recipient,
                    subject=f"Re: {message.subject}",
                    body=self._generate_response_body(questions, campaign),
                    reply_to=message.id
                )
            elif message.platform == "linkedin":
                await self.social_service.send_linkedin_message(
                    recipient_id=message.recipient,
                    message=self._generate_response_body(questions, campaign),
                    reply_to=message.id
                )
            elif message.platform == "twitter":
                await self.social_service.send_twitter_dm(
                    recipient_id=message.recipient,
                    message=self._generate_response_body(questions, campaign),
                    reply_to=message.id
                )
            
        except Exception as e:
            logger.error(f"Error handling automated response: {e}")
    
    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from text."""
        # Simple question extraction - can be enhanced with NLP
        sentences = text.split(".")
        return [
            s.strip() + "?"
            for s in sentences
            if "?" in s or s.strip().lower().startswith(("what", "how", "why", "when", "where", "who"))
        ]
    
    def _generate_response_body(self, questions: List[str], campaign: OutreachCampaign) -> str:
        """Generate response body based on questions and campaign context."""
        # TODO: Implement more sophisticated response generation
        return f"Thank you for your interest in {campaign.name}. I'll be happy to answer your questions:\n\n" + "\n".join(questions)
    
    async def get_response_analytics(
        self,
        campaign_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for message responses."""
        try:
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            
            # Get response metrics
            response_metrics = self.db.query(
                MessageResponse.response_type,
                func.count().label('count'),
                func.avg(MessageResponse.metadata['sentiment'].astext.cast(float)).label('avg_sentiment')
            ).join(
                MessageLog, MessageResponse.message_id == MessageLog.id
            ).filter(
                MessageLog.campaign_id == campaign_id,
                MessageResponse.timestamp.between(start_time, end_time)
            ).group_by(MessageResponse.response_type).all()
            
            # Get response time metrics
            response_times = self.db.query(
                func.avg(
                    func.extract('epoch', MessageResponse.timestamp - MessageLog.sent_at)
                ).label('avg_response_time')
            ).join(
                MessageLog, MessageResponse.message_id == MessageLog.id
            ).filter(
                MessageLog.campaign_id == campaign_id,
                MessageResponse.response_type == 'reply',
                MessageResponse.timestamp.between(start_time, end_time)
            ).first()
            
            return {
                'response_metrics': [
                    {
                        'type': m.response_type,
                        'count': m.count,
                        'avg_sentiment': float(m.avg_sentiment) if m.avg_sentiment else 0.0
                    }
                    for m in response_metrics
                ],
                'response_time': {
                    'avg_seconds': float(response_times.avg_response_time) if response_times.avg_response_time else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting response analytics: {e}")
            return {}
    
    async def get_sentiment_distribution(
        self,
        campaign_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get distribution of response sentiments."""
        try:
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            
            # Get sentiment distribution
            sentiments = self.db.query(
                case(
                    (MessageResponse.metadata['sentiment'].astext.cast(float) > self.config.sentiment_threshold, 'positive'),
                    (MessageResponse.metadata['sentiment'].astext.cast(float) < -self.config.sentiment_threshold, 'negative'),
                    else_='neutral'
                ).label('sentiment'),
                func.count().label('count')
            ).join(
                MessageLog, MessageResponse.message_id == MessageLog.id
            ).filter(
                MessageLog.campaign_id == campaign_id,
                MessageResponse.response_type == 'reply',
                MessageResponse.timestamp.between(start_time, end_time)
            ).group_by('sentiment').all()
            
            return {
                s.sentiment: s.count
                for s in sentiments
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment distribution: {e}")
            return {}

# Merge basic ResponseTrackingService into response_service.py
class ResponseTrackingService:
    def __init__(self, db):
        self.db = db

    def track_response(self, message_id: str, response_type: str, content: str) -> bool:
        try:
            message = self.db.query(MessageLog).filter(MessageLog.id == message_id).first()
            if not message:
                return False

            message.status = MessageStatus.RESPONDED
            message.response_type = response_type
            message.response_content = content
            message.response_timestamp = datetime.now(pytz.UTC)

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

    def get_message_responses(self, prospect_id: str) -> list:
        try:
            messages = self.db.query(MessageLog).filter(
                MessageLog.prospect_id == prospect_id,
                MessageLog.status == MessageStatus.RESPONDED
            ).all()

            return [
                {
                    'message_id': msg.id,
                    'type': msg.message_type,
                    'content': msg.response_content,
                    'timestamp': msg.response_timestamp
                }
                for msg in messages
            ]

        except Exception as e:
            raise e 