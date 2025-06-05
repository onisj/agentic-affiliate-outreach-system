from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.types import Enum
from sqlalchemy.sql import func
from database.base import Base
from datetime import datetime
import enum
import uuid
import pytz
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Create base class for declarative models
Base = declarative_base()

class BaseModel:
    """Base model with common fields for all tables."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# ENUM definitions
class ProspectStatus(str, enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    DECLINED = "declined"
    ENROLLED = "enrolled"

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"

class MessageType(str, enum.Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    SMS = "sms"

class Content(Base, BaseModel):
    """Stores content assets for campaigns (e.g., landing pages)."""
    __tablename__ = "content"
    
    name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)  # e.g., "landing_page"
    data = Column(JSONB, default={}, server_default='{}', nullable=False)
    
    __table_args__ = (
        Index('ix_content_content_type', 'content_type'),
    )

class AffiliateProspect(Base, BaseModel):
    """Stores information about affiliate prospects."""
    __tablename__ = "affiliate_prospects"
    
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=True, index=True)
    last_name = Column(String(100), nullable=True, index=True)
    company = Column(String(255), nullable=True, index=True)
    website = Column(String(255), nullable=True)
    lead_source = Column(String(100), nullable=True, index=True)
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime(timezone=True), nullable=True)
    qualification_score = Column(Integer, default=50, nullable=True, index=True)
    status = Column(Enum(ProspectStatus), default=ProspectStatus.NEW, nullable=False, index=True)
    social_profiles = Column(JSONB, default={}, server_default='{}', nullable=False)
    
    # Relationships
    messages = relationship("MessageLog", back_populates="prospect", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_affiliate_prospects_status', 'status'),
        Index('ix_affiliate_prospects_qualification_score', 'qualification_score'),
        Index('ix_affiliate_prospects_email_status', 'email', 'status'),
    )

class MessageTemplate(Base, BaseModel):
    """Stores message templates for campaigns."""
    __tablename__ = "message_templates"
    
    name = Column(String(255), nullable=False, index=True)
    message_type = Column(Enum(MessageType), nullable=False)
    subject = Column(String(255), nullable=True)  # Nullable for non-email types
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    campaigns = relationship("OutreachCampaign", back_populates="template")
    sequences = relationship("Sequence", back_populates="template")
    messages = relationship("MessageLog", back_populates="template", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_message_templates_message_type', 'message_type'),
    )

class OutreachCampaign(Base, BaseModel):
    """Manages outreach campaigns."""
    __tablename__ = "outreach_campaigns"
    
    name = Column(String(255), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True)
    target_criteria = Column(JSONB, default={}, server_default='{}', nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    
    # Relationships
    template = relationship("MessageTemplate", back_populates="campaigns")
    messages = relationship("MessageLog", back_populates="campaign", cascade="all, delete-orphan")
    sequences = relationship("Sequence", back_populates="campaign", cascade="all, delete-orphan")
    ab_tests = relationship("ABTest", back_populates="campaign", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_outreach_campaigns_status', 'status'),
    )

class MessageLog(Base, BaseModel):
    """Logs messages sent to prospects."""
    __tablename__ = "message_logs"
    
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("affiliate_prospects.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    message_type = Column(Enum(MessageType), nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False, index=True)
    external_message_id = Column(String(255), nullable=True)
    ab_test_variant = Column(String(50), nullable=True)
    message_metadata = Column(JSON, nullable=True, default={})
    
    # Relationships
    prospect = relationship("AffiliateProspect", back_populates="messages")
    campaign = relationship("OutreachCampaign", back_populates="messages")
    template = relationship("MessageTemplate", back_populates="messages")
    
    __table_args__ = (
        Index('ix_message_logs_status', 'status'),
        Index('ix_message_logs_message_type', 'message_type'),
        Index('ix_message_logs_sent_at', 'sent_at'),
        Index('ix_message_logs_prospect_campaign', 'prospect_id', 'campaign_id'),
    )

class Sequence(Base, BaseModel):
    """Defines steps in a campaign sequence."""
    __tablename__ = "sequences"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("message_templates.id", ondelete="CASCADE"), nullable=False)
    delay_days = Column(Integer, default=0, nullable=False)
    condition = Column(JSONB, default={}, server_default='{}', nullable=False)
    
    # Relationships
    campaign = relationship("OutreachCampaign", back_populates="sequences")
    template = relationship("MessageTemplate", back_populates="sequences")
    
    __table_args__ = (
        Index('ix_sequences_campaign_id_step', 'campaign_id', 'step_number', unique=True),
    )

class ABTest(Base, BaseModel):
    """Manages A/B tests for campaigns."""
    __tablename__ = "ab_tests"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    variants = Column(JSONB, default={}, server_default='{}', nullable=False)
    
    # Relationships
    campaign = relationship("OutreachCampaign", back_populates="ab_tests")
    results = relationship("ABTestResult", back_populates="ab_test", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_ab_tests_campaign_id', 'campaign_id'),
    )

class ABTestResult(Base, BaseModel):
    """Stores results of A/B tests."""
    __tablename__ = "ab_test_results"
    
    ab_test_id = Column(UUID(as_uuid=True), ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(String(50), nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    open_rate = Column(Float, default=0.0, nullable=False)
    click_rate = Column(Float, default=0.0, nullable=False)
    reply_rate = Column(Float, default=0.0, nullable=False)
    
    # Relationships
    ab_test = relationship("ABTest", back_populates="results")
    
    __table_args__ = (
        Index('ix_ab_test_results_ab_test_id_variant', 'ab_test_id', 'variant_id', unique=True),
    )

class AffiliateStatus(enum.Enum):
    """Status of an affiliate in the system."""
    UNKNOWN = "unknown"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    QUALIFIED = "qualified"
    ONBOARDED = "onboarded"
    REJECTED = "rejected"

class Affiliate(Base):
    """Model for storing affiliate information."""
    __tablename__ = "affiliates"
    
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    status = Column(Enum(AffiliateStatus), default=AffiliateStatus.UNKNOWN)
    contact_info = Column(JSON)
    discovered_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Affiliate(id='{self.id}', name='{self.name}', status='{self.status}')>"

class WebhookEventType(str, enum.Enum):
    """Types of events that can trigger webhooks."""
    MESSAGE_OPENED = "message.opened"
    MESSAGE_CLICKED = "message.clicked"
    MESSAGE_REPLIED = "message.replied"
    MESSAGE_BOUNCED = "message.bounced"
    MESSAGE_FAILED = "message.failed"
    PROSPECT_STATUS_CHANGED = "prospect.status_changed"
    CAMPAIGN_STATUS_CHANGED = "campaign.status_changed"
    PROSPECT_ENGAGEMENT = "prospect.engagement"

class Webhook(Base, BaseModel):
    """Stores webhook configurations for external integrations."""
    __tablename__ = "webhooks"
    
    url = Column(String(512), nullable=False)
    secret = Column(String(255), nullable=False)  # For HMAC signature
    events = Column(JSONB, default=[], server_default='[]', nullable=False)  # List of WebhookEventType
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(255), nullable=True)
    failure_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    validate_payloads = Column(Boolean, default=True, nullable=False)
    payload_schema = Column(JSONB, nullable=True)  # Custom payload schema if needed
    
    __table_args__ = (
        Index('ix_webhooks_url', 'url'),
        Index('ix_webhooks_is_active', 'is_active'),
    )

class WebhookDelivery(Base, BaseModel):
    """Logs webhook delivery attempts."""
    __tablename__ = "webhook_deliveries"
    
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Enum(WebhookEventType), nullable=False)
    payload = Column(JSONB, nullable=False)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    webhook = relationship("Webhook")
    
    __table_args__ = (
        Index('ix_webhook_deliveries_webhook_id', 'webhook_id'),
        Index('ix_webhook_deliveries_event_type', 'event_type'),
        Index('ix_webhook_deliveries_success', 'success'),
        Index('ix_webhook_deliveries_retry_count', 'retry_count'),
        Index('ix_webhook_deliveries_next_retry', 'next_retry_at'),
    )

class AlertType(str, enum.Enum):
    """Types of alerts that can be generated."""
    HIGH_FAILURE_RATE = "high_failure_rate"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    MESSAGE_PROCESSING_ERROR = "message_processing_error"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_PAYLOAD = "invalid_payload"
    AUTHENTICATION_ERROR = "authentication_error"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    HIGH_LATENCY = "high_latency"

class AlertSeverity(str, enum.Enum):
    """Severity levels for alerts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Alert(Base):
    """Model for storing system alerts."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    alert_metadata = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SystemMetric(Base):
    """Model for storing system metrics."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_labels = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        # Add index for efficient querying
        Index('idx_system_metrics_name_timestamp', 'metric_name', 'timestamp'),
    )

class WebhookMetric(Base):
    """Model for storing webhook-specific metrics."""
    __tablename__ = "webhook_metrics"
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_labels = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    webhook = relationship("Webhook", back_populates="metrics")
    
    __table_args__ = (
        # Add index for efficient querying
        Index('idx_webhook_metrics_webhook_timestamp', 'webhook_id', 'timestamp'),
    )

# Add relationship to Webhook model
Webhook.metrics = relationship("WebhookMetric", back_populates="webhook")

# Pydantic models for API responses
class AlertResponse(BaseModel):
    id: int
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    alert_metadata: Optional[Dict[str, Any]]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class SystemMetricResponse(BaseModel):
    metric_name: str
    metric_value: float
    metric_labels: Optional[Dict[str, str]]
    timestamp: datetime

class WebhookMetricResponse(BaseModel):
    webhook_id: int
    metric_name: str
    metric_value: float
    metric_labels: Optional[Dict[str, str]]
    timestamp: datetime