"""
Message Template Endpoints

This module provides endpoints for managing message templates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, MessageTemplate, TemplateType
from services.outreach.templates import MessageTemplates
from api.dependencies.auth import get_current_user

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str]
    content: str
    type: TemplateType
    variables: List[str]
    channel: str
    is_active: bool = True

class TemplateUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    content: Optional[str]
    type: Optional[TemplateType]
    variables: Optional[List[str]]
    channel: Optional[str]
    is_active: Optional[bool]

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content: str
    type: TemplateType
    variables: List[str]
    channel: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: int

class TemplatePreview(BaseModel):
    template_id: int
    variables: Dict[str, str]

@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new message template"""
    try:
        template_data = template.dict()
        template_data["created_by"] = current_user.id
        
        new_template = await MessageTemplate.create(**template_data)
        return new_template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    channel: Optional[str] = None,
    type: Optional[TemplateType] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """List all message templates"""
    try:
        templates = await MessageTemplate.get_all(
            channel=channel,
            type=type,
            is_active=is_active
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get template details"""
    try:
        template = await MessageTemplate.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update template details"""
    try:
        template = await MessageTemplate.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        update_data = template_update.dict(exclude_unset=True)
        updated_template = await template.update(**update_data)
        return updated_template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a template"""
    try:
        template = await MessageTemplate.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        await template.delete()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{template_id}/preview")
async def preview_template(
    template_id: int,
    preview_data: TemplatePreview,
    current_user: User = Depends(get_current_user)
):
    """Preview a template with variables"""
    try:
        template = await MessageTemplate.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        message_templates = MessageTemplates()
        preview = message_templates.personalize_template(
            template.content,
            preview_data.variables,
            template.channel
        )
        return {"preview": preview}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Duplicate an existing template"""
    try:
        template = await MessageTemplate.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        template_data = template.dict()
        template_data.pop("id")
        template_data["name"] = f"{template.name} (Copy)"
        template_data["created_by"] = current_user.id
        
        new_template = await MessageTemplate.create(**template_data)
        return new_template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 