"""
Analytics Endpoints

This module provides endpoints for accessing campaign and channel analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.models import User, Campaign, MessageLog
from services.analytics import AnalyticsService
from api.dependencies.auth import get_current_user

router = APIRouter()

class AnalyticsTimeRange(BaseModel):
    start_date: datetime
    end_date: datetime

class CampaignMetrics(BaseModel):
    total_messages: int
    successful_messages: int
    failed_messages: int
    response_rate: float
    engagement_rate: float
    conversion_rate: float

class ChannelMetrics(BaseModel):
    channel: str
    total_messages: int
    successful_messages: int
    failed_messages: int
    response_rate: float
    engagement_rate: float
    conversion_rate: float

class AudienceMetrics(BaseModel):
    total_audience: int
    active_audience: int
    new_audience: int
    churned_audience: int
    engagement_rate: float

@router.get("/campaigns/{campaign_id}/metrics", response_model=CampaignMetrics)
async def get_campaign_metrics(
    campaign_id: int,
    time_range: AnalyticsTimeRange,
    current_user: User = Depends(get_current_user)
):
    """Get metrics for a specific campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        analytics_service = AnalyticsService()
        metrics = await analytics_service.get_campaign_metrics(
            campaign_id=campaign_id,
            start_date=time_range.start_date,
            end_date=time_range.end_date
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/channels/metrics", response_model=List[ChannelMetrics])
async def get_channel_metrics(
    time_range: AnalyticsTimeRange,
    current_user: User = Depends(get_current_user)
):
    """Get metrics for all channels"""
    try:
        analytics_service = AnalyticsService()
        metrics = await analytics_service.get_channel_metrics(
            start_date=time_range.start_date,
            end_date=time_range.end_date
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/audience/metrics", response_model=AudienceMetrics)
async def get_audience_metrics(
    time_range: AnalyticsTimeRange,
    current_user: User = Depends(get_current_user)
):
    """Get audience metrics"""
    try:
        analytics_service = AnalyticsService()
        metrics = await analytics_service.get_audience_metrics(
            start_date=time_range.start_date,
            end_date=time_range.end_date
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/campaigns/{campaign_id}/message-logs")
async def get_campaign_message_logs(
    campaign_id: int,
    time_range: AnalyticsTimeRange,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get message logs for a campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        analytics_service = AnalyticsService()
        logs = await analytics_service.get_message_logs(
            campaign_id=campaign_id,
            start_date=time_range.start_date,
            end_date=time_range.end_date,
            status=status,
            channel=channel
        )
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/campaigns/{campaign_id}/response-analysis")
async def get_campaign_response_analysis(
    campaign_id: int,
    time_range: AnalyticsTimeRange,
    current_user: User = Depends(get_current_user)
):
    """Get response analysis for a campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        analytics_service = AnalyticsService()
        analysis = await analytics_service.get_response_analysis(
            campaign_id=campaign_id,
            start_date=time_range.start_date,
            end_date=time_range.end_date
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/campaigns/{campaign_id}/sentiment-analysis")
async def get_campaign_sentiment_analysis(
    campaign_id: int,
    time_range: AnalyticsTimeRange,
    current_user: User = Depends(get_current_user)
):
    """Get sentiment analysis for a campaign"""
    try:
        campaign = await Campaign.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        analytics_service = AnalyticsService()
        analysis = await analytics_service.get_sentiment_analysis(
            campaign_id=campaign_id,
            start_date=time_range.start_date,
            end_date=time_range.end_date
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 