# services/social_service.py
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
import logging
from jinja2 import Template, Environment, select_autoescape
from sqlalchemy.orm import Session
import tweepy
from database.models import MessageLog, MessageType, MessageStatus, MessageTemplate, ABTest, ABTestResult
from config.settings import settings
import requests
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialService:
    TWITTER_API_URL = "https://api.twitter.com/1.1"
    LINKEDIN_API_URL = "https://api.linkedin.com/v2"

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        
        # Initialize template environment
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Twitter credentials
        self.twitter_bearer_token: Optional[str] = settings.TWITTER_BEARER_TOKEN
        self.twitter_api_key: Optional[str] = settings.TWITTER_API_KEY
        self.twitter_api_secret: Optional[str] = settings.TWITTER_API_SECRET
        self.twitter_access_token: Optional[str] = settings.TWITTER_ACCESS_TOKEN
        self.twitter_access_token_secret: Optional[str] = settings.TWITTER_ACCESS_TOKEN_SECRET
        
        # LinkedIn credentials
        self.linkedin_client_id: Optional[str] = settings.LINKEDIN_CLIENT_ID
        self.linkedin_client_secret: Optional[str] = settings.LINKEDIN_CLIENT_SECRET
        self.linkedin_redirect_url: str = settings.LINKEDIN_REDIRECT_URL
        self.linkedin_access_token: Optional[str] = settings.LINKEDIN_ACCESS_TOKEN
        
        # Initialize Twitter client
        self._init_twitter_client()

    def _init_twitter_client(self):
        self.twitter_client: Optional[tweepy.Client] = None
        
        # Initialize Twitter client with both Bearer Token and OAuth 1.0a credentials
        if all([self.twitter_api_key, self.twitter_api_secret, 
                self.twitter_access_token, self.twitter_access_token_secret]):
            try:
                self.twitter_client = tweepy.Client(
                    consumer_key=self.twitter_api_key,
                    consumer_secret=self.twitter_api_secret,
                    access_token=self.twitter_access_token,
                    access_token_secret=self.twitter_access_token_secret,
                    bearer_token=self.twitter_bearer_token
                )
                logger.info("Twitter client initialized successfully with OAuth 1.0a")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client with OAuth 1.0a: {e}")
        elif self.twitter_bearer_token:
            try:
                self.twitter_client = tweepy.Client(bearer_token=self.twitter_bearer_token)
                logger.info("Twitter client initialized successfully with Bearer Token")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client with Bearer Token: {e}")

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
            try:
                response = self.twitter_client.create_direct_message(
                    participant_id=user_id, text=personalized_content
                )
                success = bool(response.data)
                logger.info(f"Twitter DM sent to user {user_id}: {'success' if success else 'failed'}")
            except tweepy.TooManyRequests as e:
                logger.error(f"Twitter rate limit exceeded: {e}")
                return {
                    "success": False,
                    "error": "Rate limit exceeded. Please try again later.",
                    "retry_after": e.response.headers.get("x-rate-limit-reset", 900)
                }
            except tweepy.Unauthorized as e:
                logger.error(f"Twitter authentication error: {e}")
                return {
                    "success": False,
                    "error": "Twitter authentication failed. Please check API credentials."
                }
            except tweepy.Forbidden as e:
                logger.error(f"Twitter permission error: {e}")
                return {
                    "success": False,
                    "error": "Not authorized to send DMs to this user."
                }
            except tweepy.NotFound as e:
                logger.error(f"Twitter user not found: {e}")
                return {
                    "success": False,
                    "error": "Twitter user not found."
                }
            except tweepy.TwitterServerError as e:
                logger.error(f"Twitter server error: {e}")
                return {
                    "success": False,
                    "error": "Twitter service temporarily unavailable."
                }

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
        """Send a LinkedIn message to a prospect using the LinkedIn Messaging API.

        Args:
            prospect_id: UUID string identifying the prospect.
            urn: LinkedIn URN of the recipient (e.g., urn:li:person:123).
            template: Jinja2 template for the message content.
            prospect_data: Dictionary containing prospect details (e.g., first_name, company).
            campaign_id: Optional UUID string for the campaign.
            db: SQLAlchemy session for database operations.

        Returns:
            Dictionary with success status, message ID, and error message if any.
        """
        if not db:
            logger.error("Database session is required")
            return {"success": False, "error": "Database session is required"}
        if not all([self.linkedin_client_id, self.linkedin_client_secret, self.linkedin_access_token]):
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

            # Prepare headers with OAuth 2.0 token
            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            # First, create a conversation
            conversation_data = {
                "recipients": [{"person": {"id": urn}}],
                "subject": "Partnership Opportunity",
                "body": personalized_content
            }

            try:
                response = requests.post(
                    f"{self.LINKEDIN_API_URL}/messages",
                    headers=headers,
                    json=conversation_data,
                    timeout=10
                )
                response.raise_for_status()  # Raise exception for non-200 status codes

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.error("LinkedIn authentication failed - token may be expired")
                    return {"success": False, "error": "LinkedIn authentication failed - token expired"}
                elif e.response.status_code == 403:
                    logger.error("LinkedIn permission denied - insufficient scope")
                    return {"success": False, "error": "LinkedIn permission denied - check API scope"}
                elif e.response.status_code == 429:
                    logger.error("LinkedIn rate limit exceeded")
                    return {"success": False, "error": "LinkedIn rate limit exceeded"}
                else:
                    logger.error(f"LinkedIn API request failed: {e.response.text}")
                    return {"success": False, "error": f"LinkedIn API error: {e.response.text}"}

            except requests.exceptions.RequestException as e:
                logger.error(f"LinkedIn request failed: {str(e)}")
                return {"success": False, "error": f"LinkedIn request failed: {str(e)}"}

            message_id = response.json().get("id")
            success = bool(message_id)

            # Log the message
            message_log = MessageLog(
                id=str(uuid.uuid4()),
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                message_type=MessageType.LINKEDIN.value,
                content=personalized_content,
                sent_at=datetime.now(timezone.utc),
                status=MessageStatus.SENT.value if success else MessageStatus.BOUNCED.value,
                external_message_id=message_id
            )

            db.add(message_log)
            db.commit()
            logger.info(f"LinkedIn message sent to prospect {prospect_id}, success: {success}")

            return {
                "success": success,
                "message_id": message_log.id,
                "external_message_id": message_id
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error sending LinkedIn message: {str(e)}")
            return {"success": False, "error": str(e)}

    def refresh_linkedin_token(self) -> bool:
        """Refresh the LinkedIn OAuth 2.0 access token."""
        try:
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.linkedin_client_id,
                "client_secret": self.linkedin_client_secret
            }
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.linkedin_access_token = token_data["access_token"]
            logger.info("LinkedIn access token refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh LinkedIn token: {e}")
            return False

    def get_linkedin_profile(self, urn: str) -> Dict[str, Any]:
        """Fetch a LinkedIn profile using the URN.

        Args:
            urn: LinkedIn URN of the profile (e.g., urn:li:person:123).

        Returns:
            Dictionary containing profile data or error information.
        """
        if not all([self.linkedin_client_id, self.linkedin_client_secret, self.linkedin_access_token]):
            logger.error("LinkedIn credentials not configured")
            return {"success": False, "error": "LinkedIn credentials not configured"}

        try:
            # Validate URN format
            if not urn.startswith('urn:li:person:'):
                raise ValueError("Invalid LinkedIn URN format")

            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            # Fetch basic profile
            profile_url = f"{self.LINKEDIN_API_URL}/me"
            response = requests.get(profile_url, headers=headers)
            response.raise_for_status()
            profile_data = response.json()

            # Fetch additional profile fields
            fields = [
                "id", "firstName", "lastName", "headline", "industry",
                "location", "positions", "educations", "skills"
            ]
            fields_url = f"{self.LINKEDIN_API_URL}/me?projection=({','.join(fields)})"
            response = requests.get(fields_url, headers=headers)
            response.raise_for_status()
            detailed_data = response.json()

            return {
                "success": True,
                "profile": detailed_data
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("LinkedIn authentication failed - token may be expired")
                return {"success": False, "error": "LinkedIn authentication failed - token expired"}
            elif e.response.status_code == 403:
                logger.error("LinkedIn permission denied - insufficient scope")
                return {"success": False, "error": "LinkedIn permission denied - check API scope"}
            elif e.response.status_code == 429:
                logger.error("LinkedIn rate limit exceeded")
                return {"success": False, "error": "LinkedIn rate limit exceeded"}
            else:
                logger.error(f"LinkedIn API request failed: {e.response.text}")
                return {"success": False, "error": f"LinkedIn API error: {e.response.text}"}

        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_linkedin_connections(self, start: int = 0, count: int = 50) -> Dict[str, Any]:
        """Fetch LinkedIn connections.

        Args:
            start: Starting index for pagination.
            count: Number of connections to fetch.

        Returns:
            Dictionary containing connections data or error information.
        """
        if not all([self.linkedin_client_id, self.linkedin_client_secret, self.linkedin_access_token]):
            logger.error("LinkedIn credentials not configured")
            return {"success": False, "error": "LinkedIn credentials not configured"}

        try:
            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            connections_url = f"{self.LINKEDIN_API_URL}/connections?start={start}&count={count}"
            response = requests.get(connections_url, headers=headers)
            response.raise_for_status()
            connections_data = response.json()

            return {
                "success": True,
                "connections": connections_data.get("elements", []),
                "total": connections_data.get("paging", {}).get("total", 0)
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("LinkedIn authentication failed - token may be expired")
                return {"success": False, "error": "LinkedIn authentication failed - token expired"}
            elif e.response.status_code == 403:
                logger.error("LinkedIn permission denied - insufficient scope")
                return {"success": False, "error": "LinkedIn permission denied - check API scope"}
            elif e.response.status_code == 429:
                logger.error("LinkedIn rate limit exceeded")
                return {"success": False, "error": "LinkedIn rate limit exceeded"}
            else:
                logger.error(f"LinkedIn API request failed: {e.response.text}")
                return {"success": False, "error": f"LinkedIn API error: {e.response.text}"}

        except Exception as e:
            logger.error(f"Error fetching LinkedIn connections: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_linkedin_analytics(self, message_id: str) -> Dict[str, Any]:
        """Fetch analytics for a LinkedIn message.

        Args:
            message_id: ID of the LinkedIn message.

        Returns:
            Dictionary containing message analytics or error information.
        """
        if not all([self.linkedin_client_id, self.linkedin_client_secret, self.linkedin_access_token]):
            logger.error("LinkedIn credentials not configured")
            return {"success": False, "error": "LinkedIn credentials not configured"}

        try:
            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            analytics_url = f"{self.LINKEDIN_API_URL}/messages/{message_id}/analytics"
            response = requests.get(analytics_url, headers=headers)
            response.raise_for_status()
            analytics_data = response.json()

            return {
                "success": True,
                "analytics": {
                    "views": analytics_data.get("views", 0),
                    "clicks": analytics_data.get("clicks", 0),
                    "responses": analytics_data.get("responses", 0),
                    "sent_at": analytics_data.get("sentAt"),
                    "last_viewed": analytics_data.get("lastViewedAt")
                }
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("LinkedIn authentication failed - token may be expired")
                return {"success": False, "error": "LinkedIn authentication failed - token expired"}
            elif e.response.status_code == 403:
                logger.error("LinkedIn permission denied - insufficient scope")
                return {"success": False, "error": "LinkedIn permission denied - check API scope"}
            elif e.response.status_code == 429:
                logger.error("LinkedIn rate limit exceeded")
                return {"success": False, "error": "LinkedIn rate limit exceeded"}
            else:
                logger.error(f"LinkedIn API request failed: {e.response.text}")
                return {"success": False, "error": f"LinkedIn API error: {e.response.text}"}

        except Exception as e:
            logger.error(f"Error fetching LinkedIn analytics: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_linkedin_invitation(
        self,
        prospect_id: str,
        urn: str,
        message: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Send a LinkedIn connection invitation.

        Args:
            prospect_id: UUID string identifying the prospect.
            urn: LinkedIn URN of the recipient.
            message: Custom invitation message.
            db: SQLAlchemy session for database operations.

        Returns:
            Dictionary with success status and error message if any.
        """
        if not db:
            logger.error("Database session is required")
            return {"success": False, "error": "Database session is required"}
        if not all([self.linkedin_client_id, self.linkedin_client_secret, self.linkedin_access_token]):
            logger.error("LinkedIn credentials not configured")
            return {"success": False, "error": "LinkedIn credentials not configured"}

        try:
            # Validate UUID
            try:
                uuid.UUID(prospect_id)
            except ValueError:
                logger.error("Invalid UUID format for prospect_id")
                return {"success": False, "error": "Invalid UUID format"}

            # Validate URN
            if not urn.startswith('urn:li:person:'):
                logger.error("Invalid LinkedIn URN format")
                return {"success": False, "error": "Invalid LinkedIn URN format"}

            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            invitation_data = {
                "invitee": {"person": {"id": urn}},
                "message": message[:300]  # LinkedIn invitation message limit
            }

            response = requests.post(
                f"{self.LINKEDIN_API_URL}/invitations",
                headers=headers,
                json=invitation_data
            )
            response.raise_for_status()

            invitation_id = response.json().get("id")
            success = bool(invitation_id)

            # Log the invitation
            message_log = MessageLog(
                id=str(uuid.uuid4()),
                prospect_id=prospect_id,
                message_type=MessageType.LINKEDIN_INVITATION.value,
                content=message,
                sent_at=datetime.now(timezone.utc),
                status=MessageStatus.SENT.value if success else MessageStatus.BOUNCED.value,
                external_message_id=invitation_id
            )

            db.add(message_log)
            db.commit()
            logger.info(f"LinkedIn invitation sent to prospect {prospect_id}, success: {success}")

            return {
                "success": success,
                "message_id": message_log.id,
                "invitation_id": invitation_id
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("LinkedIn authentication failed - token may be expired")
                return {"success": False, "error": "LinkedIn authentication failed - token expired"}
            elif e.response.status_code == 403:
                logger.error("LinkedIn permission denied - insufficient scope")
                return {"success": False, "error": "LinkedIn permission denied - check API scope"}
            elif e.response.status_code == 429:
                logger.error("LinkedIn rate limit exceeded")
                return {"success": False, "error": "LinkedIn rate limit exceeded"}
            else:
                logger.error(f"LinkedIn API request failed: {e.response.text}")
                return {"success": False, "error": f"LinkedIn API error: {e.response.text}"}

        except Exception as e:
            db.rollback()
            logger.error(f"Error sending LinkedIn invitation: {str(e)}")
            return {"success": False, "error": str(e)}

    # Template Management Methods
    async def create_template(
        self,
        name: str,
        content: str,
        message_type: MessageType,
        subject: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new message template."""
        if not self.db:
            raise ValueError("Database session is required")
            
        try:
            # Validate template syntax
            self.env.from_string(content)
            
            template = MessageTemplate(
                id=str(uuid.uuid4()),
                name=name,
                content=content,
                message_type=message_type,
                subject=subject,
                variables=variables or []
            )
            
            self.db.add(template)
            self.db.commit()
            
            return {
                "id": template.id,
                "name": template.name,
                "message_type": template.message_type,
                "created_at": template.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            self.db.rollback()
            raise

    # A/B Testing Methods
    async def create_ab_test(
        self,
        campaign_id: str,
        name: str,
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create an A/B test for message variants."""
        if not self.db:
            raise ValueError("Database session is required")
            
        try:
            ab_test = ABTest(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                name=name,
                variants=variants
            )
            
            self.db.add(ab_test)
            self.db.commit()
            
            return {
                "id": ab_test.id,
                "name": ab_test.name,
                "variants": ab_test.variants
            }
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            self.db.rollback()
            raise

    async def get_personalized_message(
        self,
        template_id: str,
        data: Dict[str, Any],
        ab_test_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a personalized message from a template."""
        if not self.db:
            raise ValueError("Database session is required")
            
        try:
            template = self.db.query(MessageTemplate).filter(
                MessageTemplate.id == template_id
            ).first()
            
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Select variant if A/B testing
            variant = None
            if ab_test_id:
                variant = await self._select_ab_test_variant(ab_test_id)
                if variant:
                    content = variant.get("content", template.content)
                    subject = variant.get("subject", template.subject)
                else:
                    content = template.content
                    subject = template.subject
            else:
                content = template.content
                subject = template.subject
            
            # Render template with data
            jinja_template = self.env.from_string(content)
            personalized_content = jinja_template.render(**data)
            
            if subject:
                subject_template = self.env.from_string(subject)
                personalized_subject = subject_template.render(**data)
            else:
                personalized_subject = None
            
            return {
                "content": personalized_content,
                "subject": personalized_subject,
                "variant_id": variant.get("id") if variant else None
            }
            
        except Exception as e:
            logger.error(f"Error personalizing message: {e}")
            raise

    async def _select_ab_test_variant(self, ab_test_id: str) -> Optional[Dict[str, Any]]:
        """Select a variant for A/B testing."""
        if not self.db:
            raise ValueError("Database session is required")
            
        try:
            ab_test = self.db.query(ABTest).filter(
                ABTest.id == ab_test_id
            ).first()
            
            if not ab_test:
                return None
            
            # Get current results
            results = self.db.query(ABTestResult).filter(
                ABTestResult.ab_test_id == ab_test_id
            ).all()
            
            # If no results yet, random selection
            if not results:
                return random.choice(ab_test.variants)
            
            # Calculate success rates
            variant_stats = {}
            for result in results:
                variant_id = result.variant_id
                if variant_id not in variant_stats:
                    variant_stats[variant_id] = {
                        "sent": 0,
                        "success": 0
                    }
                variant_stats[variant_id]["sent"] += result.sent_count
                variant_stats[variant_id]["success"] += (
                    result.open_rate + result.click_rate + result.reply_rate
                ) / 3
            
            # Select variant with highest success rate
            best_variant = max(
                variant_stats.items(),
                key=lambda x: x[1]["success"] / x[1]["sent"] if x[1]["sent"] > 0 else 0
            )[0]
            
            return next(
                (v for v in ab_test.variants if v["id"] == best_variant),
                random.choice(ab_test.variants)
            )
            
        except Exception as e:
            logger.error(f"Error selecting A/B test variant: {e}")
            return None

    async def update_ab_test_results(
        self,
        ab_test_id: str,
        variant_id: str,
        sent_count: int,
        open_rate: float,
        click_rate: float,
        reply_rate: float
    ) -> bool:
        """Update A/B test results."""
        if not self.db:
            raise ValueError("Database session is required")
            
        try:
            result = ABTestResult(
                ab_test_id=ab_test_id,
                variant_id=variant_id,
                sent_count=sent_count,
                open_rate=open_rate,
                click_rate=click_rate,
                reply_rate=reply_rate
            )
            
            self.db.add(result)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating A/B test results: {e}")
            self.db.rollback()
            return False

    def fetch_twitter_profile(self, twitter_handle: str) -> Dict[str, Any]:
        """Fetch Twitter profile data."""
        try:
            if not self.twitter_client:
                raise Exception("Twitter client not initialized")
            user = self.twitter_client.get_user(username=twitter_handle.lstrip('@'))
            return {
                "username": user.data.username,
                "followers_count": user.data.public_metrics["followers_count"],
                "tweet_count": user.data.public_metrics["tweet_count"]
            }
        except Exception as e:
            logger.error(f"Error fetching Twitter profile: {str(e)}")
            raise

    def fetch_linkedin_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch LinkedIn profile data."""
        try:
            if not self.linkedin_access_token:
                raise Exception("LinkedIn access token not configured")
            # Implementation will be added later
            return {"url": linkedin_url, "connections": 0}
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile: {str(e)}")
            raise

    def analyze_social_engagement(self, prospect) -> Dict[str, Any]:
        """Analyze social media engagement."""
        try:
            twitter_data = self.fetch_twitter_profile(prospect.twitter_handle) if prospect.twitter_handle else {}
            linkedin_data = self.fetch_linkedin_profile(prospect.linkedin_url) if prospect.linkedin_url else {}
            
            engagement_score = (
                twitter_data.get("followers_count", 0) * 0.4 +
                twitter_data.get("tweet_count", 0) * 0.3 +
                linkedin_data.get("connections", 0) * 0.3
            )
            
            activity_level = "high" if engagement_score > 1000 else "medium" if engagement_score > 100 else "low"
            
            return {
                "engagement_score": engagement_score,
                "activity_level": activity_level,
                "twitter_data": twitter_data,
                "linkedin_data": linkedin_data
            }
        except Exception as e:
            logger.error(f"Error analyzing social engagement: {str(e)}")
            raise

    def cache_social_data(self, prospect_id: str, platform: str, data: Dict[str, Any]) -> None:
        """Cache social media data."""
        try:
            # Implementation will be added later
            pass
        except Exception as e:
            logger.error(f"Error caching social data: {str(e)}")
            raise

    def validate_twitter_handle(self, handle: str) -> bool:
        """Validate Twitter handle format."""
        return bool(handle and handle.startswith('@'))

    def send_twitter_message(self, handle: str, message: str) -> Dict[str, Any]:
        """Send Twitter direct message."""
        try:
            if not self.twitter_client:
                raise Exception("Twitter client not initialized")
            if not self.validate_twitter_handle(handle):
                raise ValueError("Invalid Twitter handle format")
            
            user = self.twitter_client.get_user(username=handle.lstrip('@'))
            response = self.twitter_client.create_direct_message(
                participant_id=user.data.id,
                text=message
            )
            
            return {
                "success": True,
                "message_id": response.data.id,
                "recipient": handle
            }
        except Exception as e:
            logger.error(f"Error sending Twitter message: {str(e)}")
            raise