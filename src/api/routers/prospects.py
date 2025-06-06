from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database.session import get_db 
from database.models import AffiliateProspect, ProspectStatus
from api.schemas.prospect import ProspectCreate, ProspectResponse
from app.tasks.scoring_tasks import score_prospect
import uuid
from uuid import UUID
from datetime import datetime, timezone

router = APIRouter(tags=["prospects"])

@router.post("/", response_model=ProspectResponse, status_code=201)
def create_prospect(prospect: ProspectCreate, db: Session = Depends(get_db)):
    """Create a new affiliate prospect"""
    existing = db.query(AffiliateProspect).filter(
        AffiliateProspect.email == prospect.email
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Prospect with this email already exists"
        )
    
    db_prospect = AffiliateProspect(
        id=UUID(str(uuid.uuid4())),
        email=prospect.email,
        first_name=prospect.first_name,
        last_name=prospect.last_name,
        company=prospect.company,
        website=prospect.website,
        social_profiles=prospect.social_profiles,
        lead_source=prospect.lead_source,
        consent_given=prospect.consent_given,
        consent_timestamp=datetime.now(timezone.utc) if prospect.consent_given else None,
        status=ProspectStatus.NEW
    )
    
    db.add(db_prospect)
    db.commit()
    db.refresh(db_prospect)
    
    # Queue scoring task
    score_prospect.delay(str(db_prospect.id))
    
    return db_prospect

@router.get("/", response_model=List[ProspectResponse])
def get_prospects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of prospects with optional status filter"""
    query = db.query(AffiliateProspect)
    
    if status:
        try:
            query = query.filter(AffiliateProspect.status == ProspectStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
    
    prospects = query.offset(skip).limit(limit).all()
    return prospects

@router.get("/{prospect_id}", response_model=ProspectResponse)
def get_prospect(prospect_id: str, db: Session = Depends(get_db)):
    """Get specific prospect by ID"""
    try:
        prospect = db.query(AffiliateProspect).filter(
            AffiliateProspect.id == UUID(prospect_id)
        ).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format")
    
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    return prospect

@router.put("/{prospect_id}/consent")
def update_consent(prospect_id: str, consent_given: bool, db: Session = Depends(get_db)):
    """Update prospect's consent status"""
    try:
        prospect = db.query(AffiliateProspect).filter(
            AffiliateProspect.id == UUID(prospect_id)
        ).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format")
    
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    prospect.consent_given = consent_given
    prospect.consent_timestamp = datetime.now(timezone.utc) if consent_given else None
    db.commit()
    db.refresh(prospect)
    
    return {"message": f"Consent updated to {consent_given} for prospect {prospect_id}"}

@router.post("/bulk-update")
def bulk_update_prospects(
    prospect_ids: List[str],
    status: Optional[str] = None,
    consent_given: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Bulk update prospect status or consent"""
    try:
        prospects = db.query(AffiliateProspect).filter(
            AffiliateProspect.id.in_([UUID(pid) for pid in prospect_ids])
        ).all()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format")
    
    if not prospects:
        raise HTTPException(status_code=404, detail="No prospects found")
    
    updated_count = 0
    for prospect in prospects:
        if status:
            try:
                prospect.status = ProspectStatus(status)
                updated_count += 1
            except ValueError:
                continue
        if consent_given is not None:
            prospect.consent_given = consent_given
            prospect.consent_timestamp = datetime.now(timezone.utc) if consent_given else None
            updated_count += 1
    
    db.commit()
    
    return {"message": f"Updated {updated_count} prospects"}

@router.delete("/{prospect_id}/unsubscribe")
async def unsubscribe_prospect(prospect_id: str, db: Session = Depends(get_db)):
    try:
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == UUID(prospect_id)).first()
        if not prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")
        prospect.consent_given = False
        prospect.consent_timestamp = None
        prospect.status = ProspectStatus.DECLINED
        db.commit()
        return {"message": "Prospect unsubscribed successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format")