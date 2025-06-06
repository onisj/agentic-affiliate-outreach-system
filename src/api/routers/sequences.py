from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Sequence, OutreachCampaign, MessageTemplate
from api.schemas.sequence import SequenceCreate, SequenceResponse
from uuid import uuid4
from datetime import datetime, timezone

router = APIRouter(prefix="/sequences", tags=["sequences"])

@router.post("/", response_model=SequenceResponse)
def create_sequence(sequence: SequenceCreate, db: Session = Depends(get_db)):
    # Validate campaign
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == sequence.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Validate template
    template = db.query(MessageTemplate).filter(MessageTemplate.id == sequence.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check for duplicate step
    existing = db.query(Sequence).filter(
        Sequence.campaign_id == sequence.campaign_id,
        Sequence.step_number == sequence.step_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Step number already exists for this campaign")
    
    db_sequence = Sequence(
        id=uuid4(),
        campaign_id=sequence.campaign_id,
        step_number=sequence.step_number,
        template_id=sequence.template_id,
        delay_days=sequence.delay_days,
        condition=sequence.condition,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_sequence)
    db.commit()
    db.refresh(db_sequence)
    return db_sequence

@router.get("/{sequence_id}", response_model=SequenceResponse)
def get_sequence(sequence_id: str, db: Session = Depends(get_db)):
    sequence = db.query(Sequence).filter(Sequence.id == sequence_id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return sequence