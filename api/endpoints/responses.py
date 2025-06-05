from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from database.session import get_db
from services.response_tracking import ResponseTrackingService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class MessageOpen(BaseModel):
    """Schema for tracking message opens."""
    external_message_id: Optional[str] = None

class MessageClick(BaseModel):
    """Schema for tracking message clicks."""
    click_url: str

class MessageReply(BaseModel):
    """Schema for tracking message replies."""
    reply_content: str
    external_message_id: Optional[str] = None

@router.post("/messages/{message_id}/open")
async def track_message_open(
    message_id: str,
    data: MessageOpen,
    db: Session = Depends(get_db)
):
    """Track when a message is opened."""
    service = ResponseTrackingService(db)
    result = await service.track_message_open(
        message_id=message_id,
        external_message_id=data.external_message_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/messages/{message_id}/click")
async def track_message_click(
    message_id: str,
    data: MessageClick,
    db: Session = Depends(get_db)
):
    """Track when a message link is clicked."""
    service = ResponseTrackingService(db)
    result = await service.track_message_click(
        message_id=message_id,
        click_url=data.click_url
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/messages/{message_id}/reply")
async def track_message_reply(
    message_id: str,
    data: MessageReply,
    db: Session = Depends(get_db)
):
    """Track and analyze a message reply."""
    service = ResponseTrackingService(db)
    result = await service.track_message_reply(
        message_id=message_id,
        reply_content=data.reply_content,
        external_message_id=data.external_message_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/analytics")
async def get_response_analytics(
    campaign_id: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get comprehensive response analytics."""
    service = ResponseTrackingService(db)
    result = await service.get_response_analytics(
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date
    )
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result["error"])
    return result 