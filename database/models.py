from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum
from sqlalchemy.sql import func
from database.base import Base
from datetime import datetime
import enum
import uuid
import pytz


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

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"

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
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    lead_source = Column(String(100), nullable=True)
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime(timezone=True), nullable=True)
    qualification_score = Column(Integer, default=50, nullable=True)
    status = Column(Enum(ProspectStatus), default=ProspectStatus.NEW, nullable=False)
    social_profiles = Column(JSONB, default={}, server_default='{}', nullable=False)
    
    # Relationships
    messages = relationship("MessageLog", back_populates="prospect", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_affiliate_prospects_status', 'status'),
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
    
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("affiliate_prospects.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True)
    message_type = Column(Enum(MessageType), nullable=False)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    ab_test_variant = Column(String(50), nullable=True)
    
    # Relationships
    prospect = relationship("AffiliateProspect", back_populates="messages")
    campaign = relationship("OutreachCampaign", back_populates="messages")
    
    __table_args__ = (
        Index('ix_message_logs_status', 'status'),
        Index('ix_message_logs_message_type', 'message_type'),
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