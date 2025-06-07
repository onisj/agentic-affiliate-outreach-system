from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class ProspectStatus(enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    REJECTED = "rejected"

class ContentType(enum.Enum):
    LANDING_PAGE = "landing_page"
    EMAIL_TEMPLATE = "email_template"
    SOCIAL_POST = "social_post"
    WEBPAGE = "webpage"

class AffiliateProspect(Base):
    __tablename__ = "affiliate_prospects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    company = Column(String)
    website = Column(String)
    lead_source = Column(String)
    status = Column(Enum(ProspectStatus), default=ProspectStatus.NEW)
    score = Column(Float)
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responses = relationship("ProspectResponse", back_populates="prospect")
    social_profiles = relationship("SocialProfile", back_populates="prospect")
    campaign_interactions = relationship("CampaignInteraction", back_populates="prospect")

class Content(Base):
    __tablename__ = "content"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_type = Column(Enum(ContentType))
    name = Column(String)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProspectResponse(Base):
    __tablename__ = "prospect_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("affiliate_prospects.id"))
    response_type = Column(String)  # email, social, web
    content = Column(String)
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prospect = relationship("AffiliateProspect", back_populates="responses")

class SocialProfile(Base):
    __tablename__ = "social_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("affiliate_prospects.id"))
    platform = Column(String)  # linkedin, twitter, etc.
    profile_url = Column(String)
    username = Column(String)
    followers_count = Column(Integer)
    engagement_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prospect = relationship("AffiliateProspect", back_populates="social_profiles")

class CampaignInteraction(Base):
    __tablename__ = "campaign_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("affiliate_prospects.id"))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    interaction_type = Column(String)  # email_open, click, response, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
    
    # Relationships
    prospect = relationship("AffiliateProspect", back_populates="campaign_interactions")
    campaign = relationship("Campaign", back_populates="interactions")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String)
    status = Column(String)  # draft, active, completed, etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = relationship("CampaignInteraction", back_populates="campaign") 