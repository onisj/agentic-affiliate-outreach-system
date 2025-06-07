"""
Discord Channel Endpoints

This module provides endpoints for managing Discord interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, DiscordProfile, DiscordMessage
from services.outreach.channels.discord import DiscordClient
from api.dependencies.auth import get_current_user

router = APIRouter()

class DiscordMessage(BaseModel):
    channel_id: str
    content: str
    tts: bool = False
    embed: Optional[Dict[str, Any]] = None
    allowed_mentions: Optional[Dict[str, Any]] = None
    message_reference: Optional[Dict[str, Any]] = None

class DiscordEmbed(BaseModel):
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    color: Optional[int]
    fields: Optional[List[Dict[str, Any]]]
    thumbnail: Optional[Dict[str, Any]]
    image: Optional[Dict[str, Any]]
    footer: Optional[Dict[str, Any]]
    timestamp: Optional[datetime]

class DiscordChannel(BaseModel):
    id: str
    name: str
    type: str
    guild_id: Optional[str]
    position: Optional[int]
    topic: Optional[str]
    nsfw: Optional[bool]
    last_message_id: Optional[str]

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    message: DiscordMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a message to a channel"""
    try:
        client = DiscordClient(current_user.id)
        result = await client.send_message(
            channel_id=message.channel_id,
            content=message.content,
            tts=message.tts,
            embed=message.embed,
            allowed_mentions=message.allowed_mentions,
            message_reference=message.message_reference
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/messages/{message_id}/edit")
async def edit_message(
    message_id: str,
    content: str,
    embed: Optional[DiscordEmbed] = None,
    current_user: User = Depends(get_current_user)
):
    """Edit a message"""
    try:
        client = DiscordClient(current_user.id)
        result = await client.edit_message(
            message_id=message_id,
            content=content,
            embed=embed.dict() if embed else None
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a message"""
    try:
        client = DiscordClient(current_user.id)
        await client.delete_message(message_id)
        return {"message": "Successfully deleted message"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/channels", response_model=List[DiscordChannel])
async def get_channels(
    current_user: User = Depends(get_current_user)
):
    """Get list of channels"""
    try:
        client = DiscordClient(current_user.id)
        channels = await client.get_channels()
        return channels
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/channels/{channel_id}", response_model=DiscordChannel)
async def get_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get channel details"""
    try:
        client = DiscordClient(current_user.id)
        channel = await client.get_channel(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        return channel
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/channels/{channel_id}/messages")
async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    before: Optional[str] = None,
    after: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get channel messages"""
    try:
        client = DiscordClient(current_user.id)
        messages = await client.get_channel_messages(
            channel_id=channel_id,
            limit=limit,
            before=before,
            after=after
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/channels/{channel_id}/typing")
async def trigger_typing(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    """Trigger typing indicator"""
    try:
        client = DiscordClient(current_user.id)
        await client.trigger_typing(channel_id)
        return {"message": "Typing indicator triggered"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/messages/{message_id}/reactions/{emoji}")
async def add_reaction(
    message_id: str,
    emoji: str,
    current_user: User = Depends(get_current_user)
):
    """Add a reaction to a message"""
    try:
        client = DiscordClient(current_user.id)
        await client.add_reaction(message_id, emoji)
        return {"message": "Successfully added reaction"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/messages/{message_id}/reactions/{emoji}")
async def remove_reaction(
    message_id: str,
    emoji: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a reaction from a message"""
    try:
        client = DiscordClient(current_user.id)
        await client.remove_reaction(message_id, emoji)
        return {"message": "Successfully removed reaction"}
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
    """Get Discord analytics"""
    try:
        client = DiscordClient(current_user.id)
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