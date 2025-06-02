from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import OutreachCampaign, AffiliateProspect, MessageTemplate, CampaignStatus
from api.schemas.campaign import CampaignCreate, CampaignResponse
from tasks.sequence_tasks import process_sequence_step
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.post("/", response_model=CampaignResponse)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    template = db.query(MessageTemplate).filter(MessageTemplate.id == campaign.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_campaign = OutreachCampaign(
        id=uuid4(),
        name=campaign.name,
        template_id=campaign.template_id,
        target_criteria=campaign.target_criteria,
        status=CampaignStatus.DRAFT,
        created_at=datetime.utcnow()
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/", response_model=list[CampaignResponse])
def get_campaigns(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    campaigns = db.query(OutreachCampaign).offset(skip).limit(limit).all()
    return campaigns

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.post("/{campaign_id}/start")
def start_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Campaign not in draft status")
    
    template = db.query(MessageTemplate).filter(MessageTemplate.id == campaign.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get qualified prospects
    query = db.query(AffiliateProspect).filter(AffiliateProspect.consent_given == True)
    if campaign.target_criteria:
        if min_score := campaign.target_criteria.get("min_score"):
            query = query.filter(AffiliateProspect.qualification_score >= min_score)
    
    prospects = query.all()
    if not prospects:
        raise HTTPException(status_code=400, detail="No qualified prospects found")
    
    # Update campaign status
    campaign.status = CampaignStatus.ACTIVE
    campaign.updated_at = datetime.utcnow()
    db.commit()
    
    # Start sequence for each prospect
    for prospect in prospects:
        process_sequence_step.delay(str(prospect.id), str(campaign_id))
    
    return {"message": "Campaign started successfully"}