from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.session import get_db
from database.models import OutreachCampaign, AffiliateProspect, MessageTemplate, CampaignStatus
from api.schemas.campaigns import CampaignCreate
from app.tasks.sequence_tasks import process_sequence_step
from uuid import UUID
import logging
from typing import List
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from pydantic import ValidationError
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi import FastAPI

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["campaigns"])

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
        # Check if template exists and is active
        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == campaign.template_id,
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
            template_id=campaign.template_id,
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
async def get_campaigns(
    db: Session = Depends(get_db), 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=0)
):
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
    logger.debug("Fetching campaign with id=%s", campaign_id)
    try:
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
    logger.debug("Starting campaign with id=%s", campaign_id)
    try:
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
        if campaign.status != CampaignStatus.DRAFT:
            logger.error("Campaign not in draft status: %s", campaign.status)
            raise HTTPException(
                status_code=400,
                detail=f"Campaign is in {campaign.status.name.upper()} status, only DRAFT campaigns can be started"
            )
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
        query = db.query(AffiliateProspect).filter(
            AffiliateProspect.consent_given == True
        )
        if campaign.target_criteria:
            if min_score := campaign.target_criteria.get("min_score"):
                query = query.filter(AffiliateProspect.qualification_score >= min_score)
            if industry := campaign.target_criteria.get("industry"):
                pass
        prospects = query.all()
        logger.debug("Found %d qualified prospects", len(prospects))
        if not prospects:
            logger.error("No qualified prospects found for campaign: %s", campaign_id)
            raise HTTPException(
                status_code=400,
                detail="No qualified prospects found for this campaign"
            )
        campaign.status = CampaignStatus.ACTIVE
        db.commit()
        try:
            for prospect in prospects:
                process_sequence_step.delay(str(prospect.id), str(campaign.id))
        except Exception as e:
            logger.error("Error queueing sequence tasks: %s", e)
        return serialize_campaign_response(campaign)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting campaign: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, db: Session = Depends(get_db)):
    logger.debug("Pausing campaign with id=%s", campaign_id)
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error pausing campaign: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{campaign_id}/resume")
async def resume_campaign(campaign_id: str, db: Session = Depends(get_db)):
    logger.debug("Resuming campaign with id=%s", campaign_id)
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resuming campaign: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=fastapi_status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )