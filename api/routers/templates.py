from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import uuid
from datetime import datetime, timezone
from database.models import MessageTemplate, MessageType
from api.schemas.template import TemplateCreate, TemplateResponse
from database.session import get_db

router = APIRouter(tags=["templates"])

@router.post("/", response_model=TemplateResponse, status_code=201)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new message template."""
    try:
        message_type = MessageType(template.message_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message type. Must be 'email', 'linkedin', or 'twitter'")

    now = datetime.now(timezone.utc)
    db_template = MessageTemplate(
        id=UUID(str(uuid.uuid4())),
        name=template.name,
        subject=template.subject,
        content=template.content,
        message_type=message_type,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/", response_model=List[TemplateResponse])
def get_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of templates."""
    templates = db.query(MessageTemplate).filter(MessageTemplate.is_active == True).offset(skip).limit(limit).all()
    return templates

@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a specific template by ID."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: UUID, template_update: TemplateCreate, db: Session = Depends(get_db)):
    """Update a template's details."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        message_type = MessageType(template_update.message_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message type. Must be 'email', 'linkedin', or 'twitter'")

    template.name = template_update.name
    template.subject = template_update.subject
    template.content = template_update.content
    template.message_type = message_type
    template.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(template)
    return template

@router.delete("/{template_id}")
def delete_template(template_id: UUID, db: Session = Depends(get_db)):
    """Deactivate a template (soft delete)."""
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_active = False
    template.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Template deactivated successfully"}