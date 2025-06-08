"""
Content Analytics

This module provides content performance analysis and optimization insights.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import ContentMetrics, EngagementLog
from services.monitoring import MonitoringService

class ContentAnalytics:
    """Analyzes content performance and effectiveness."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        
    async def get_content_metrics(
        self,
        channel: str,
        content_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get content performance metrics."""
        try:
            metrics = await ContentMetrics.get_content_metrics(
                user_id=self.user_id,
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add content effectiveness
            metrics["effectiveness"] = await self._calculate_content_effectiveness(
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add content trends
            metrics["trends"] = await self._analyze_content_trends(
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting content metrics: {str(e)}",
                error_type="metrics_error",
                component="content_analytics",
                context={"channel": channel, "content_type": content_type}
            )
            raise
            
    async def _calculate_content_effectiveness(
        self,
        channel: str,
        content_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate content effectiveness metrics."""
        try:
            engagement_logs = await EngagementLog.get_content_engagement(
                user_id=self.user_id,
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            total_posts = len(engagement_logs)
            if total_posts == 0:
                return {
                    "engagement_rate": 0,
                    "conversion_rate": 0,
                    "reach_rate": 0,
                    "viral_coefficient": 0
                }
                
            return {
                "engagement_rate": sum(log.engagement_rate for log in engagement_logs) / total_posts,
                "conversion_rate": sum(log.conversion_rate for log in engagement_logs) / total_posts,
                "reach_rate": sum(log.reach_rate for log in engagement_logs) / total_posts,
                "viral_coefficient": sum(log.viral_coefficient for log in engagement_logs) / total_posts
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating content effectiveness: {str(e)}",
                error_type="calculation_error",
                component="content_analytics",
                context={"channel": channel, "content_type": content_type}
            )
            raise
            
    async def _analyze_content_trends(
        self,
        channel: str,
        content_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Analyze content performance trends."""
        try:
            metrics = await ContentMetrics.get_trend_metrics(
                user_id=self.user_id,
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "engagement_trend": await self._calculate_trend(metrics.get("engagement_rates", [])),
                "reach_trend": await self._calculate_trend(metrics.get("reach_rates", [])),
                "conversion_trend": await self._calculate_trend(metrics.get("conversion_rates", [])),
                "viral_trend": await self._calculate_trend(metrics.get("viral_coefficients", []))
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing content trends: {str(e)}",
                error_type="analysis_error",
                component="content_analytics",
                context={"channel": channel, "content_type": content_type}
            )
            raise
            
    async def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Calculate trend statistics."""
        try:
            if not values:
                return {
                    "direction": 0,
                    "magnitude": 0,
                    "volatility": 0
                }
                
            # Calculate trend direction
            direction = (values[-1] - values[0]) / len(values)
            
            # Calculate trend magnitude
            magnitude = abs(direction)
            
            # Calculate volatility
            volatility = sum(abs(values[i] - values[i-1]) for i in range(1, len(values))) / (len(values) - 1)
            
            return {
                "direction": direction,
                "magnitude": magnitude,
                "volatility": volatility
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating trend: {str(e)}",
                error_type="calculation_error",
                component="content_analytics"
            )
            raise 