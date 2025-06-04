# services/social_service.py
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging
from jinja2 import Template
from sqlalchemy.orm import Session
import tweepy
from database.models import MessageLog, MessageType, MessageStatus
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialService:
    TWITTER_API_URL = "https://api.twitter.com/1.1"
    LINKEDIN_API_URL = "https://api.linkedin.com/v2"

    def __init__(self):
        self.twitter_bearer_token: Optional[str] = settings.TWITTER_BEARER_TOKEN
        self.linkedin_client_id: Optional[str] = settings.LINKEDIN_CLIENT_ID
        self.linkedin_client_secret: Optional[str] = settings.LINKEDIN_CLIENT_SECRET
        self.linkedin_redirect_url: str = settings.LINKEDIN_REDIRECT_URL
        self.twitter_client: Optional[tweepy.Client] = None
        if self.twitter_bearer_token:
            try:
                self.twitter_client = tweepy.Client(bearer_token=self.twitter_bearer_token)
                logger.info("Twitter client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client: {e}")

    def send_twitter_dm(
        self,
        prospect_id: str,
        user_id: str,
        template: str,
        prospect_data: Dict[str, Any],
        campaign_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Send a Twitter DM to a prospect and log the attempt in the database.

        Args:
            prospect_id: UUID string identifying the prospect.
            user_id: Twitter user ID of the recipient.
            template: Jinja2 template for the message content.
            prospect_data: Dictionary containing prospect details (e.g., first_name, company).
            campaign_id: Optional UUID string for the campaign.
            db: SQLAlchemy session for database operations.

        Returns:
            Dictionary with success status, message ID, and optional error message.
        """
        if not db:
            logger.error("Database session is required")
            return {"success": False, "error": "Database session is required"}
        if not self.twitter_client:
            logger.error("Twitter client not initialized")
            return {"success": False, "error": "Twitter client not initialized"}

        try:
            # Validate UUIDs
            try:
                uuid.UUID(prospect_id)
                if campaign_id:
                    uuid.UUID(campaign_id)
            except ValueError:
                logger.error("Invalid UUID format for prospect_id or campaign_id")
                return {"success": False, "error": "Invalid UUID format"}

            # Validate required inputs
            if not user_id.strip():
                logger.error("Twitter user_id is empty")
                return {"success": False, "error": "user_id is required"}
            if not template.strip():
                logger.error("Message template is empty")
                return {"success": False, "error": "template is required"}
            if not isinstance(prospect_data, dict):
                logger.error("prospect_data must be a dictionary")
                return {"success": False, "error": "prospect_data must be a dictionary"}

            # Personalize message
            template_obj = Template(template)
            context = {
                "first_name": prospect_data.get("first_name", "there").strip(),
                "company": prospect_data.get("company", "your company").strip(),
                "company_mention": f"I noticed you work at {prospect_data.get('company', 'your company').strip()}",
            }
            personalized_content = template_obj.render(**context)[:280]  # Twitter DM limit
            logger.debug(f"Personalized Twitter DM content: {personalized_content}")

            # Send Twitter DM
            response = self.twitter_client.create_direct_message(
                participant_id=user_id, text=personalized_content
            )
            success = bool(response.data)
            logger.info(f"Twitter DM sent to user {user_id}: {'success' if success else 'failed'}")

            # Log the message
            message_log = MessageLog(
                id=str(uuid.uuid4()),
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                message_type=MessageType.TWITTER.value,
                content=personalized_content,
                sent_at=datetime.now(timezone.utc),
                status=MessageStatus.SENT.value if success else MessageStatus.BOUNCED.value,
            )

            db.add(message_log)
            db.commit()
            logger.info(f"Message logged with ID {message_log.id}")

            return {"success": success, "message_id": message_log.id}

        except Exception as e:
            db.rollback()
            logger.error(f"Error sending Twitter DM: {e}")
            return {"success": False, "error": str(e)}

    def send_linkedin_message(
        self,
        prospect_id: str,
        urn: str,
        template: str,
        prospect_data: Dict[str, Any],
        campaign_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Placeholder for sending a LinkedIn message to a prospect.

        Note: This is a mock implementation pending OAuth 2.0 setup for LinkedIn API.

        Args:
            prospect_id: UUID string identifying the prospect.
            urn: LinkedIn URN of the recipient (e.g., urn:li:person:123).
            template: Jinja2 template for the message content.
            prospect_data: Dictionary containing prospect details (e.g., first_name, company).
            campaign_id: Optional UUID string for the campaign.
            db: SQLAlchemy session for database operations.

        Returns:
            Dictionary with success status (always False), message ID, and error message.
        """
        if not db:
            logger.error("Database session is required")
            return {"success": False, "error": "Database session is required"}
        if not all([self.linkedin_client_id, self.linkedin_client_secret]):
            logger.error("LinkedIn credentials not configured")
            return {"success": False, "error": "LinkedIn credentials not configured"}

        try:
            # Validate UUIDs
            try:
                uuid.UUID(prospect_id)
                if campaign_id:
                    uuid.UUID(campaign_id)
            except ValueError:
                logger.error("Invalid UUID format for prospect_id or campaign_id")
                return {"success": False, "error": "Invalid UUID format"}

            # Validate required inputs
            if not urn.strip():
                logger.error("LinkedIn URN is empty")
                return {"success": False, "error": "urn is required"}
            if not template.strip():
                logger.error("Message template is empty")
                return {"success": False, "error": "template is required"}
            if not isinstance(prospect_data, dict):
                logger.error("prospect_data must be a dictionary")
                return {"success": False, "error": "prospect_data must be a dictionary"}

            # Personalize message
            template_obj = Template(template)
            context = {
                "first_name": prospect_data.get("first_name", "there").strip(),
                "company": prospect_data.get("company", "your company").strip(),
                "company_mention": f"I noticed you work at {prospect_data.get('company', 'your company').strip()}",
            }
            personalized_content = template_obj.render(**context)[:1000]  # LinkedIn message limit
            logger.debug(f"Personalized LinkedIn message content: {personalized_content}")

            # Placeholder for LinkedIn messaging
            error_message = "LinkedIn messaging not implemented (requires OAuth access token)"
            logger.warning(error_message)
            success = False

            # Log the message
            message_log = MessageLog(
                id=str(uuid.uuid4()),
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                message_type=MessageType.LINKEDIN.value,
                content=personalized_content,
                sent_at=datetime.now(timezone.utc),
                status=MessageStatus.BOUNCED.value,
            )

            db.add(message_log)
            db.commit()
            logger.info(f"Message logged with ID {message_log.id}")

            return {"success": success, "message_id": message_log.id, "error": error_message}

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing LinkedIn message: {e}")
            return {"success": False, "error": str(e)}