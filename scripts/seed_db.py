from sqlalchemy.orm import Session
from database.models import MessageTemplate, OutreachCampaign, AffiliateProspect, MessageType, CampaignStatus, ProspectStatus
from database.base import Base
from database.session import SessionLocal, engine
from uuid import uuid4
from datetime import datetime
import pytz
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def create_message_templates(db: Session) -> list[MessageTemplate]:
    """Seed multiple message templates if none exist."""
    if db.query(MessageTemplate).count() > 0:
        logger.info("Message templates already exist, skipping seeding.")
        return db.query(MessageTemplate).all()

    templates = [
        MessageTemplate(
            id=uuid4(),
            name="Welcome Email",
            message_type=MessageType.EMAIL,
            content="Hi {{first_name}}, welcome to our affiliate program at example.com!",
            is_active=True,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
        MessageTemplate(
            id=uuid4(),
            name="Follow-Up Twitter DM",
            message_type=MessageType.TWITTER_DM,
            content="Hey {{first_name}}, excited about partnering with example.com? Let's chat!",
            is_active=True,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
        MessageTemplate(
            id=uuid4(),
            name="Cold Outreach Email",
            message_type=MessageType.EMAIL,
            content="Hello {{first_name}}, explore affiliate opportunities at example.com!",
            is_active=True,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
    ]
    for template in templates:
        db.add(template)
        db.commit()  # Commit each template to match your working script
        logger.info("Seeded MessageTemplate: %s (%s)", template.id, template.name)
    return templates

def create_outreach_campaigns(db: Session, templates: list[MessageTemplate]) -> list[OutreachCampaign]:
    """Seed multiple outreach campaigns if none exist, using provided templates."""
    if db.query(OutreachCampaign).count() > 0:
        logger.info("Outreach campaigns already exist, skipping seeding.")
        return db.query(OutreachCampaign).all()

    if not templates:
        raise ValueError("No MessageTemplate found; seed MessageTemplate first.")

    campaigns = [
        OutreachCampaign(
            id=uuid4(),
            name="Spring Tech Campaign",
            template_id=templates[0].id,
            status=CampaignStatus.DRAFT,
            target_criteria={"min_score": 70, "industry": "tech"},
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
        OutreachCampaign(
            id=uuid4(),
            name="Twitter Outreach",
            template_id=templates[1].id,
            status=CampaignStatus.ACTIVE,
            target_criteria={"min_score": 60, "has_twitter": True},
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
        OutreachCampaign(
            id=uuid4(),
            name="Cold Email Blast",
            template_id=templates[2].id,
            status=CampaignStatus.DRAFT,
            target_criteria={"min_score": 50, "industry": "ecommerce"},
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
    ]
    for campaign in campaigns:
        db.add(campaign)
        logger.info("Seeded OutreachCampaign: %s (%s)", campaign.id, campaign.name)
    return campaigns

def create_affiliate_prospects(db: Session) -> list[AffiliateProspect]:
    """Seed multiple affiliate prospects if none exist."""
    if db.query(AffiliateProspect).count() > 0:
        logger.info("Affiliate prospects already exist, skipping seeding.")
        return db.query(AffiliateProspect).all()

    prospects = [
        AffiliateProspect(
            id=uuid4(),
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            company="Acme Corp",
            website="https://example.com",
            consent_given=True,
            qualification_score=80,
            status=ProspectStatus.NEW,
            social_profiles={"twitter": "johndoe"},
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
        AffiliateProspect(
            id=uuid4(),
            email="jane.smith@example.com",
            first_name="Jane",
            last_name="Smith",
            company="Smith Ventures",
            website="https://example.com/jane",
            consent_given=False,
            qualification_score=65,
            status=ProspectStatus.CONTACTED,
            social_profiles={"twitter": "janesmith"},
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
        AffiliateProspect(
            id=uuid4(),
            email="bob.jones@example.com",
            first_name="Bob",
            last_name="Jones",
            company="Jones Ecommerce",
            website="https://example.com/bob",
            consent_given=True,
            qualification_score=55,
            status=ProspectStatus.NEW,
            social_profiles={},
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        ),
    ]
    for prospect in prospects:
        db.add(prospect)
        logger.info("Seeded AffiliateProspect: %s (%s)", prospect.id, prospect.email)
    return prospects

def seed_db():
    """Seed the database with initial data for all required tables."""
    db: Session = SessionLocal()
    try:
        # Seed data in order of dependency
        templates = create_message_templates(db)
        campaigns = create_outreach_campaigns(db, templates)
        prospects = create_affiliate_prospects(db)

        db.commit()  # Final commit for campaigns and prospects
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error("Error seeding database: %s", str(e))
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()