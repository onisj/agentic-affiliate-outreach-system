"""
Timing Optimizer

This module implements the timing optimization system for the Agentic Affiliate Outreach System.
It handles time zone awareness, platform-specific optimal times, and individual preference learning.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from services.monitoring import MonitoringService
from services.analytics import AnalyticsService

class TimingOptimizer:
    """Optimizes message timing based on various factors."""
    
    def __init__(
        self,
        monitoring_service: MonitoringService,
        analytics_service: AnalyticsService
    ):
        """Initialize the timing optimizer."""
        self.monitoring_service = monitoring_service
        self.analytics_service = analytics_service
        self.platform_optimal_times: Dict[str, Dict[str, Any]] = {
            "linkedin": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_hours": [9, 10, 11, 14, 15, 16],
                "timezone_aware": True
            },
            "email": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_hours": [8, 9, 10, 15, 16, 17],
                "timezone_aware": True
            },
            "twitter": {
                "best_days": ["Monday", "Wednesday", "Friday"],
                "best_hours": [12, 13, 14, 15, 16],
                "timezone_aware": True
            }
        }
        
    async def get_optimal_send_time(
        self,
        prospect_id: str,
        channel: str,
        timezone: Optional[str] = None
    ) -> datetime:
        """Get the optimal time to send a message."""
        try:
            # Get prospect preferences
            preferences = await self._get_prospect_preferences(prospect_id)
            
            # Get platform optimal times
            platform_times = self.platform_optimal_times.get(channel, {})
            
            # Get historical engagement data
            engagement_data = await self._get_engagement_data(prospect_id, channel)
            
            # Calculate optimal time
            optimal_time = await self._calculate_optimal_time(
                preferences=preferences,
                platform_times=platform_times,
                engagement_data=engagement_data,
                timezone=timezone
            )
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "optimal_time_calculated",
                {
                    "prospect_id": prospect_id,
                    "channel": channel,
                    "optimal_time": optimal_time.isoformat()
                }
            )
            
            return optimal_time
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "optimal_time_calculation_failed",
                str(e),
                {"prospect_id": prospect_id, "channel": channel}
            )
            raise
    
    async def _get_prospect_preferences(self, prospect_id: str) -> Dict[str, Any]:
        """Get prospect's timing preferences."""
        try:
            # Get preferences from analytics service
            preferences = await self.analytics_service.get_prospect_preferences(prospect_id)
            
            return {
                "preferred_days": preferences.get("preferred_days", []),
                "preferred_hours": preferences.get("preferred_hours", []),
                "timezone": preferences.get("timezone", "UTC")
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "preference_retrieval_failed",
                str(e),
                {"prospect_id": prospect_id}
            )
            raise
    
    async def _get_engagement_data(
        self,
        prospect_id: str,
        channel: str
    ) -> Dict[str, Any]:
        """Get historical engagement data for the prospect."""
        try:
            # Get engagement data from analytics service
            engagement_data = await self.analytics_service.get_engagement_data(
                prospect_id=prospect_id,
                channel=channel
            )
            
            return {
                "best_days": engagement_data.get("best_days", []),
                "best_hours": engagement_data.get("best_hours", []),
                "response_times": engagement_data.get("response_times", [])
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "engagement_data_retrieval_failed",
                str(e),
                {"prospect_id": prospect_id, "channel": channel}
            )
            raise
    
    async def _calculate_optimal_time(
        self,
        preferences: Dict[str, Any],
        platform_times: Dict[str, Any],
        engagement_data: Dict[str, Any],
        timezone: Optional[str]
    ) -> datetime:
        """Calculate the optimal send time based on all factors."""
        try:
            # Get current time in prospect's timezone
            tz = pytz.timezone(timezone or preferences.get("timezone", "UTC"))
            current_time = datetime.now(tz)
            
            # Combine all timing factors
            best_days = set(
                preferences.get("preferred_days", []) +
                platform_times.get("best_days", []) +
                engagement_data.get("best_days", [])
            )
            
            best_hours = set(
                preferences.get("preferred_hours", []) +
                platform_times.get("best_hours", []) +
                engagement_data.get("best_hours", [])
            )
            
            # Find next optimal time
            optimal_time = current_time
            while True:
                # Check if current day is optimal
                if optimal_time.strftime("%A") in best_days:
                    # Check if current hour is optimal
                    if optimal_time.hour in best_hours:
                        break
                
                # Move to next hour
                optimal_time += timedelta(hours=1)
                
                # If we've checked 24 hours, move to next day
                if (optimal_time - current_time).total_seconds() > 86400:
                    optimal_time = current_time + timedelta(days=1)
                    optimal_time = optimal_time.replace(hour=min(best_hours))
            
            return optimal_time
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "optimal_time_calculation_failed",
                str(e)
            )
            raise
    
    async def update_preferences(
        self,
        prospect_id: str,
        engagement_data: Dict[str, Any]
    ) -> None:
        """Update prospect preferences based on engagement data."""
        try:
            # Update preferences in analytics service
            await self.analytics_service.update_preferences(
                prospect_id=prospect_id,
                engagement_data=engagement_data
            )
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "preferences_updated",
                {
                    "prospect_id": prospect_id,
                    "engagement_data": engagement_data
                }
            )
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "preference_update_failed",
                str(e),
                {"prospect_id": prospect_id}
            )
            raise
    
    async def get_platform_optimal_times(self, channel: str) -> Dict[str, Any]:
        """Get platform-specific optimal times."""
        try:
            return self.platform_optimal_times.get(channel, {})
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "platform_times_retrieval_failed",
                str(e),
                {"channel": channel}
            )
            raise
    
    async def update_platform_optimal_times(
        self,
        channel: str,
        optimal_times: Dict[str, Any]
    ) -> None:
        """Update platform-specific optimal times."""
        try:
            self.platform_optimal_times[channel] = optimal_times
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "platform_times_updated",
                {
                    "channel": channel,
                    "optimal_times": optimal_times
                }
            )
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "platform_times_update_failed",
                str(e),
                {"channel": channel}
            )
            raise 