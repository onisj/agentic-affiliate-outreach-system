"""
User Analytics

This module provides user engagement analysis and segmentation capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import UserMetrics, EngagementLog, User
from services.monitoring import MonitoringService

class UserAnalytics:
    """Analyzes user engagement and behavior patterns."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        
    async def get_user_metrics(
        self,
        channel: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get user engagement metrics."""
        try:
            metrics = await UserMetrics.get_user_metrics(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add user behavior analysis
            metrics["user_behavior"] = await self._analyze_user_behavior(
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add user segmentation
            metrics["user_segments"] = await self._get_user_segments(
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting user metrics: {str(e)}",
                error_type="metrics_error",
                component="user_analytics",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise
            
    async def _analyze_user_behavior(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        try:
            engagement_logs = await EngagementLog.get_engagement_logs(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "active_hours": await self._get_active_hours(engagement_logs),
                "preferred_content": await self._get_preferred_content(engagement_logs),
                "interaction_patterns": await self._get_interaction_patterns(engagement_logs),
                "response_times": await self._get_response_times(engagement_logs)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing user behavior: {str(e)}",
                error_type="analysis_error",
                component="user_analytics",
                context={"channel": channel}
            )
            raise
            
    async def _get_user_segments(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get user segments based on behavior and engagement."""
        try:
            users = await User.get_active_users(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            segments = []
            for user in users:
                engagement = await self._get_user_engagement(user.id)
                segments.append({
                    "user_id": user.id,
                    "segment": await self._determine_segment(engagement),
                    "engagement_level": await self._calculate_engagement_level(engagement),
                    "preferences": await self._get_user_preferences(user.id)
                })
                
            return segments
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting user segments: {str(e)}",
                error_type="segmentation_error",
                component="user_analytics",
                context={"channel": channel}
            )
            raise
            
    async def _get_active_hours(self, logs: List[EngagementLog]) -> Dict[str, int]:
        """Get user active hours distribution."""
        try:
            hours = {}
            for log in logs:
                hour = log.timestamp.hour
                hours[hour] = hours.get(hour, 0) + 1
            return hours
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting active hours: {str(e)}",
                error_type="analysis_error",
                component="user_analytics"
            )
            raise
            
    async def _get_preferred_content(self, logs: List[EngagementLog]) -> Dict[str, int]:
        """Get user preferred content types."""
        try:
            content_types = {}
            for log in logs:
                content_type = log.content_type
                content_types[content_type] = content_types.get(content_type, 0) + 1
            return content_types
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting preferred content: {str(e)}",
                error_type="analysis_error",
                component="user_analytics"
            )
            raise
            
    async def _get_interaction_patterns(self, logs: List[EngagementLog]) -> Dict[str, Any]:
        """Get user interaction patterns."""
        try:
            patterns = {
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "clicks": 0
            }
            
            for log in logs:
                patterns["likes"] += log.likes
                patterns["comments"] += log.comments
                patterns["shares"] += log.shares
                patterns["clicks"] += log.clicks
                
            return patterns
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting interaction patterns: {str(e)}",
                error_type="analysis_error",
                component="user_analytics"
            )
            raise
            
    async def _get_response_times(self, logs: List[EngagementLog]) -> Dict[str, float]:
        """Get user response time statistics."""
        try:
            response_times = [log.response_time for log in logs if log.response_time]
            
            if not response_times:
                return {
                    "average": 0,
                    "median": 0,
                    "min": 0,
                    "max": 0
                }
                
            return {
                "average": sum(response_times) / len(response_times),
                "median": sorted(response_times)[len(response_times) // 2],
                "min": min(response_times),
                "max": max(response_times)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting response times: {str(e)}",
                error_type="analysis_error",
                component="user_analytics"
            )
            raise 