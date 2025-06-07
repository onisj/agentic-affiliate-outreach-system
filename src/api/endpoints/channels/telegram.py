"""
Telegram Channel Endpoints

This module provides endpoints for managing Telegram interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, TelegramProfile, TelegramMessage
from services.outreach.channels.telegram import TelegramClient
from api.dependencies.auth import get_current_user

router = APIRouter()

class TelegramMessage(BaseModel):
    chat_id: str
    text: str
    parse_mode: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    reply_markup: Optional[Dict[str, Any]] = None
    disable_web_page_preview: bool = False

class TelegramMediaMessage(BaseModel):
    chat_id: str
    caption: Optional[str] = None
    media_url: str
    media_type: str  # photo, video, audio, document
    reply_to_message_id: Optional[str] = None
    reply_markup: Optional[Dict[str, Any]] = None

class TelegramChat(BaseModel):
    id: str
    type: str  # private, group, supergroup, channel
    title: Optional[str]
    username: Optional[str]
    description: Optional[str]
    member_count: Optional[int]

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    message: TelegramMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a text message"""
    try:
        client = TelegramClient(current_user.id)
        result = await client.send_message(
            chat_id=message.chat_id,
            text=message.text,
            parse_mode=message.parse_mode,
            reply_to_message_id=message.reply_to_message_id,
            reply_markup=message.reply_markup,
            disable_web_page_preview=message.disable_web_page_preview
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/media", status_code=status.HTTP_201_CREATED)
async def send_media(
    message: TelegramMediaMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a media message"""
    try:
        client = TelegramClient(current_user.id)
        result = await client.send_media(
            chat_id=message.chat_id,
            caption=message.caption,
            media_url=message.media_url,
            media_type=message.media_type,
            reply_to_message_id=message.reply_to_message_id,
            reply_markup=message.reply_markup
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/chats", response_model=List[TelegramChat])
async def get_chats(
    current_user: User = Depends(get_current_user)
):
    """Get list of chats"""
    try:
        client = TelegramClient(current_user.id)
        chats = await client.get_chats()
        return chats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/chats/{chat_id}", response_model=TelegramChat)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat details"""
    try:
        client = TelegramClient(current_user.id)
        chat = await client.get_chat(chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        return chat
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get chat messages"""
    try:
        client = TelegramClient(current_user.id)
        messages = await client.get_chat_messages(
            chat_id=chat_id,
            limit=limit,
            offset=offset
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/chats/{chat_id}/invite")
async def invite_to_chat(
    chat_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Invite a user to a chat"""
    try:
        client = TelegramClient(current_user.id)
        result = await client.invite_to_chat(chat_id, user_id)
        return {"message": "Successfully invited user", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/chats/{chat_id}/pin")
async def pin_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Pin a message in a chat"""
    try:
        client = TelegramClient(current_user.id)
        result = await client.pin_message(chat_id, message_id)
        return {"message": "Successfully pinned message", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/chats/{chat_id}/unpin")
async def unpin_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unpin a message in a chat"""
    try:
        client = TelegramClient(current_user.id)
        result = await client.unpin_message(chat_id, message_id)
        return {"message": "Successfully unpinned message", "result": result}
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
    """Get Telegram analytics"""
    try:
        client = TelegramClient(current_user.id)
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