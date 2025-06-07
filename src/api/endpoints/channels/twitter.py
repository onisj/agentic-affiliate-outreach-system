"""
Twitter Channel Endpoints

This module provides endpoints for Twitter-specific operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from services.outreach.twitter_client import TwitterClient
from api.dependencies.auth import get_current_user
from database.models import User

router = APIRouter()

class TwitterMessage(BaseModel):
    user_id: str
    message: str

class TwitterTweet(BaseModel):
    text: str
    reply_to_tweet_id: Optional[str] = None

class TwitterUser(BaseModel):
    id: str
    username: str
    name: str
    description: Optional[str]
    followers_count: int
    following_count: int
    tweet_count: int
    profile_image_url: Optional[str]

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_dm(
    message: TwitterMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a direct message to a Twitter user"""
    try:
        async with TwitterClient() as client:
            success = await client.send_message(
                recipient_id=message.user_id,
                message=message.message
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send Twitter DM"
                )
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/tweets", status_code=status.HTTP_201_CREATED)
async def send_tweet(
    tweet: TwitterTweet,
    current_user: User = Depends(get_current_user)
):
    """Send a tweet"""
    try:
        async with TwitterClient() as client:
            success = await client.send_tweet(tweet.text)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send tweet"
                )
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{username}", response_model=TwitterUser)
async def get_user_profile(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Get a Twitter user's profile"""
    try:
        async with TwitterClient() as client:
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

@router.post("/users/{user_id}/follow")
async def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Follow a Twitter user"""
    try:
        async with TwitterClient() as client:
            success = await client.follow_user(user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to follow user"
                )
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search/users")
async def search_users(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search for Twitter users"""
    try:
        async with TwitterClient() as client:
            # TODO: Implement user search
            return {"message": "User search not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/tweets/{tweet_id}/replies")
async def get_tweet_replies(
    tweet_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get replies to a tweet"""
    try:
        async with TwitterClient() as client:
            # TODO: Implement tweet replies retrieval
            return {"message": "Tweet replies not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 