"""
YouTube Channel Endpoints

This module provides endpoints for managing YouTube interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, YouTubeChannel, YouTubeVideo
from services.outreach.channels.youtube import YouTubeClient
from api.dependencies.auth import get_current_user

router = APIRouter()

class YouTubeVideo(BaseModel):
    title: str
    description: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    privacy_status: str = "private"
    scheduled_time: Optional[datetime] = None

class YouTubeComment(BaseModel):
    video_id: str
    comment: str
    parent_id: Optional[str] = None

class YouTubePlaylist(BaseModel):
    title: str
    description: Optional[str]
    privacy_status: str = "private"
    tags: Optional[List[str]] = None

@router.post("/videos", status_code=status.HTTP_201_CREATED)
async def upload_video(
    video: YouTubeVideo,
    current_user: User = Depends(get_current_user)
):
    """Upload a new video"""
    try:
        client = YouTubeClient(current_user.id)
        result = await client.upload_video(
            title=video.title,
            description=video.description,
            video_url=video.video_url,
            thumbnail_url=video.thumbnail_url,
            tags=video.tags,
            category_id=video.category_id,
            privacy_status=video.privacy_status,
            scheduled_time=video.scheduled_time
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/videos/{video_id}")
async def get_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get video details"""
    try:
        client = YouTubeClient(current_user.id)
        video = await client.get_video(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        return video
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/videos/{video_id}")
async def update_video(
    video_id: str,
    video_update: YouTubeVideo,
    current_user: User = Depends(get_current_user)
):
    """Update video details"""
    try:
        client = YouTubeClient(current_user.id)
        result = await client.update_video(
            video_id=video_id,
            title=video_update.title,
            description=video_update.description,
            tags=video_update.tags,
            category_id=video_update.category_id,
            privacy_status=video_update.privacy_status
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a video"""
    try:
        client = YouTubeClient(current_user.id)
        await client.delete_video(video_id)
        return {"message": "Video deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/videos/{video_id}/comments")
async def add_comment(
    video_id: str,
    comment: YouTubeComment,
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a video"""
    try:
        client = YouTubeClient(current_user.id)
        result = await client.add_comment(
            video_id=video_id,
            comment=comment.comment,
            parent_id=comment.parent_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/videos/{video_id}/comments")
async def get_comments(
    video_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get video comments"""
    try:
        client = YouTubeClient(current_user.id)
        comments = await client.get_comments(video_id, limit=limit)
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/playlists", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist: YouTubePlaylist,
    current_user: User = Depends(get_current_user)
):
    """Create a new playlist"""
    try:
        client = YouTubeClient(current_user.id)
        result = await client.create_playlist(
            title=playlist.title,
            description=playlist.description,
            privacy_status=playlist.privacy_status,
            tags=playlist.tags
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/playlists/{playlist_id}/videos")
async def add_video_to_playlist(
    playlist_id: str,
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """Add a video to a playlist"""
    try:
        client = YouTubeClient(current_user.id)
        result = await client.add_video_to_playlist(playlist_id, video_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/channels")
async def get_channels(
    current_user: User = Depends(get_current_user)
):
    """Get list of YouTube channels"""
    try:
        client = YouTubeClient(current_user.id)
        channels = await client.get_channels()
        return channels
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
    """Get YouTube analytics"""
    try:
        client = YouTubeClient(current_user.id)
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

@router.get("/videos/search")
async def search_videos(
    query: str,
    max_results: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search for videos"""
    try:
        client = YouTubeClient(current_user.id)
        videos = await client.search_videos(query, max_results=max_results)
        return videos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 