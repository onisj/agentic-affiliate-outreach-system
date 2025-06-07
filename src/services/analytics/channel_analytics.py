"""
Channel Analytics Service

This module provides comprehensive analytics for all social media channels.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import (
    User, MessageLog, EngagementLog, ChannelMetrics,
    UserMetrics, ContentMetrics, CampaignMetrics
)
from services.monitoring import MonitoringService

class ChannelAnalytics:
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
        """Get comprehensive channel metrics"""
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
            
            # Add content performance
            metrics["content_performance"] = await self._get_content_performance(
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return metrics
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting channel metrics: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def get_user_metrics(
        self,
        channel: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get user engagement metrics"""
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
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def get_content_metrics(
        self,
        channel: str,
        content_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get content performance metrics"""
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
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def get_campaign_metrics(
        self,
        campaign_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get campaign performance metrics"""
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
                context={"campaign_id": campaign_id, "user_id": self.user_id}
            )
            raise

    async def _calculate_engagement_rates(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate engagement rates for different metrics"""
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
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _calculate_audience_growth(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate audience growth metrics"""
        try:
            metrics = await ChannelMetrics.get_audience_growth(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "total_growth": metrics.total_growth,
                "growth_rate": metrics.growth_rate,
                "retention_rate": metrics.retention_rate,
                "churn_rate": metrics.churn_rate
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating audience growth: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _get_content_performance(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get content performance metrics"""
        try:
            metrics = await ContentMetrics.get_performance(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "best_performing": metrics.best_performing,
                "worst_performing": metrics.worst_performing,
                "average_engagement": metrics.average_engagement,
                "content_types": metrics.content_types
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting content performance: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _analyze_user_behavior(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        try:
            behavior = await UserMetrics.analyze_behavior(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "active_hours": behavior.active_hours,
                "preferred_content": behavior.preferred_content,
                "interaction_patterns": behavior.interaction_patterns,
                "user_retention": behavior.user_retention
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing user behavior: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _get_user_segments(
        self,
        channel: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get user segmentation data"""
        try:
            segments = await UserMetrics.get_segments(
                user_id=self.user_id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            return [
                {
                    "segment_name": segment.name,
                    "user_count": segment.user_count,
                    "engagement_rate": segment.engagement_rate,
                    "demographics": segment.demographics
                }
                for segment in segments
            ]
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting user segments: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _calculate_content_effectiveness(
        self,
        channel: str,
        content_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate content effectiveness metrics"""
        try:
            effectiveness = await ContentMetrics.calculate_effectiveness(
                user_id=self.user_id,
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "engagement_score": effectiveness.engagement_score,
                "reach_score": effectiveness.reach_score,
                "conversion_score": effectiveness.conversion_score,
                "overall_score": effectiveness.overall_score
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating content effectiveness: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _analyze_content_trends(
        self,
        channel: str,
        content_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Analyze content trends"""
        try:
            trends = await ContentMetrics.analyze_trends(
                user_id=self.user_id,
                channel=channel,
                content_type=content_type,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "trending_topics": trends.trending_topics,
                "content_patterns": trends.content_patterns,
                "performance_trends": trends.performance_trends,
                "recommendations": trends.recommendations
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing content trends: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise

    async def _calculate_campaign_effectiveness(
        self,
        campaign_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate campaign effectiveness metrics"""
        try:
            effectiveness = await CampaignMetrics.calculate_effectiveness(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "reach_rate": effectiveness.reach_rate,
                "engagement_rate": effectiveness.engagement_rate,
                "conversion_rate": effectiveness.conversion_rate,
                "overall_effectiveness": effectiveness.overall_effectiveness
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating campaign effectiveness: {str(e)}",
                context={"campaign_id": campaign_id, "user_id": self.user_id}
            )
            raise

    async def _calculate_campaign_roi(
        self,
        campaign_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate campaign ROI metrics"""
        try:
            roi = await CampaignMetrics.calculate_roi(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "total_investment": roi.total_investment,
                "total_revenue": roi.total_revenue,
                "roi_percentage": roi.roi_percentage,
                "break_even_point": roi.break_even_point
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating campaign ROI: {str(e)}",
                context={"campaign_id": campaign_id, "user_id": self.user_id}
            )
            raise

    async def _get_total_followers(self, channel: str) -> int:
        """Get total number of followers for a channel"""
        try:
            return await ChannelMetrics.get_total_followers(
                user_id=self.user_id,
                channel=channel
            )
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting total followers: {str(e)}",
                context={"channel": channel, "user_id": self.user_id}
            )
            raise 