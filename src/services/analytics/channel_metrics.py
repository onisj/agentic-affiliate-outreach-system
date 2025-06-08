"""
Channel Metrics

This module provides channel-specific metrics and analytics for social media platforms.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import ChannelMetrics, EngagementLog
from services.monitoring import MonitoringService

class ChannelMetricsAnalyzer:
    """Analyzes channel-specific metrics and performance."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        
    async def get_channel_metrics(
        self,
        channel: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "day"
    ) -> Dict[str, Any]:
        """Get comprehensive channel metrics."""
        try:
            metrics = await ChannelMetrics.get_channel_metrics(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            # Add engagement rates
            metrics["engagement_rates"] = await self._calculate_engagement_rates(
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add audience growth
            metrics["audience_growth"] = await self._calculate_audience_growth(
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting channel metrics: {str(e)}",
                error_type="metrics_error",
                component="channel_metrics",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise
            
    async def _calculate_engagement_rates(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate engagement rates for different metrics."""
        try:
            engagement_logs = await EngagementLog.get_engagement_logs(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            total_interactions = sum(log.interaction_count for log in engagement_logs)
            total_followers = await self._get_total_followers(channel)
            
            return {
                "overall_rate": total_interactions / total_followers if total_followers > 0 else 0,
                "like_rate": sum(log.likes for log in engagement_logs) / total_followers if total_followers > 0 else 0,
                "comment_rate": sum(log.comments for log in engagement_logs) / total_followers if total_followers > 0 else 0,
                "share_rate": sum(log.shares for log in engagement_logs) / total_followers if total_followers > 0 else 0
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating engagement rates: {str(e)}",
                error_type="calculation_error",
                component="channel_metrics",
                context={"channel": channel}
            )
            raise
            
    async def _calculate_audience_growth(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate audience growth metrics."""
        try:
            metrics = await ChannelMetrics.get_audience_metrics(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "follower_growth": metrics.get("follower_growth", 0),
                "growth_rate": metrics.get("growth_rate", 0),
                "retention_rate": metrics.get("retention_rate", 0),
                "churn_rate": metrics.get("churn_rate", 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating audience growth: {str(e)}",
                error_type="calculation_error",
                component="channel_metrics",
                context={"channel": channel}
            )
            raise
            
    async def _get_total_followers(self, channel: str) -> int:
        """Get total follower count for a channel."""
        try:
            metrics = await ChannelMetrics.get_latest_metrics(
                user_id=self.user_id,
                channel=channel
            )
            return metrics.get("follower_count", 0)
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting total followers: {str(e)}",
                error_type="metrics_error",
                component="channel_metrics",
                context={"channel": channel}
            )
            raise 