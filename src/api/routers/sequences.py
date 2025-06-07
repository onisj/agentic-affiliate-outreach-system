from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.session import get_db
from database.models import Sequence, OutreachCampaign, MessageTemplate, CampaignStatus
from api.schemas.sequence import SequenceCreate, SequenceUpdate, SequenceResponse
from uuid import UUID
import logging
from datetime import datetime, timezone
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sequences", tags=["sequences"])

@router.post("/", response_model=SequenceResponse)
def create_sequence(sequence: SequenceCreate, db: Session = Depends(get_db)):
    """
    Create a new sequence step for a campaign.
    
    Args:
        sequence: Sequence creation data
        db: Database session
    
    Returns:
        Created sequence data
    """
    logger.debug("Creating sequence with data: %s", sequence.model_dump())
    
    try:
        # Validate campaign
        campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == sequence.campaign_id).first()
        if not campaign:
            logger.error("Campaign not found: %s", sequence.campaign_id)
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Validate template
        template = db.query(MessageTemplate).filter(MessageTemplate.id == sequence.template_id).first()
        if not template:
            logger.error("Template not found: %s", sequence.template_id)
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check for duplicate step
        existing = db.query(Sequence).filter(
            Sequence.campaign_id == sequence.campaign_id,
            Sequence.step_number == sequence.step_number
        ).first()
        if existing:
            logger.error("Step number %d already exists for campaign %s", 
                        sequence.step_number, sequence.campaign_id)
            raise HTTPException(
                status_code=400, 
                detail="Step number already exists for this campaign"
            )
        
        # Create sequence
        db_sequence = Sequence(
            campaign_id=sequence.campaign_id,
            step_number=sequence.step_number,
            template_id=sequence.template_id,
            delay_days=sequence.delay_days,
            condition=sequence.condition,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(db_sequence)
        try:
            db.commit()
            db.refresh(db_sequence)
        except IntegrityError as e:
            db.rollback()
            logger.error("Database integrity error creating sequence: %s", e)
            raise HTTPException(
                status_code=400,
                detail="Failed to create sequence due to data integrity constraints"
            )
        
        logger.info("Created sequence: %s", db_sequence.id)
        return db_sequence
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error creating sequence: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{sequence_id}", response_model=SequenceResponse)
def get_sequence(sequence_id: str, db: Session = Depends(get_db)):
    """
    Get a sequence by ID.
    
    Args:
        sequence_id: UUID of the sequence
        db: Database session
    
    Returns:
        Sequence data
    """
    logger.debug("Fetching sequence: %s", sequence_id)
    
    try:
        try:
            sequence_uuid = UUID(sequence_id)
        except ValueError:
            logger.error("Invalid UUID format: %s", sequence_id)
            raise HTTPException(status_code=400, detail="Invalid sequence_id format")
            
        sequence = db.query(Sequence).filter(Sequence.id == sequence_uuid).first()
        if not sequence:
            logger.error("Sequence not found: %s", sequence_id)
            raise HTTPException(status_code=404, detail="Sequence not found")
            
        return sequence
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching sequence: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{sequence_id}", response_model=SequenceResponse)
def update_sequence(
    sequence_id: str,
    sequence_update: SequenceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a sequence step.
    
    Args:
        sequence_id: UUID of the sequence to update
        sequence_update: Updated sequence data
        db: Database session
    
    Returns:
        Updated sequence data
    """
    logger.debug("Updating sequence %s with data: %s", sequence_id, sequence_update.model_dump())
    
    try:
        try:
            sequence_uuid = UUID(sequence_id)
        except ValueError:
            logger.error("Invalid UUID format: %s", sequence_id)
            raise HTTPException(status_code=400, detail="Invalid sequence_id format")
            
        # Get sequence
        sequence = db.query(Sequence).filter(Sequence.id == sequence_uuid).first()
        if not sequence:
            logger.error("Sequence not found: %s", sequence_id)
            raise HTTPException(status_code=404, detail="Sequence not found")
            
        # Check campaign status
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == sequence.campaign_id
        ).first()
        if campaign.status != CampaignStatus.DRAFT:
            logger.error("Cannot update sequence for non-draft campaign: %s", campaign.status)
            raise HTTPException(
                status_code=400,
                detail="Sequence can only be updated for campaigns in DRAFT status"
            )
            
        # Validate template if provided
        if sequence_update.template_id:
            template = db.query(MessageTemplate).filter(
                MessageTemplate.id == sequence_update.template_id
            ).first()
            if not template:
                logger.error("Template not found: %s", sequence_update.template_id)
                raise HTTPException(status_code=404, detail="Template not found")
                
        # Check for duplicate step number if changing
        if sequence_update.step_number and sequence_update.step_number != sequence.step_number:
            existing = db.query(Sequence).filter(
                Sequence.campaign_id == sequence.campaign_id,
                Sequence.step_number == sequence_update.step_number,
                Sequence.id != sequence_uuid
            ).first()
            if existing:
                logger.error("Step number %d already exists for campaign %s",
                            sequence_update.step_number, sequence.campaign_id)
                raise HTTPException(
                    status_code=400,
                    detail="Step number already exists for this campaign"
                )
                
        # Update sequence
        for field, value in sequence_update.model_dump(exclude_unset=True).items():
            setattr(sequence, field, value)
            
        try:
            db.commit()
            db.refresh(sequence)
        except IntegrityError as e:
            db.rollback()
            logger.error("Database integrity error updating sequence: %s", e)
            raise HTTPException(
                status_code=400,
                detail="Failed to update sequence due to data integrity constraints"
            )
            
        logger.info("Updated sequence: %s", sequence.id)
        return sequence
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error updating sequence: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sequence(sequence_id: str, db: Session = Depends(get_db)):
    """
    Delete a sequence step.
    
    Args:
        sequence_id: UUID of the sequence to delete
        db: Database session
    """
    logger.debug("Deleting sequence: %s", sequence_id)
    
    try:
        try:
            sequence_uuid = UUID(sequence_id)
        except ValueError:
            logger.error("Invalid UUID format: %s", sequence_id)
            raise HTTPException(status_code=400, detail="Invalid sequence_id format")
            
        # Get sequence
        sequence = db.query(Sequence).filter(Sequence.id == sequence_uuid).first()
        if not sequence:
            logger.error("Sequence not found: %s", sequence_id)
            raise HTTPException(status_code=404, detail="Sequence not found")
            
        # Check campaign status
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == sequence.campaign_id
        ).first()
        if campaign.status != CampaignStatus.DRAFT:
            logger.error("Cannot delete sequence for non-draft campaign: %s", campaign.status)
            raise HTTPException(
                status_code=400,
                detail="Sequence can only be deleted for campaigns in DRAFT status"
            )
            
        # Delete sequence
        db.delete(sequence)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            logger.error("Database integrity error deleting sequence: %s", e)
            raise HTTPException(
                status_code=400,
                detail="Failed to delete sequence due to data integrity constraints"
            )
            
        logger.info("Deleted sequence: %s", sequence_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error deleting sequence: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

