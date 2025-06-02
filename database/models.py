from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Enum, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class ProspectStatus(enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    DECLINED = "declined"
    ENROLLED = "enrolled"

class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class MessageStatus(enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"

class MessageType(enum.Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"

class AffiliateProspect(Base):
    __tablename__ = "affiliate_prospects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    website = Column(String(255))
    social_profiles = Column(JSON)
    lead_source = Column(String(100))
    qualification_score = Column(Integer, default=0)
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime)
    status = Column(Enum(ProspectStatus), default=ProspectStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MessageTemplate(Base):
    __tablename__ = "message_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.EMAIL)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    template_id = Column(UUID(as_uuid=True))
    target_criteria = Column(JSON)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class MessageLog(Base):
    __tablename__ = "message_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), nullable=False)
    campaign_id = Column(UUID(as_uuid=True))
    template_id = Column(UUID(as_uuid=True))
    message_type = Column(Enum(MessageType), default=MessageType.EMAIL)
    subject = Column(String(500))
    content = Column(Text)
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    ab_test_variant = Column(String(50))  # Track A/B test variant

class Content(Base):
    __tablename__ = "content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class Sequence(Base):
    __tablename__ = "sequences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), nullable=False)
    step_number = Column(Integer, nullable=False)
    template_id = Column(UUID(as_uuid=True), nullable=False)
    delay_days = Column(Integer, nullable=False)
    condition = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ABTest(Base):
    __tablename__ = "ab_tests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    variants = Column(JSON, nullable=False)  # e.g., [{"variant_id": "A", "template_id": "uuid"}, ...]
    created_at = Column(DateTime, default=datetime.utcnow)

class ABTestResult(Base):
    __tablename__ = "ab_test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ab_test_id = Column(UUID(as_uuid=True), nullable=False)
    variant_id = Column(String(50), nullable=False)
    sent_count = Column(Integer, default=0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    reply_rate = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)