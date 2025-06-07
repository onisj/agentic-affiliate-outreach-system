"""
TikTok Channel Endpoints

This module provides endpoints for managing TikTok interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database.models import User, TikTokProfile, TikTokVideo
from services.outreach.channels.tiktok import TikTokClient
from services.analytics.channel_analytics import ChannelAnalytics
from api.dependencies.auth import get_current_user

router = APIRouter()

class TikTokVideo(BaseModel):
    description: str
    video_url: str
    cover_url: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy_level: str = "private"
    scheduled_time: Optional[datetime] = None
    duet_enabled: bool = True
    stitch_enabled: bool = True
    comments_enabled: bool = True

class TikTokComment(BaseModel):
    video_id: str
    comment: str
    parent_id: Optional[str] = None

class TikTokUser(BaseModel):
    username: str
    nickname: Optional[str]
    signature: Optional[str]
    followers_count: Optional[int]
    following_count: Optional[int]
    likes_count: Optional[int]
    video_count: Optional[int]
    is_verified: Optional[bool]

class TikTokAnalytics(BaseModel):
    channel_metrics: Dict[str, Any]
    user_metrics: Dict[str, Any]
    content_metrics: Dict[str, Any]
    campaign_metrics: Optional[Dict[str, Any]]
    engagement_metrics: Dict[str, Any]
    audience_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]

@router.post("/videos", status_code=status.HTTP_201_CREATED)
async def upload_video(
    video: TikTokVideo,
    current_user: User = Depends(get_current_user)
):
    """Upload a new TikTok video"""
    try:
        client = TikTokClient(current_user.id)
        result = await client.upload_video(
            description=video.description,
            video_url=video.video_url,
            cover_url=video.cover_url,
            tags=video.tags,
            privacy_level=video.privacy_level,
            scheduled_time=video.scheduled_time,
            duet_enabled=video.duet_enabled,
            stitch_enabled=video.stitch_enabled,
            comments_enabled=video.comments_enabled
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
        client = TikTokClient(current_user.id)
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

@router.post("/videos/{video_id}/comments")
async def add_comment(
    video_id: str,
    comment: TikTokComment,
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a video"""
    try:
        client = TikTokClient(current_user.id)
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
        client = TikTokClient(current_user.id)
        comments = await client.get_comments(video_id, limit=limit)
        return comments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{username}", response_model=TikTokUser)
async def get_user_profile(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Get TikTok user profile"""
    try:
        client = TikTokClient(current_user.id)
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

@router.get("/users/{username}/videos")
async def get_user_videos(
    username: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get videos from a user"""
    try:
        client = TikTokClient(current_user.id)
        videos = await client.get_user_videos(username, limit=limit)
        return videos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/videos/{video_id}/like")
async def like_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """Like a video"""
    try:
        client = TikTokClient(current_user.id)
        result = await client.like_video(video_id)
        return {"message": "Successfully liked video", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/videos/{video_id}/share")
async def share_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """Share a video"""
    try:
        client = TikTokClient(current_user.id)
        result = await client.share_video(video_id)
        return {"message": "Successfully shared video", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/trending")
async def get_trending_videos(
    category: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get trending videos"""
    try:
        client = TikTokClient(current_user.id)
        videos = await client.get_trending_videos(category=category, limit=limit)
        return videos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/hashtags/{hashtag}/videos")
async def get_hashtag_videos(
    hashtag: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get videos with a specific hashtag"""
    try:
        client = TikTokClient(current_user.id)
        videos = await client.get_hashtag_videos(hashtag, limit=limit)
        return videos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics", response_model=TikTokAnalytics)
async def get_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    interval: str = "day",
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive TikTok analytics"""
    try:
        analytics = ChannelAnalytics(current_user.id)
        
        # Get channel metrics
        channel_metrics = await analytics.get_channel_metrics(
            channel="tiktok",
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        # Get user metrics
        user_metrics = await analytics.get_user_metrics(
            channel="tiktok",
            start_date=start_date,
            end_date=end_date
        )
        
        # Get content metrics
        content_metrics = await analytics.get_content_metrics(
            channel="tiktok",
            content_type="video",
            start_date=start_date,
            end_date=end_date
        )
        
        # Get engagement metrics
        engagement_metrics = {
            "likes": channel_metrics["engagement_rates"]["like_rate"],
            "comments": channel_metrics["engagement_rates"]["comment_rate"],
            "shares": channel_metrics["engagement_rates"]["share_rate"],
            "follows": channel_metrics["engagement_rates"]["follow_rate"],
            "average_engagement": sum([
                channel_metrics["engagement_rates"]["like_rate"],
                channel_metrics["engagement_rates"]["comment_rate"],
                channel_metrics["engagement_rates"]["share_rate"],
                channel_metrics["engagement_rates"]["follow_rate"]
            ]) / 4
        }
        
        # Get audience metrics
        audience_metrics = {
            "total_followers": channel_metrics["audience_growth"]["total_followers"],
            "growth_rate": channel_metrics["audience_growth"]["growth_rate"],
            "retention_rate": channel_metrics["audience_growth"]["retention_rate"],
            "demographics": user_metrics["user_segments"],
            "active_users": user_metrics["user_behavior"]["active_users"]
        }
        
        # Get performance metrics
        performance_metrics = {
            "video_views": content_metrics["effectiveness"]["view_score"],
            "average_watch_time": content_metrics["effectiveness"]["watch_time_score"],
            "completion_rate": content_metrics["effectiveness"]["completion_rate"],
            "trending_topics": content_metrics["trends"]["trending_topics"],
            "best_performing_content": content_metrics["trends"]["best_performing"]
        }
        
        return TikTokAnalytics(
            channel_metrics=channel_metrics,
            user_metrics=user_metrics,
            content_metrics=content_metrics,
            campaign_metrics=None,  # Add if campaign tracking is implemented
            engagement_metrics=engagement_metrics,
            audience_metrics=audience_metrics,
            performance_metrics=performance_metrics
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics/trends")
async def get_trending_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get trending analytics"""
    try:
        analytics = ChannelAnalytics(current_user.id)
        content_metrics = await analytics.get_content_metrics(
            channel="tiktok",
            content_type="video",
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "trending_topics": content_metrics["trends"]["trending_topics"],
            "content_patterns": content_metrics["trends"]["content_patterns"],
            "performance_trends": content_metrics["trends"]["performance_trends"],
            "recommendations": content_metrics["trends"]["recommendations"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics/audience")
async def get_audience_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get audience analytics"""
    try:
        analytics = ChannelAnalytics(current_user.id)
        user_metrics = await analytics.get_user_metrics(
            channel="tiktok",
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "user_segments": user_metrics["user_segments"],
            "user_behavior": user_metrics["user_behavior"],
            "demographics": user_metrics["user_behavior"]["demographics"],
            "engagement_patterns": user_metrics["user_behavior"]["interaction_patterns"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics/content")
async def get_content_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get content analytics"""
    try:
        analytics = ChannelAnalytics(current_user.id)
        content_metrics = await analytics.get_content_metrics(
            channel="tiktok",
            content_type="video",
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "effectiveness": content_metrics["effectiveness"],
            "performance": content_metrics["trends"]["performance_trends"],
            "best_performing": content_metrics["trends"]["best_performing"],
            "recommendations": content_metrics["trends"]["recommendations"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 