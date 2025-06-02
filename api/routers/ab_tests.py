from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import ABTest, OutreachCampaign
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/ab-tests", tags=["ab-tests"])

@router.post("/")
def create_ab_test(campaign_id: str, name: str, variants: List[Dict[str, Any]], db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    ab_test = ABTest(
        id=uuid4(),
        campaign_id=campaign_id,
        name=name,
        variants=variants,  # e.g., [{"variant_id": "A", "template_id": "uuid"}, {"variant_id": "B", "template_id": "uuid"}]
        created_at=datetime.utcnow()
    )
    
    db.add(ab_test)
    db.commit()
    db.refresh(ab_test)
    return ab_test

@router.get("/{ab_test_id}")
def get_ab_test(ab_test_id: str, db: Session = Depends(get_db)):
    ab_test = db.query(ABTest).filter(ABTest.id == ab_test_id).first()
    if not ab_test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return ab_test