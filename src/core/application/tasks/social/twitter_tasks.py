"""
Twitter Tasks

This module provides Celery tasks for:
1. Prospect research and analysis
2. Campaign analytics
3. Connection management
4. Message sending and tracking
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from celery import Task
from sqlalchemy.orm import Session

from tasks.celery_app import celery_app
from app.services.twitter import TwitterService
from database.session import get_db
from database.models import MessageLog, MessageType, MessageStatus
from utils.base_task import BaseTask

logger = logging.getLogger(__name__)

class TwitterTask(BaseTask):
    """Base class for Twitter tasks with common functionality."""
    
    def __init__(self):
        super().__init__()
        self.twitter_service = TwitterService()

    def after_return(self, *args, **kwargs):
        """Cleanup after task completion."""
        self.twitter_service.close()

@celery_app.task(bind=True, base=TwitterTask)
def research_prospect(self, username: str) -> Dict[str, Any]:
    """Research and analyze a Twitter prospect."""
    try:
        # Fetch profile
        profile_result = self.twitter_service.get_user_profile(username)
        if not profile_result["success"]:
            return {
                "success": False,
                "error": profile_result["error"]
            }
        
        profile = profile_result["profile"]
        
        # Get recent tweets
        tweets_result = self.twitter_service.get_user_tweets(username)
        tweets = tweets_result.get("tweets", []) if tweets_result["success"] else []
        
        # Analyze profile
        analysis = {
            "name": profile.get("name", ""),
            "username": profile.get("username", ""),
            "bio": profile.get("description", ""),
            "location": profile.get("location", ""),
            "followers": profile.get("public_metrics", {}).get("followers_count", 0),
            "following": profile.get("public_metrics", {}).get("following_count", 0),
            "tweet_count": profile.get("public_metrics", {}).get("tweet_count", 0),
            "account_created": profile.get("created_at", ""),
            "recent_tweets": self._analyze_tweets(tweets),
            "engagement_rate": self._calculate_engagement_rate(profile, tweets)
        }
        
        # Save analysis
        self._save_analysis(username, analysis)
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error researching prospect: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task(bind=True, base=TwitterTask)
def analyze_campaign(self, campaign_id: str) -> Dict[str, Any]:
    """Analyze Twitter campaign performance."""
    try:
        db = next(get_db())
        
        # Get campaign messages
        messages = db.query(MessageLog).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.message_type == MessageType.TWITTER.value
        ).all()
        
        # Calculate metrics
        metrics = {
            "total_messages": len(messages),
            "sent": sum(1 for m in messages if m.status == MessageStatus.SENT.value),
            "delivered": sum(1 for m in messages if m.status == MessageStatus.DELIVERED.value),
            "read": sum(1 for m in messages if m.status == MessageStatus.READ.value),
            "replied": sum(1 for m in messages if m.status == MessageStatus.REPLIED.value)
        }
        
        # Calculate response rate
        if metrics["delivered"] > 0:
            metrics["response_rate"] = (metrics["replied"] / metrics["delivered"]) * 100
        else:
            metrics["response_rate"] = 0
        
        # Generate time series
        time_series = self._generate_time_series(messages)
        
        return {
            "success": True,
            "metrics": metrics,
            "time_series": time_series
        }
        
    except Exception as e:
        logger.error(f"Error analyzing campaign: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task(bind=True, base=TwitterTask)
def manage_connections(self, action: str, usernames: List[str]) -> Dict[str, Any]:
    """Manage Twitter connections."""
    try:
        results = {
            "total": len(usernames),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for username in usernames:
            try:
                if action == "follow":
                    result = self.twitter_service.follow_user(username)
                elif action == "unfollow":
                    result = self.twitter_service.unfollow_user(username)
                else:
                    raise ValueError(f"Invalid action: {action}")
                
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "username": username,
                        "error": result["error"]
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "username": username,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error managing connections: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task(bind=True, base=TwitterTask)
def send_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send Twitter messages in bulk."""
    try:
        results = {
            "total": len(messages),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        db = next(get_db())
        
        for message_data in messages:
            try:
                # Send message
                result = self.twitter_service.send_direct_message(
                    message_data["user_id"],
                    message_data["message"]
                )
                
                if result["success"]:
                    # Log message
                    self.twitter_service.log_message(
                        message_data["prospect_id"],
                        message_data["message"],
                        result["message_id"],
                        db
                    )
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": message_data["user_id"],
                        "error": result["error"]
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": message_data["user_id"],
                    "error": str(e)
                })
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error sending messages: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def _analyze_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze recent tweets for insights."""
    analyzed_tweets = []
    for tweet in tweets:
        metrics = tweet.get("public_metrics", {})
        analyzed_tweets.append({
            "text": tweet.get("text", ""),
            "created_at": tweet.get("created_at", ""),
            "retweets": metrics.get("retweet_count", 0),
            "likes": metrics.get("like_count", 0),
            "replies": metrics.get("reply_count", 0),
            "engagement": metrics.get("retweet_count", 0) + metrics.get("like_count", 0)
        })
    return analyzed_tweets

def _calculate_engagement_rate(self, profile: Dict[str, Any], tweets: List[Dict[str, Any]]) -> float:
    """Calculate engagement rate from recent tweets."""
    try:
        followers = profile.get("public_metrics", {}).get("followers_count", 0)
        if followers == 0:
            return 0.0
            
        total_engagement = sum(
            tweet.get("public_metrics", {}).get("retweet_count", 0) +
            tweet.get("public_metrics", {}).get("like_count", 0)
            for tweet in tweets
        )
        
        return (total_engagement / (len(tweets) * followers)) * 100
    except:
        return 0.0

def _save_analysis(self, username: str, analysis: Dict[str, Any]) -> None:
    """Save profile analysis to database."""
    try:
        db = next(get_db())
        # TODO: Implement analysis storage
        db.commit()
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")
        if db:
            db.rollback()

def _generate_time_series(self, messages: List[MessageLog]) -> Dict[str, List[Dict[str, Any]]]:
    """Generate time series data for campaign analysis."""
    try:
        time_series = {
            "sent": [],
            "delivered": [],
            "read": [],
            "replied": []
        }
        
        for message in messages:
            timestamp = message.sent_at.isoformat()
            
            if message.status == MessageStatus.SENT.value:
                time_series["sent"].append({"timestamp": timestamp, "count": 1})
            elif message.status == MessageStatus.DELIVERED.value:
                time_series["delivered"].append({"timestamp": timestamp, "count": 1})
            elif message.status == MessageStatus.READ.value:
                time_series["read"].append({"timestamp": timestamp, "count": 1})
            elif message.status == MessageStatus.REPLIED.value:
                time_series["replied"].append({"timestamp": timestamp, "count": 1})
        
        return time_series
    except:
        return {
            "sent": [],
            "delivered": [],
            "read": [],
            "replied": []
        } 