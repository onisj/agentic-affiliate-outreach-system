from app.services.cache import cache_result
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from database.models import MessageLog, OutreachCampaign, CampaignStatus, MessageStatus, CampaignResponse
from database.session import get_db
from sqlalchemy import case
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.cache import cache
import logging
import aiohttp
from sqlalchemy import JSON

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache warming functions
async def warm_campaign_list():
    """Warm cache with list of all campaigns."""
    db = next(get_db())
    try:
        campaigns = db.query(Campaign).all()
        return [campaign.to_dict() for campaign in campaigns]
    except Exception as e:
        logger.error(f"Error warming campaign list cache: {e}")
        return None

async def warm_campaign_stats():
    """Warm cache with campaign statistics."""
    db = next(get_db())
    try:
        stats = {}
        campaigns = db.query(Campaign).all()
        for campaign in campaigns:
            stats[campaign.id] = {
                'total_messages': db.query(func.count(MessageLog.id))
                    .filter(MessageLog.campaign_id == campaign.id)
                    .scalar(),
                'sent_messages': db.query(func.count(MessageLog.id))
                    .filter(MessageLog.campaign_id == campaign.id)
                    .filter(MessageLog.status == 'sent')
                    .scalar(),
                'opened_messages': db.query(func.count(MessageLog.id))
                    .filter(MessageLog.campaign_id == campaign.id)
                    .filter(MessageLog.status == 'opened')
                    .scalar(),
                'clicked_messages': db.query(func.count(MessageLog.id))
                    .filter(MessageLog.campaign_id == campaign.id)
                    .filter(MessageLog.status == 'clicked')
                    .scalar()
            }
        return stats
    except Exception as e:
        logger.error(f"Error warming campaign stats cache: {e}")
        return None

# Start cache warming
cache.warmer.start_warming("campaigns:list", warm_campaign_list, ttl=300, interval=240)  # 5 min TTL, 4 min interval
cache.warmer.start_warming("campaigns:stats", warm_campaign_stats, ttl=300, interval=240)

@router.get("/campaigns", response_model=List[CampaignResponse])
@cache_result(ttl=300, key_prefix="campaigns_list")  # Cache for 5 minutes
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    status: Optional[CampaignStatus] = None,
    db: Session = Depends(get_db)
):
    """List all campaigns with optional status filter."""
    query = db.query(OutreachCampaign)
    if status:
        query = query.filter(OutreachCampaign.status == status)
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
@cache_result(ttl=600, key_prefix="campaign_detail")  # Cache for 10 minutes
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """Get campaign details by ID."""
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
@cache_result(ttl=300, key_prefix="campaign_stats")  # Cache for 5 minutes
async def get_campaign_stats(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """Get campaign statistics."""
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Calculate stats using optimized queries
    stats = db.query(
        func.count(MessageLog.id).label('total_messages'),
        func.sum(case((MessageLog.status == MessageStatus.OPENED, 1), else_=0)).label('opens'),
        func.sum(case((MessageLog.status == MessageStatus.CLICKED, 1), else_=0)).label('clicks'),
        func.sum(case((MessageLog.status == MessageStatus.REPLIED, 1), else_=0)).label('replies')
    ).filter(
        MessageLog.campaign_id == campaign_id
    ).first()
    
    return {
        "campaign_id": campaign_id,
        "total_messages": stats.total_messages or 0,
        "opens": stats.opens or 0,
        "clicks": stats.clicks or 0,
        "replies": stats.replies or 0,
        "open_rate": (stats.opens or 0) / (stats.total_messages or 1) * 100,
        "click_rate": (stats.clicks or 0) / (stats.total_messages or 1) * 100,
        "reply_rate": (stats.replies or 0) / (stats.total_messages or 1) * 100
    }

@router.post("/campaigns/", response_model=dict)
@cache.invalidate_on_update("campaigns:*")
async def create_campaign(
    campaign: dict,
    db: Session = Depends(get_db)
):
    """Create a new campaign."""
    new_campaign = Campaign(**campaign)
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign.to_dict()

@router.put("/campaigns/{campaign_id}", response_model=dict)
@cache.invalidate_on_update("campaigns:*")
async def update_campaign(
    campaign_id: str,
    campaign: dict,
    db: Session = Depends(get_db)
):
    """Update an existing campaign."""
    existing_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not existing_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    for key, value in campaign.items():
        setattr(existing_campaign, key, value)
    
    db.commit()
    db.refresh(existing_campaign)
    return existing_campaign.to_dict()

@router.delete("/campaigns/{campaign_id}")
@cache.invalidate_on_update("campaigns:*")
async def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """Delete a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted successfully"}

async def send_linkedin_message(access_token, recipient_urn, subject, content):
    url = "https://api.linkedin.com/v2/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "recipients": {
            "values": [recipient_urn]
        },
        "subject": subject,
        "body": content
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            return await resp.json()

async def send_twitter_dm(bearer_token, recipient_id, text):
    url = "https://api.twitter.com/2/dm_events"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    data = {
        "event": {
            "type": "message_create",
            "message_create": {
                "target": {"recipient_id": recipient_id},
                "message_data": {"text": text}
            }
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            return await resp.json() 