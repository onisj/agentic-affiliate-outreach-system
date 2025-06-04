from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.session import get_db
from database.models import OutreachCampaign, AffiliateProspect, MessageTemplate, CampaignStatus
from api.schemas.campaigns import CampaignCreate
from tasks.sequence_tasks import process_sequence_step
from uuid import UUID
import logging
from typing import List

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

def serialize_campaign_response(campaign) -> dict:
    """Helper function to properly serialize campaign data"""
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "template_id": str(campaign.template_id) if campaign.template_id else None,
        "target_criteria": campaign.target_criteria or {},
        "status": campaign.status.value if hasattr(campaign.status, 'value') else str(campaign.status),
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign with proper validation and error handling"""
    logger.debug("Starting create_campaign with data: %s", campaign.model_dump())
    
    try:
        # Validate template_id format
        try:
            template_uuid = UUID(campaign.template_id)
        except ValueError:
            logger.error("Invalid UUID format for template_id: %s", campaign.template_id)
            raise HTTPException(
                status_code=400, 
                detail="Invalid template_id format. Must be a valid UUID."
            )
        
        # Check if template exists and is active
        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == template_uuid,
            MessageTemplate.is_active == True
        ).first()
        
        if not template:
            logger.error("Template not found or inactive for id: %s", campaign.template_id)
            raise HTTPException(
                status_code=404, 
                detail="Template not found or is inactive"
            )
        
        # Create campaign
        db_campaign = OutreachCampaign(
            name=campaign.name.strip(),
            template_id=template_uuid,
            target_criteria=campaign.target_criteria or {},
            status=CampaignStatus.DRAFT
        )
        
        db.add(db_campaign)
        
        try:
            db.commit()
            db.refresh(db_campaign)
        except IntegrityError as e:
            db.rollback()
            logger.error("Database integrity error creating campaign: %s", e)
            raise HTTPException(
                status_code=400,
                detail="Failed to create campaign due to data integrity constraints"
            )
        
        logger.info("Created campaign: %s", db_campaign.id)
        return serialize_campaign_response(db_campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error creating campaign: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
async def get_campaigns(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Get campaigns with proper serialization"""
    logger.debug("Fetching campaigns with skip=%d, limit=%d", skip, limit)
    
    try:
        campaigns = db.query(OutreachCampaign).offset(skip).limit(limit).all()
        logger.debug("Fetched %d campaigns", len(campaigns))
        
        # Serialize each campaign properly
        serialized_campaigns = [serialize_campaign_response(campaign) for campaign in campaigns]
        return serialized_campaigns
        
    except Exception as e:
        logger.error("Error fetching campaigns: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get a specific campaign with proper serialization"""
    logger.debug("Fetching campaign with id=%s", campaign_id)
    
    try:
        # Validate UUID format
        try:
            campaign_uuid = UUID(campaign_id)
        except ValueError:
            logger.error("Invalid UUID format: %s", campaign_id)
            raise HTTPException(status_code=400, detail="Invalid campaign_id format")
        
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == campaign_uuid
        ).first()
        
        if not campaign:
            logger.error("Campaign not found: %s", campaign_id)
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        logger.debug("Found campaign: %s", campaign.id)
        return serialize_campaign_response(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching campaign: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Start a campaign with comprehensive validation"""
    logger.debug("Starting campaign with id=%s", campaign_id)
    
    try:
        # Validate UUID format
        try:
            campaign_uuid = UUID(campaign_id)
        except ValueError:
            logger.error("Invalid UUID format: %s", campaign_id)
            raise HTTPException(status_code=400, detail="Invalid campaign_id format")
        
        # Get campaign with template
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == campaign_uuid
        ).first()
        
        if not campaign:
            logger.error("Campaign not found: %s", campaign_id)
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Check campaign status
        if campaign.status != CampaignStatus.DRAFT:
            logger.error("Campaign not in draft status: %s", campaign.status)
            raise HTTPException(
                status_code=400, 
                detail=f"Campaign is in {campaign.status.value} status, only DRAFT campaigns can be started"
            )
        
        # Verify template exists and is active
        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == campaign.template_id,
            MessageTemplate.is_active == True
        ).first()
        
        if not template:
            logger.error("Template not found or inactive for campaign: %s", campaign_id)
            raise HTTPException(
                status_code=404, 
                detail="Template not found or is inactive"
            )
        
        # Get qualified prospects
        query = db.query(AffiliateProspect).filter(
            AffiliateProspect.consent_given == True
        )
        
        # Apply target criteria filtering
        if campaign.target_criteria:
            if min_score := campaign.target_criteria.get("min_score"):
                query = query.filter(AffiliateProspect.qualification_score >= min_score)
            
            # Add other criteria filters as needed
            if industry := campaign.target_criteria.get("industry"):
                # Assuming you have an industry field or it's in a JSON field
                pass  # Implement industry filtering if needed
        
        prospects = query.all()
        logger.debug("Found %d qualified prospects", len(prospects))
        
        if not prospects:
            logger.error("No qualified prospects found for campaign: %s", campaign_id)
            raise HTTPException(
                status_code=400, 
                detail="No qualified prospects found matching campaign criteria"
            )
        
        # Update campaign status
        campaign.status = CampaignStatus.ACTIVE
        
        try:
            db.commit()
            db.refresh(campaign)
        except IntegrityError as e:
            db.rollback()
            logger.error("Database error updating campaign status: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Failed to update campaign status"
            )
        
        logger.info("Updated campaign status to ACTIVE: %s", campaign_id)
        
        # Start sequence for each qualified prospect
        for prospect in prospects:
            logger.debug("Triggering sequence step for prospect: %s", prospect.id)
            try:
                process_sequence_step.delay(str(prospect.id), str(campaign_id))
            except Exception as e:
                logger.warning("Failed to queue sequence task for prospect %s: %s", prospect.id, e)
                # Continue with other prospects even if one fails
        
        return serialize_campaign_response(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error starting campaign: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Pause an active campaign"""
    logger.debug("Pausing campaign with id=%s", campaign_id)
    
    try:
        campaign_uuid = UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign_id format")
    
    campaign = db.query(OutreachCampaign).filter(
        OutreachCampaign.id == campaign_uuid
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Only ACTIVE campaigns can be paused, current status: {campaign.status.value}"
        )
    
    campaign.status = CampaignStatus.PAUSED
    db.commit()
    db.refresh(campaign)
    
    return serialize_campaign_response(campaign)

@router.post("/{campaign_id}/resume")
async def resume_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Resume a paused campaign"""
    logger.debug("Resuming campaign with id=%s", campaign_id)
    
    try:
        campaign_uuid = UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign_id format")
    
    campaign = db.query(OutreachCampaign).filter(
        OutreachCampaign.id == campaign_uuid
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.PAUSED:
        raise HTTPException(
            status_code=400,
            detail=f"Only PAUSED campaigns can be resumed, current status: {campaign.status.value}"
        )
    
    campaign.status = CampaignStatus.ACTIVE
    db.commit()
    db.refresh(campaign)
    
    return serialize_campaign_response(campaign)