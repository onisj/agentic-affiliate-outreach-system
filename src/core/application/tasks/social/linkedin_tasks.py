"""
LinkedIn Tasks

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
from services.linkedin import LinkedInService
from database.session import get_db
from database.models import MessageLog, MessageType, MessageStatus
from utils.base_task import BaseTask

logger = logging.getLogger(__name__)

class LinkedInTask(BaseTask):
    """Base class for LinkedIn tasks with common functionality."""
    
    def __init__(self):
        super().__init__()
        self.linkedin_service = LinkedInService()

    def after_return(self, *args, **kwargs):
        """Cleanup after task completion."""
        self.linkedin_service.close()

@celery_app.task(bind=True, base=LinkedInTask)
def research_prospect(self, profile_id: str) -> Dict[str, Any]:
    """Research and analyze a LinkedIn prospect."""
    try:
        # Fetch profile
        profile_result = self.linkedin_service.get_profile(profile_id)
        if not profile_result["success"]:
            return {
                "success": False,
                "error": profile_result["error"]
            }
        
        profile = profile_result["profile"]
        
        # Analyze profile
        analysis = {
            "name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}",
            "headline": profile.get("headline", ""),
            "industry": profile.get("industry", ""),
            "location": profile.get("location", {}).get("name", ""),
            "current_position": self._get_current_position(profile),
            "company": self._get_current_company(profile),
            "years_experience": self._calculate_experience(profile),
            "skills": self._extract_skills(profile),
            "education": self._extract_education(profile)
        }
        
        # Save analysis
        self._save_analysis(profile_id, analysis)
        
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

@celery_app.task(bind=True, base=LinkedInTask)
def analyze_campaign(self, campaign_id: str) -> Dict[str, Any]:
    """Analyze LinkedIn campaign performance."""
    try:
        db = next(get_db())
        
        # Get campaign messages
        messages = db.query(MessageLog).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.message_type == MessageType.LINKEDIN.value
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

@celery_app.task(bind=True, base=LinkedInTask)
def manage_connections(self, action: str, profile_ids: List[str]) -> Dict[str, Any]:
    """Manage LinkedIn connections."""
    try:
        results = {
            "total": len(profile_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for profile_id in profile_ids:
            try:
                if action == "connect":
                    result = self.linkedin_service.send_connection_request(profile_id)
                elif action == "unconnect":
                    result = self.linkedin_service.remove_connection(profile_id)
                else:
                    raise ValueError(f"Invalid action: {action}")
                
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "profile_id": profile_id,
                        "error": result["error"]
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "profile_id": profile_id,
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

@celery_app.task(bind=True, base=LinkedInTask)
def send_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send LinkedIn messages in bulk."""
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
                result = self.linkedin_service.send_message(
                    message_data["profile_id"],
                    message_data["message"]
                )
                
                if result["success"]:
                    # Log message
                    self.linkedin_service.log_message(
                        message_data["prospect_id"],
                        message_data["message"],
                        result["message_id"],
                        db
                    )
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "profile_id": message_data["profile_id"],
                        "error": result["error"]
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "profile_id": message_data["profile_id"],
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

def _get_current_position(self, profile: Dict[str, Any]) -> str:
    """Extract current position from profile."""
    try:
        positions = profile.get("positions", {}).get("values", [])
        if positions:
            return positions[0].get("title", "")
        return ""
    except:
        return ""

def _get_current_company(self, profile: Dict[str, Any]) -> str:
    """Extract current company from profile."""
    try:
        positions = profile.get("positions", {}).get("values", [])
        if positions:
            return positions[0].get("company", {}).get("name", "")
        return ""
    except:
        return ""

def _calculate_experience(self, profile: Dict[str, Any]) -> int:
    """Calculate years of experience from profile."""
    try:
        positions = profile.get("positions", {}).get("values", [])
        if not positions:
            return 0
            
        total_years = 0
        for position in positions:
            start_date = position.get("startDate", {})
            end_date = position.get("endDate", {})
            
            if start_date and end_date:
                start = datetime(start_date.get("year", 0), start_date.get("month", 1), 1)
                end = datetime(end_date.get("year", 0), end_date.get("month", 1), 1)
                total_years += (end - start).days / 365.25
            elif start_date:
                start = datetime(start_date.get("year", 0), start_date.get("month", 1), 1)
                total_years += (datetime.now() - start).days / 365.25
                
        return int(total_years)
    except:
        return 0

def _extract_skills(self, profile: Dict[str, Any]) -> List[str]:
    """Extract skills from profile."""
    try:
        return [skill.get("name", "") for skill in profile.get("skills", {}).get("values", [])]
    except:
        return []

def _extract_education(self, profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract education from profile."""
    try:
        return [{
            "school": edu.get("schoolName", ""),
            "degree": edu.get("degree", ""),
            "field": edu.get("fieldOfStudy", ""),
            "year": edu.get("endDate", {}).get("year", "")
        } for edu in profile.get("educations", {}).get("values", [])]
    except:
        return []

def _save_analysis(self, profile_id: str, analysis: Dict[str, Any]) -> None:
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