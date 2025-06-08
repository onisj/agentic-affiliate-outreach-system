"""
Campaign Analytics

This module provides campaign performance analysis and ROI tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import CampaignMetrics, EngagementLog
from services.monitoring import MonitoringService

class CampaignAnalytics:
    """Analyzes campaign performance and effectiveness."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        
    async def get_campaign_metrics(
        self,
        campaign_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get campaign performance metrics."""
        try:
            metrics = await CampaignMetrics.get_campaign_metrics(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add campaign effectiveness
            metrics["effectiveness"] = await self._calculate_campaign_effectiveness(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add ROI analysis
            metrics["roi"] = await self._calculate_campaign_roi(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting campaign metrics: {str(e)}",
                error_type="metrics_error",
                component="campaign_analytics",
                context={"campaign_id": campaign_id}
            )
            raise
            
    async def _calculate_campaign_effectiveness(
        self,
        campaign_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate campaign effectiveness metrics."""
        try:
            engagement_logs = await EngagementLog.get_campaign_engagement(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            total_messages = len(engagement_logs)
            if total_messages == 0:
                return {
                    "response_rate": 0,
                    "conversion_rate": 0,
                    "engagement_rate": 0,
                    "reach_rate": 0
                }
                
            return {
                "response_rate": sum(log.response_rate for log in engagement_logs) / total_messages,
                "conversion_rate": sum(log.conversion_rate for log in engagement_logs) / total_messages,
                "engagement_rate": sum(log.engagement_rate for log in engagement_logs) / total_messages,
                "reach_rate": sum(log.reach_rate for log in engagement_logs) / total_messages
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating campaign effectiveness: {str(e)}",
                error_type="calculation_error",
                component="campaign_analytics",
                context={"campaign_id": campaign_id}
            )
            raise
            
    async def _calculate_campaign_roi(
        self,
        campaign_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate campaign ROI metrics."""
        try:
            metrics = await CampaignMetrics.get_roi_metrics(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "total_investment": metrics.get("total_investment", 0),
                "total_revenue": metrics.get("total_revenue", 0),
                "roi": metrics.get("roi", 0),
                "cpa": metrics.get("cpa", 0),
                "cpc": metrics.get("cpc", 0),
                "cpm": metrics.get("cpm", 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating campaign ROI: {str(e)}",
                error_type="calculation_error",
                component="campaign_analytics",
                context={"campaign_id": campaign_id}
            )
            raise
            
    async def get_campaign_recommendations(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """Get campaign optimization recommendations."""
        try:
            metrics = await self.get_campaign_metrics(campaign_id)
            
            return {
                "timing_recommendations": await self._get_timing_recommendations(metrics),
                "content_recommendations": await self._get_content_recommendations(metrics),
                "audience_recommendations": await self._get_audience_recommendations(metrics),
                "budget_recommendations": await self._get_budget_recommendations(metrics)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting campaign recommendations: {str(e)}",
                error_type="recommendation_error",
                component="campaign_analytics",
                context={"campaign_id": campaign_id}
            )
            raise
            
    async def _get_timing_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get timing optimization recommendations."""
        try:
            recommendations = []
            
            if metrics["effectiveness"]["response_rate"] < 0.1:
                recommendations.append("Consider adjusting message timing to improve response rates")
                
            if metrics["effectiveness"]["engagement_rate"] < 0.05:
                recommendations.append("Optimize posting schedule based on audience activity patterns")
                
            return recommendations
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting timing recommendations: {str(e)}",
                error_type="recommendation_error",
                component="campaign_analytics"
            )
            raise
            
    async def _get_content_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get content optimization recommendations."""
        try:
            recommendations = []
            
            if metrics["effectiveness"]["conversion_rate"] < 0.02:
                recommendations.append("Review and optimize call-to-action effectiveness")
                
            if metrics["effectiveness"]["reach_rate"] < 0.1:
                recommendations.append("Enhance content visibility and distribution strategy")
                
            return recommendations
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting content recommendations: {str(e)}",
                error_type="recommendation_error",
                component="campaign_analytics"
            )
            raise 