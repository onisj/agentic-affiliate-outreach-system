"""
Base Channel Service

Abstract base class defining the interface for all channel services.
Provides common functionality and enforces consistent implementation patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ChannelType(Enum):
    """Supported channel types"""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    DISCORD = "discord"

class MessageStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"
    BOUNCED = "bounced"
    BLOCKED = "blocked"

class EngagementType(Enum):
    """Types of engagement metrics"""
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    CLICK = "click"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    BLOCK = "block"
    REPORT = "report"

@dataclass
class ChannelConfig:
    """Configuration for a channel service"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 100
    rate_limit_window: int = 3600  # seconds
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1
    enabled: bool = True
    features: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageRequest:
    """Request to send a message"""
    recipient_id: str
    content: str
    subject: Optional[str] = None
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    scheduled_time: Optional[datetime] = None
    priority: int = 1
    campaign_id: Optional[str] = None
    template_id: Optional[str] = None

@dataclass
class MessageResponse:
    """Response from sending a message"""
    success: bool
    message_id: Optional[str] = None
    external_id: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    error: Optional[str] = None
    retry_after: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class ProfileData:
    """Profile information from a channel"""
    user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    verified: bool = False
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    engagement_rate: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EngagementMetrics:
    """Engagement metrics for content or profile"""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    saves: int = 0
    engagement_rate: float = 0.0
    reach: int = 0
    impressions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseChannelService(ABC):
    """Abstract base class for all channel services"""
    
    def __init__(self, config: ChannelConfig, db: Optional[Session] = None):
        self.config = config
        self.db = db
        self.channel_type = self._get_channel_type()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize rate limiting
        self._rate_limit_tracker = {}
        
        # Validate configuration
        self._validate_config()
        
        # Initialize client
        self._init_client()
    
    @abstractmethod
    def _get_channel_type(self) -> ChannelType:
        """Return the channel type for this service"""
        pass
    
    @abstractmethod
    def _init_client(self) -> None:
        """Initialize the API client for this channel"""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the configuration for this channel"""
        pass
    
    @abstractmethod
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send a message through this channel"""
        pass
    
    @abstractmethod
    async def get_profile(self, user_id: str) -> Optional[ProfileData]:
        """Get profile information for a user"""
        pass
    
    @abstractmethod
    async def get_engagement_metrics(self, content_id: str) -> Optional[EngagementMetrics]:
        """Get engagement metrics for content"""
        pass
    
    # Common utility methods
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = datetime.now(timezone.utc)
        window_start = current_time.timestamp() - self.config.rate_limit_window
        
        # Clean old entries
        self._rate_limit_tracker = {
            timestamp: count for timestamp, count in self._rate_limit_tracker.items()
            if timestamp > window_start
        }
        
        # Count requests in current window
        total_requests = sum(self._rate_limit_tracker.values())
        
        return total_requests < self.config.rate_limit
    
    def _record_request(self) -> None:
        """Record a request for rate limiting"""
        current_time = datetime.now(timezone.utc).timestamp()
        self._rate_limit_tracker[current_time] = self._rate_limit_tracker.get(current_time, 0) + 1
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID"""
        return f"{self.channel_type.value}_{uuid.uuid4()}"
    
    def _log_message(self, request: MessageRequest, response: MessageResponse) -> None:
        """Log message details to database if available"""
        if not self.db:
            return
        
        try:
            from database.models import MessageLog, MessageType
            
            # Map channel type to message type
            message_type_map = {
                ChannelType.EMAIL: MessageType.EMAIL,
                ChannelType.LINKEDIN: MessageType.LINKEDIN,
                ChannelType.TWITTER: MessageType.TWITTER,
                ChannelType.INSTAGRAM: MessageType.INSTAGRAM,
                ChannelType.FACEBOOK: MessageType.FACEBOOK,
                ChannelType.WHATSAPP: MessageType.WHATSAPP,
                ChannelType.YOUTUBE: MessageType.YOUTUBE,
                ChannelType.TIKTOK: MessageType.TIKTOK,
                ChannelType.TELEGRAM: MessageType.TELEGRAM,
                ChannelType.REDDIT: MessageType.REDDIT,
                ChannelType.DISCORD: MessageType.DISCORD,
            }
            
            message_log = MessageLog(
                id=response.message_id or self._generate_message_id(),
                prospect_id=request.recipient_id,
                campaign_id=request.campaign_id,
                message_type=message_type_map.get(self.channel_type, MessageType.EMAIL).value,
                content=request.content,
                subject=request.subject,
                sent_at=response.timestamp,
                status=response.status.value,
                external_message_id=response.external_id,
                metadata={
                    **request.metadata,
                    **response.metadata,
                    'channel': self.channel_type.value,
                    'success': response.success,
                    'error': response.error
                }
            )
            
            self.db.add(message_log)
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log message: {str(e)}")
            if self.db:
                self.db.rollback()
    
    def _handle_api_error(self, error: Exception, context: str = "") -> MessageResponse:
        """Handle API errors and return appropriate response"""
        error_msg = str(error)
        self.logger.error(f"API error in {context}: {error_msg}")
        
        # Determine if error is retryable
        retryable_errors = [
            "rate limit",
            "timeout",
            "server error",
            "service unavailable",
            "internal error"
        ]
        
        is_retryable = any(err in error_msg.lower() for err in retryable_errors)
        
        return MessageResponse(
            success=False,
            error=error_msg,
            retry_after=self.config.retry_delay if is_retryable else None,
            metadata={
                'retryable': is_retryable,
                'context': context
            }
        )
    
    def _personalize_content(self, content: str, profile: Optional[ProfileData] = None) -> str:
        """Apply basic personalization to content"""
        if not profile:
            return content
        
        # Basic variable substitution
        replacements = {
            '{name}': profile.display_name or profile.username or 'there',
            '{username}': profile.username or '',
            '{first_name}': (profile.display_name or '').split()[0] if profile.display_name else 'there',
        }
        
        personalized = content
        for placeholder, value in replacements.items():
            personalized = personalized.replace(placeholder, value)
        
        return personalized
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the channel API"""
        try:
            # Try to get our own profile or make a simple API call
            result = await self.get_profile("me")
            return {
                'success': True,
                'channel': self.channel_type.value,
                'message': 'Connection successful'
            }
        except Exception as e:
            return {
                'success': False,
                'channel': self.channel_type.value,
                'error': str(e)
            }
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Get information about this channel"""
        return {
            'channel_type': self.channel_type.value,
            'enabled': self.config.enabled,
            'rate_limit': self.config.rate_limit,
            'rate_limit_window': self.config.rate_limit_window,
            'features': self.config.features,
            'has_credentials': bool(self.config.api_key or self.config.access_token)
        }
