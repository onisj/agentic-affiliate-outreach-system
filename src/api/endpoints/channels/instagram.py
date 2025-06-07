"""
Instagram Channel Endpoints

This module provides endpoints for managing Instagram interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, InstagramProfile, InstagramPost
from services.outreach.channels.instagram import InstagramClient
from api.dependencies.auth import get_current_user

router = APIRouter()

class InstagramMessage(BaseModel):
    recipient_id: str
    message: str
    media_url: Optional[str] = None
    reply_to_message_id: Optional[str] = None

class InstagramPost(BaseModel):
    caption: str
    media_urls: List[str]
    location: Optional[str] = None
    hashtags: Optional[List[str]] = None

class InstagramUser(BaseModel):
    username: str
    full_name: Optional[str]
    biography: Optional[str]
    followers_count: Optional[int]
    following_count: Optional[int]
    media_count: Optional[int]
    is_private: Optional[bool]
    is_verified: Optional[bool]

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_dm(
    message: InstagramMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a direct message to an Instagram user"""
    try:
        client = InstagramClient(current_user.id)
        result = await client.send_direct_message(
            recipient_id=message.recipient_id,
            message=message.message,
            media_url=message.media_url,
            reply_to_message_id=message.reply_to_message_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(
    post: InstagramPost,
    current_user: User = Depends(get_current_user)
):
    """Create a new Instagram post"""
    try:
        client = InstagramClient(current_user.id)
        result = await client.create_post(
            caption=post.caption,
            media_urls=post.media_urls,
            location=post.location,
            hashtags=post.hashtags
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{username}", response_model=InstagramUser)
async def get_user_profile(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Get Instagram user profile"""
    try:
        client = InstagramClient(current_user.id)
        profile = await client.get_user_profile(username)
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

@router.post("/users/{username}/follow")
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Follow an Instagram user"""
    try:
        client = InstagramClient(current_user.id)
        result = await client.follow_user(username)
        return {"message": "Successfully followed user", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/users/{username}/unfollow")
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Unfollow an Instagram user"""
    try:
        client = InstagramClient(current_user.id)
        result = await client.unfollow_user(username)
        return {"message": "Successfully unfollowed user", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{username}/posts")
async def get_user_posts(
    username: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get posts from an Instagram user"""
    try:
        client = InstagramClient(current_user.id)
        posts = await client.get_user_posts(username, limit=limit)
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Like an Instagram post"""
    try:
        client = InstagramClient(current_user.id)
        result = await client.like_post(post_id)
        return {"message": "Successfully liked post", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/posts/{post_id}/comment")
async def comment_on_post(
    post_id: str,
    comment: str,
    current_user: User = Depends(get_current_user)
):
    """Comment on an Instagram post"""
    try:
        client = InstagramClient(current_user.id)
        result = await client.comment_on_post(post_id, comment)
        return {"message": "Successfully commented on post", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/hashtags/{hashtag}/posts")
async def get_hashtag_posts(
    hashtag: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get posts with a specific hashtag"""
    try:
        client = InstagramClient(current_user.id)
        posts = await client.get_hashtag_posts(hashtag, limit=limit)
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/locations/{location_id}/posts")
async def get_location_posts(
    location_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get posts from a specific location"""
    try:
        client = InstagramClient(current_user.id)
        posts = await client.get_location_posts(location_id, limit=limit)
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 