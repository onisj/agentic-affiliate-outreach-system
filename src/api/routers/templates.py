from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from database.models import MessageTemplate, MessageLog, MessageType
from database.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.cache import cache_result, cache
import logging
from app.services.messaging import MessagingService
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache warming functions
async def warm_template_list():
    """Warm cache with list of all templates."""
    db = next(get_db())
    try:
        templates = db.query(MessageTemplate).all()
        return [template.to_dict() for template in templates]
    except Exception as e:
        logger.error(f"Error warming template list cache: {e}")
        return None

async def warm_template_stats():
    """Warm cache with template usage statistics."""
    db = next(get_db())
    try:
        stats = {}
        templates = db.query(MessageTemplate).all()
        for template in templates:
            stats[template.id] = {
                'total_uses': db.query(func.count(MessageLog.id))
                    .filter(MessageLog.template_id == template.id)
                    .scalar(),
                'success_rate': db.query(
                    func.sum(case((MessageLog.status == 'sent', 1), else_=0)) * 100.0 /
                    func.count(MessageLog.id)
                ).filter(
                    MessageLog.template_id == template.id
                ).scalar() or 0
            }
        return stats
    except Exception as e:
        logger.error(f"Error warming template stats cache: {e}")
        return None

# Start cache warming
cache.warmer.start_warming("templates:list", warm_template_list, ttl=300, interval=240)  # 5 min TTL, 4 min interval
cache.warmer.start_warming("templates:stats", warm_template_stats, ttl=300, interval=240)

@router.get("/templates/", response_model=List[dict])
@cache_result(ttl=300, key_prefix="templates")
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all message templates."""
    templates = db.query(MessageTemplate).offset(skip).limit(limit).all()
    return [template.to_dict() for template in templates]

@router.get("/templates/{template_id}", response_model=dict)
@cache_result(ttl=600, key_prefix="templates")
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific template by ID."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()

@router.get("/templates/{template_id}/stats", response_model=dict)
@cache_result(ttl=300, key_prefix="templates")
async def get_template_stats(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific template."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    stats = {
        'total_uses': db.query(func.count(MessageLog.id))
            .filter(MessageLog.template_id == template_id)
            .scalar(),
        'success_rate': db.query(
            func.sum(case((MessageLog.status == 'sent', 1), else_=0)) * 100.0 /
            func.count(MessageLog.id)
        ).filter(
            MessageLog.template_id == template_id
        ).scalar() or 0
    }
    return stats

class TemplateCreate(BaseModel):
    """Schema for creating a message template."""
    name: str
    content: str
    message_type: MessageType
    subject: Optional[str] = None
    variables: Optional[List[str]] = None

class ABTestCreate(BaseModel):
    """Schema for creating an A/B test."""
    campaign_id: str
    name: str
    variants: List[Dict[str, Any]]

class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: str
    name: str
    message_type: MessageType
    created_at: str

class ABTestResponse(BaseModel):
    """Schema for A/B test response."""
    id: str
    name: str
    variants: List[Dict[str, Any]]

@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new message template."""
    service = MessagingService(db)
    try:
        return await service.create_template(
            name=template.name,
            content=template.content,
            message_type=template.message_type,
            subject=template.subject,
            variables=template.variables
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    ab_test: ABTestCreate,
    db: Session = Depends(get_db)
):
    """Create a new A/B test."""
    service = MessagingService(db)
    try:
        return await service.create_ab_test(
            campaign_id=ab_test.campaign_id,
            name=ab_test.name,
            variants=ab_test.variants
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/templates/{template_id}/personalize")
async def personalize_message(
    template_id: str,
    data: Dict[str, Any],
    ab_test_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get a personalized message from a template."""
    service = MessagingService(db)
    try:
        return await service.get_personalized_message(
            template_id=template_id,
            data=data,
            ab_test_id=ab_test_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ab-tests/{ab_test_id}/results")
async def update_ab_test_results(
    ab_test_id: str,
    variant_id: str,
    sent_count: int,
    open_rate: float,
    click_rate: float,
    reply_rate: float,
    db: Session = Depends(get_db)
):
    """Update A/B test results."""
    service = MessagingService(db)
    success = await service.update_ab_test_results(
        ab_test_id=ab_test_id,
        variant_id=variant_id,
        sent_count=sent_count,
        open_rate=open_rate,
        click_rate=click_rate,
        reply_rate=reply_rate
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update A/B test results")
    return {"message": "Results updated successfully"}

@router.put("/templates/{template_id}", response_model=dict)
@cache.invalidate_on_update("templates:*")
async def update_template(
    template_id: str,
    template: dict,
    db: Session = Depends(get_db)
):
    """Update an existing template."""
    existing_template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not existing_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template.items():
        setattr(existing_template, key, value)
    
    db.commit()
    db.refresh(existing_template)
    return existing_template.to_dict()

@router.delete("/templates/{template_id}")
@cache.invalidate_on_update("templates:*")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a template."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"} 