"""
Timing Engine

This module provides intelligent timing recommendations for outreach activities
based on prospect behavior, time zones, and engagement patterns.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import Prospect, EngagementLog, TimeZone
from services.monitoring import MonitoringService
from services.analytics import UserAnalytics

class TimingEngine:
    """Provides intelligent timing recommendations for outreach."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        self.user_analytics = UserAnalytics(user_id)
        
    async def get_optimal_timing(
        self,
        prospect: Prospect,
        channel: str,
        message_type: str
    ) -> Dict[str, Any]:
        """Get optimal timing for outreach."""
        try:
            # Get prospect's timezone
            timezone = await self._get_prospect_timezone(prospect)
            
            # Get engagement patterns
            patterns = await self._get_engagement_patterns(prospect, channel)
            
            # Get response patterns
            response_patterns = await self._get_response_patterns(prospect, channel)
            
            # Calculate optimal timing
            optimal_times = await self._calculate_optimal_times(
                timezone=timezone,
                patterns=patterns,
                response_patterns=response_patterns,
                message_type=message_type
            )
            
            return {
                "optimal_times": optimal_times,
                "timezone": timezone,
                "confidence_score": await self._calculate_confidence_score(
                    patterns=patterns,
                    response_patterns=response_patterns
                )
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting optimal timing: {str(e)}",
                error_type="timing_error",
                component="timing_engine",
                context={"prospect_id": prospect.id, "channel": channel}
            )
            raise
            
    async def _get_prospect_timezone(self, prospect: Prospect) -> str:
        """Get prospect's timezone."""
        try:
            timezone = await TimeZone.get_timezone(prospect.id)
            return timezone or "UTC"
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting prospect timezone: {str(e)}",
                error_type="timezone_error",
                component="timing_engine",
                context={"prospect_id": prospect.id}
            )
            raise
            
    async def _get_engagement_patterns(
        self,
        prospect: Prospect,
        channel: str
    ) -> Dict[str, Any]:
        """Get prospect's engagement patterns."""
        try:
            engagement_logs = await EngagementLog.get_prospect_engagement(
                prospect_id=prospect.id,
                channel=channel
            )
            
            return {
                "active_hours": await self._analyze_active_hours(engagement_logs),
                "preferred_days": await self._analyze_preferred_days(engagement_logs),
                "response_times": await self._analyze_response_times(engagement_logs)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting engagement patterns: {str(e)}",
                error_type="pattern_error",
                component="timing_engine",
                context={"prospect_id": prospect.id, "channel": channel}
            )
            raise
            
    async def _get_response_patterns(
        self,
        prospect: Prospect,
        channel: str
    ) -> Dict[str, Any]:
        """Get prospect's response patterns."""
        try:
            response_logs = await EngagementLog.get_prospect_responses(
                prospect_id=prospect.id,
                channel=channel
            )
            
            return {
                "average_response_time": await self._calculate_average_response_time(response_logs),
                "response_rate_by_time": await self._calculate_response_rate_by_time(response_logs),
                "response_rate_by_day": await self._calculate_response_rate_by_day(response_logs)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting response patterns: {str(e)}",
                error_type="pattern_error",
                component="timing_engine",
                context={"prospect_id": prospect.id, "channel": channel}
            )
            raise
            
    async def _calculate_optimal_times(
        self,
        timezone: str,
        patterns: Dict[str, Any],
        response_patterns: Dict[str, Any],
        message_type: str
    ) -> List[Dict[str, Any]]:
        """Calculate optimal times for outreach."""
        try:
            optimal_times = []
            
            # Get active hours
            active_hours = patterns["active_hours"]
            
            # Get response rates
            response_rates = response_patterns["response_rate_by_time"]
            
            # Calculate optimal times based on activity and response rates
            for hour in range(24):
                if active_hours.get(hour, 0) > 0.5 and response_rates.get(hour, 0) > 0.3:
                    optimal_times.append({
                        "hour": hour,
                        "confidence": (active_hours.get(hour, 0) + response_rates.get(hour, 0)) / 2,
                        "timezone": timezone
                    })
                    
            return sorted(optimal_times, key=lambda x: x["confidence"], reverse=True)
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating optimal times: {str(e)}",
                error_type="calculation_error",
                component="timing_engine"
            )
            raise
            
    async def _calculate_confidence_score(
        self,
        patterns: Dict[str, Any],
        response_patterns: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for timing recommendations."""
        try:
            # Calculate confidence based on data quality and consistency
            pattern_confidence = sum(patterns["active_hours"].values()) / len(patterns["active_hours"])
            response_confidence = sum(response_patterns["response_rate_by_time"].values()) / len(response_patterns["response_rate_by_time"])
            
            return (pattern_confidence + response_confidence) / 2
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating confidence score: {str(e)}",
                error_type="calculation_error",
                component="timing_engine"
            )
            raise 