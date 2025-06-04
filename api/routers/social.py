from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import AffiliateProspect, MessageTemplate
from services.social_service import SocialService
from typing import Dict, Any

router = APIRouter(prefix="/social", tags=["social"])

@router.post("/twitter/{prospect_id}")
def send_twitter_message(prospect_id: str, template_id: str, db: Session = Depends(get_db)):
    """Send a Twitter DM to a prospect"""
    social_service = SocialService()
    
    prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template or template.message_type != "twitter":
        raise HTTPException(status_code=404, detail="Valid Twitter template not found")
    
    if not prospect.consent_given:
        raise HTTPException(status_code=400, detail="Prospect has not given consent")
    
    twitter_id = prospect.social_profiles.get('twitter', {}).get('user_id')
    if not twitter_id:
        raise HTTPException(status_code=400, detail="Twitter user ID not found")
    
    prospect_data = {
        'first_name': prospect.first_name,
        'last_name': prospect.last_name,
        'company': prospect.company,
        'email': prospect.email
    }
    
    result = social_service.send_twitter_dm(prospect_id, twitter_id, template.content, 
                                          prospect_data, db=db)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return {"message_id": result['message_id'], "message": "Twitter DM sent successfully"}

@router.post("/linkedin/{prospect_id}")
def send_linkedin_message(prospect_id: str, template_id: str, db: Session = Depends(get_db)):
    """Send a LinkedIn message to a prospect"""
    social_service = SocialService()
    
    prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template or template.message_type != "linkedin":
        raise HTTPException(status_code=404, detail="Valid LinkedIn template not found")
    
    if not prospect.consent_given:
        raise HTTPException(status_code=400, detail="Prospect has not given consent")
    
    linkedin_urn = prospect.social_profiles.get('linkedin', {}).get('urn')
    if not linkedin_urn:
        raise HTTPException(status_code=400, detail="LinkedIn URN not found")
    
    prospect_data = {
        'first_name': prospect.first_name,
        'last_name': prospect.last_name,
        'company': prospect.company,
        'email': prospect.email
    }
    
    result = social_service.send_linkedin_message(prospect_id, linkedin_urn, template.content, 
                                                prospect_data, db=db)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return {"message_id": result['message_id'], "message": "LinkedIn message sent successfully"}