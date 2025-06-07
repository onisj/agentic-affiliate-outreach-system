"""
Campaign Management Endpoints

This module provides endpoints for managing outreach campaigns.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from database.models import User, Campaign, CampaignStatus
from services.outreach.campaign_orchestrator import CampaignOrchestrator
from api.dependencies.auth import get_current_user

router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str]
    target_audience: List[str]
    channels: List[str]
    start_date: datetime
    end_date: Optional[datetime]
    message_template: str
    max_daily_messages: int = 100

class CampaignUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    target_audience: Optional[List[str]]
    channels: Optional[List[str]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    message_template: Optional[str]
    max_daily_messages: Optional[int]
    status: Optional[CampaignStatus]

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_audience: List[str]
    channels: List[str]
    start_date: datetime
    end_date: Optional[datetime]
    message_template: str
    max_daily_messages: int
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime
    created_by: int

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign"""
    try:
        campaign_data = campaign.dict()
        campaign_data["created_by"] = current_user.id
        campaign_data["status"] = CampaignStatus.DRAFT
        
        new_campaign = await Campaign.create(**campaign_data)
        return new_campaign
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """List all campaigns"""
    try:
        campaigns = await Campaign.get_all(status=status)
        return campaigns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get campaign details"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        return campaign
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update campaign details"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        update_data = campaign_update.dict(exclude_unset=True)
        updated_campaign = await campaign.update(**update_data)
        return updated_campaign
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user)
):
    """Start a campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign.status != CampaignStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign can only be started from DRAFT status"
            )
        
        orchestrator = CampaignOrchestrator(campaign)
        await orchestrator.start()
        
        return {"message": "Campaign started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user)
):
    """Pause a campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign.status != CampaignStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign can only be paused from ACTIVE status"
            )
        
        orchestrator = CampaignOrchestrator(campaign)
        await orchestrator.pause()
        
        return {"message": "Campaign paused successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user)
):
    """Resume a paused campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign.status != CampaignStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign can only be resumed from PAUSED status"
            )
        
        orchestrator = CampaignOrchestrator(campaign)
        await orchestrator.resume()
        
        return {"message": "Campaign resumed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{campaign_id}/stop")
async def stop_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user)
):
    """Stop a campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign.status not in [CampaignStatus.ACTIVE, CampaignStatus.PAUSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign can only be stopped from ACTIVE or PAUSED status"
            )
        
        orchestrator = CampaignOrchestrator(campaign)
        await orchestrator.stop()
        
        return {"message": "Campaign stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 