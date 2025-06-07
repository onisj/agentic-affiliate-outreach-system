"""
Facebook Channel Endpoints

This module provides endpoints for managing Facebook interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, FacebookProfile, FacebookPost
from services.outreach.channels.facebook import FacebookClient
from api.dependencies.auth import get_current_user

router = APIRouter()

class FacebookMessage(BaseModel):
    recipient_id: str
    message: str
    attachment_url: Optional[str] = None
    quick_replies: Optional[List[Dict[str, Any]]] = None

class FacebookPost(BaseModel):
    message: str
    link: Optional[str] = None
    photos: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None
    target_audience: Optional[Dict[str, Any]] = None

class FacebookUser(BaseModel):
    id: str
    name: str
    email: Optional[str]
    profile_picture: Optional[str]
    location: Optional[str]
    about: Optional[str]
    website: Optional[str]

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    message: FacebookMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a message to a Facebook user"""
    try:
        client = FacebookClient(current_user.id)
        result = await client.send_message(
            recipient_id=message.recipient_id,
            message=message.message,
            attachment_url=message.attachment_url,
            quick_replies=message.quick_replies
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(
    post: FacebookPost,
    current_user: User = Depends(get_current_user)
):
    """Create a new Facebook post"""
    try:
        client = FacebookClient(current_user.id)
        result = await client.create_post(
            message=post.message,
            link=post.link,
            photos=post.photos,
            scheduled_time=post.scheduled_time,
            target_audience=post.target_audience
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{user_id}", response_model=FacebookUser)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get Facebook user profile"""
    try:
        client = FacebookClient(current_user.id)
        profile = await client.get_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/pages")
async def get_pages(
    current_user: User = Depends(get_current_user)
):
    """Get list of Facebook pages managed by the user"""
    try:
        client = FacebookClient(current_user.id)
        pages = await client.get_pages()
        return pages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/pages/{page_id}/posts")
async def get_page_posts(
    page_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get posts from a Facebook page"""
    try:
        client = FacebookClient(current_user.id)
        posts = await client.get_page_posts(page_id, limit=limit)
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/posts/{post_id}/comments")
async def comment_on_post(
    post_id: str,
    comment: str,
    current_user: User = Depends(get_current_user)
):
    """Comment on a Facebook post"""
    try:
        client = FacebookClient(current_user.id)
        result = await client.comment_on_post(post_id, comment)
        return {"message": "Successfully commented on post", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/groups")
async def get_groups(
    current_user: User = Depends(get_current_user)
):
    """Get list of Facebook groups the user is a member of"""
    try:
        client = FacebookClient(current_user.id)
        groups = await client.get_groups()
        return groups
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/groups/{group_id}/posts")
async def create_group_post(
    group_id: str,
    post: FacebookPost,
    current_user: User = Depends(get_current_user)
):
    """Create a post in a Facebook group"""
    try:
        client = FacebookClient(current_user.id)
        result = await client.create_group_post(
            group_id=group_id,
            message=post.message,
            link=post.link,
            photos=post.photos
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/events")
async def get_events(
    current_user: User = Depends(get_current_user)
):
    """Get list of Facebook events"""
    try:
        client = FacebookClient(current_user.id)
        events = await client.get_events()
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/events")
async def create_event(
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new Facebook event"""
    try:
        client = FacebookClient(current_user.id)
        result = await client.create_event(event_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 