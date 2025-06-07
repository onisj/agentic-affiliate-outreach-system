"""
WhatsApp Channel Endpoints

This module provides endpoints for managing WhatsApp interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, WhatsAppProfile, WhatsAppMessage
from services.outreach.channels.whatsapp import WhatsAppClient
from api.dependencies.auth import get_current_user

router = APIRouter()

class WhatsAppMessage(BaseModel):
    recipient_number: str
    message: str
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_params: Optional[Dict[str, Any]] = None
    reply_to_message_id: Optional[str] = None

class WhatsAppTemplate(BaseModel):
    name: str
    language: str
    category: str
    components: List[Dict[str, Any]]

class WhatsAppContact(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    message: WhatsAppMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a WhatsApp message"""
    try:
        client = WhatsAppClient(current_user.id)
        result = await client.send_message(
            recipient_number=message.recipient_number,
            message=message.message,
            media_url=message.media_url,
            template_name=message.template_name,
            template_params=message.template_params,
            reply_to_message_id=message.reply_to_message_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/messages/bulk", status_code=status.HTTP_201_CREATED)
async def send_bulk_messages(
    messages: List[WhatsAppMessage],
    current_user: User = Depends(get_current_user)
):
    """Send multiple WhatsApp messages"""
    try:
        client = WhatsAppClient(current_user.id)
        results = await client.send_bulk_messages(messages)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/templates", response_model=List[WhatsAppTemplate])
async def get_templates(
    current_user: User = Depends(get_current_user)
):
    """Get list of available message templates"""
    try:
        client = WhatsAppClient(current_user.id)
        templates = await client.get_templates()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    template: WhatsAppTemplate,
    current_user: User = Depends(get_current_user)
):
    """Create a new message template"""
    try:
        client = WhatsAppClient(current_user.id)
        result = await client.create_template(
            name=template.name,
            language=template.language,
            category=template.category,
            components=template.components
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: WhatsAppContact,
    current_user: User = Depends(get_current_user)
):
    """Create a new WhatsApp contact"""
    try:
        client = WhatsAppClient(current_user.id)
        result = await client.create_contact(
            name=contact.name,
            phone_number=contact.phone_number,
            email=contact.email,
            company=contact.company,
            notes=contact.notes
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/contacts", response_model=List[WhatsAppContact])
async def get_contacts(
    current_user: User = Depends(get_current_user)
):
    """Get list of WhatsApp contacts"""
    try:
        client = WhatsAppClient(current_user.id)
        contacts = await client.get_contacts()
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get message details"""
    try:
        client = WhatsAppClient(current_user.id)
        message = await client.get_message(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/messages")
async def get_messages(
    recipient_number: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get message history"""
    try:
        client = WhatsAppClient(current_user.id)
        messages = await client.get_messages(
            recipient_number=recipient_number,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/media/{media_id}")
async def get_media(
    media_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get media content"""
    try:
        client = WhatsAppClient(current_user.id)
        media = await client.get_media(media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        return media
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics")
async def get_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get WhatsApp analytics"""
    try:
        client = WhatsAppClient(current_user.id)
        analytics = await client.get_analytics(
            start_date=start_date,
            end_date=end_date
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 