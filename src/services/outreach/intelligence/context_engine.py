"""
Context Engine

This module provides contextual information for personalization by analyzing
platform-specific data, engagement history, and user preferences.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from src.database.models import (
    User, Prospect, MessageTemplate,
    EngagementLog, ChannelMetrics
)
from src.services.monitoring import MonitoringService
from src.services.analytics.channel_analytics import ChannelAnalytics

class ContextEngine:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        self.analytics = ChannelAnalytics(user_id)

    async def get_context(
        self,
        prospect: Prospect,
        template: MessageTemplate,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive context for personalization"""
        try:
            # Get platform context
            platform_context = await self._get_platform_context(
                prospect=prospect,
                template=template
            )
            
            # Get engagement context
            engagement_context = await self._get_engagement_context(
                prospect=prospect,
                template=template
            )
            
            # Get preference context
            preference_context = await self._get_preference_context(
                prospect=prospect,
                template=template
            )
            
            # Get temporal context
            temporal_context = await self._get_temporal_context(
                prospect=prospect,
                template=template
            )
            
            # Combine all contexts
            context = {
                "platform": platform_context,
                "engagement": engagement_context,
                "preferences": preference_context,
                "temporal": temporal_context
            }
            
            # Add any additional context
            if additional_context:
                context.update(additional_context)
            
            return context
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting context: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_platform_context(
        self,
        prospect: Prospect,
        template: MessageTemplate
    ) -> Dict[str, Any]:
        """Get platform-specific context"""
        try:
            # Get channel metrics
            channel_metrics = await ChannelMetrics.get_channel_metrics(
                user_id=self.user_id,
                channel=template.channel
            )
            
            # Get platform-specific data
            platform_data = await self._get_platform_data(
                prospect=prospect,
                channel=template.channel
            )
            
            return {
                "channel": template.channel,
                "metrics": channel_metrics,
                "platform_data": platform_data,
                "content_guidelines": await self._get_content_guidelines(
                    channel=template.channel
                )
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting platform context: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_engagement_context(
        self,
        prospect: Prospect,
        template: MessageTemplate
    ) -> Dict[str, Any]:
        """Get engagement history context"""
        try:
            # Get engagement history
            history = await EngagementLog.get_prospect_history(
                prospect_id=prospect.id,
                user_id=self.user_id
            )
            
            # Analyze engagement patterns
            patterns = await self._analyze_engagement_patterns(history)
            
            # Get response rates
            response_rates = await self._get_response_rates(history)
            
            return {
                "history": history,
                "patterns": patterns,
                "response_rates": response_rates,
                "last_interaction": await self._get_last_interaction(history)
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting engagement context: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_preference_context(
        self,
        prospect: Prospect,
        template: MessageTemplate
    ) -> Dict[str, Any]:
        """Get prospect preferences context"""
        try:
            return {
                "channel_preferences": prospect.channel_preferences,
                "content_preferences": prospect.content_preferences,
                "timing_preferences": prospect.timing_preferences,
                "interaction_preferences": prospect.interaction_preferences
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting preference context: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_temporal_context(
        self,
        prospect: Prospect,
        template: MessageTemplate
    ) -> Dict[str, Any]:
        """Get temporal context (time-based factors)"""
        try:
            current_time = datetime.utcnow()
            
            return {
                "time_of_day": current_time.hour,
                "day_of_week": current_time.weekday(),
                "timezone": prospect.timezone,
                "seasonal_factors": await self._get_seasonal_factors(current_time)
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting temporal context: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_platform_data(
        self,
        prospect: Prospect,
        channel: str
    ) -> Dict[str, Any]:
        """Get platform-specific data for the prospect"""
        try:
            # Get platform-specific profile data
            profile_data = await self._get_platform_profile(
                prospect=prospect,
                channel=channel
            )
            
            # Get platform-specific activity data
            activity_data = await self._get_platform_activity(
                prospect=prospect,
                channel=channel
            )
            
            return {
                "profile": profile_data,
                "activity": activity_data
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting platform data: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _analyze_engagement_patterns(
        self,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze engagement patterns from history"""
        try:
            # Analyze response times
            response_times = await self._analyze_response_times(history)
            
            # Analyze engagement frequency
            frequency = await self._analyze_engagement_frequency(history)
            
            # Analyze content preferences
            content_prefs = await self._analyze_content_preferences(history)
            
            return {
                "response_times": response_times,
                "frequency": frequency,
                "content_preferences": content_prefs
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing engagement patterns: {str(e)}",
                context={"user_id": self.user_id}
            )
            raise

    async def _get_seasonal_factors(
        self,
        current_time: datetime
    ) -> Dict[str, Any]:
        """Get seasonal factors affecting engagement"""
        try:
            return {
                "season": self._get_season(current_time),
                "holiday": await self._get_holiday_context(current_time),
                "business_cycle": await self._get_business_cycle(current_time)
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting seasonal factors: {str(e)}",
                context={"user_id": self.user_id}
            )
            raise 