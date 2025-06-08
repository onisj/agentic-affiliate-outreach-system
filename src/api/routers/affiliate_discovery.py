from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database.session import get_db
from services.affiliate_discovery import AffiliateDiscoveryService
from database.models import AffiliateStatus
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class SearchCriteria(BaseModel):
    """Search criteria for discovering affiliates."""
    keywords: List[str]
    location: str
    min_followers: int = 0
    max_followers: int = None
    industry: str = None
    additional_filters: Dict[str, Any] = None

class AffiliateResponse(BaseModel):
    """Response model for affiliate data."""
    id: str
    name: str
    platform: str
    status: AffiliateStatus
    contact_info: Dict[str, Any]
    discovered_at: datetime
    last_updated: datetime

@router.post("/discover/{platform}", response_model=List[AffiliateResponse])
async def discover_affiliates(
    platform: str,
    search_criteria: SearchCriteria,
    db: Session = Depends(get_db)
):
    """Discover potential affiliates on a specific platform."""
    service = AffiliateDiscoveryService(db)
    try:
        affiliates = await service.discover_affiliates(
            platform=platform,
            search_criteria=search_criteria.dict()
        )
        return affiliates
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()

@router.get("/affiliate/{affiliate_id}", response_model=AffiliateResponse)
async def get_affiliate(
    affiliate_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific affiliate."""
    service = AffiliateDiscoveryService(db)
    try:
        affiliate = await service.get_affiliate(affiliate_id)
        if not affiliate:
            raise HTTPException(status_code=404, detail="Affiliate not found")
        return affiliate
    finally:
        await service.close()

@router.put("/affiliate/{affiliate_id}/status")
async def update_affiliate_status(
    affiliate_id: str,
    status: AffiliateStatus,
    notes: str = None,
    db: Session = Depends(get_db)
):
    """Update the status of an affiliate."""
    service = AffiliateDiscoveryService(db)
    try:
        success = await service.update_affiliate_status(
            affiliate_id=affiliate_id,
            status=status,
            notes=notes
        )
        if not success:
            raise HTTPException(status_code=404, detail="Affiliate not found")
        return {"message": "Status updated successfully"}
    finally:
        await service.close()

@router.get("/metrics")
async def get_discovery_metrics(db: Session = Depends(get_db)):
    """Get metrics about the discovery process."""
    service = AffiliateDiscoveryService(db)
    try:
        return await service.get_discovery_metrics()
    finally:
        await service.close() 