"""
Response Analyzer

This module provides analysis of prospect response patterns and engagement behavior
to optimize outreach strategies.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.models import Prospect, EngagementLog, ResponsePattern
from services.monitoring import MonitoringService
from services.analytics import UserAnalytics

class ResponseAnalyzer:
    """Analyzes prospect response patterns and engagement behavior."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        self.user_analytics = UserAnalytics(user_id)
        
    async def analyze_responses(
        self,
        prospect: Prospect,
        channel: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze prospect response patterns."""
        try:
            # Get response history
            responses = await EngagementLog.get_prospect_responses(
                prospect_id=prospect.id,
                channel=channel,
                start_date=start_date,
                end_date=end_date
            )
            
            # Analyze response patterns
            patterns = await self._analyze_response_patterns(responses)
            
            # Get engagement metrics
            engagement = await self._get_engagement_metrics(responses)
            
            # Get sentiment analysis
            sentiment = await self._analyze_sentiment(responses)
            
            return {
                "patterns": patterns,
                "engagement": engagement,
                "sentiment": sentiment,
                "recommendations": await self._generate_recommendations(
                    patterns=patterns,
                    engagement=engagement,
                    sentiment=sentiment
                )
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing responses: {str(e)}",
                error_type="analysis_error",
                component="response_analyzer",
                context={"prospect_id": prospect.id, "channel": channel}
            )
            raise
            
    async def _analyze_response_patterns(
        self,
        responses: List[EngagementLog]
    ) -> Dict[str, Any]:
        """Analyze response patterns from engagement logs."""
        try:
            return {
                "response_rate": await self._calculate_response_rate(responses),
                "response_time": await self._analyze_response_time(responses),
                "response_quality": await self._analyze_response_quality(responses),
                "engagement_trend": await self._analyze_engagement_trend(responses)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing response patterns: {str(e)}",
                error_type="analysis_error",
                component="response_analyzer"
            )
            raise
            
    async def _get_engagement_metrics(
        self,
        responses: List[EngagementLog]
    ) -> Dict[str, Any]:
        """Get engagement metrics from responses."""
        try:
            return {
                "total_responses": len(responses),
                "average_response_length": await self._calculate_average_length(responses),
                "engagement_score": await self._calculate_engagement_score(responses),
                "interaction_depth": await self._calculate_interaction_depth(responses)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting engagement metrics: {str(e)}",
                error_type="metrics_error",
                component="response_analyzer"
            )
            raise
            
    async def _analyze_sentiment(
        self,
        responses: List[EngagementLog]
    ) -> Dict[str, Any]:
        """Analyze sentiment in responses."""
        try:
            sentiments = [response.sentiment for response in responses if response.sentiment]
            
            if not sentiments:
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                    "sentiment_trend": "stable"
                }
                
            return {
                "overall_sentiment": await self._calculate_overall_sentiment(sentiments),
                "sentiment_distribution": await self._calculate_sentiment_distribution(sentiments),
                "sentiment_trend": await self._analyze_sentiment_trend(sentiments)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing sentiment: {str(e)}",
                error_type="analysis_error",
                component="response_analyzer"
            )
            raise
            
    async def _generate_recommendations(
        self,
        patterns: Dict[str, Any],
        engagement: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        try:
            recommendations = []
            
            # Response rate recommendations
            if patterns["response_rate"] < 0.3:
                recommendations.append("Consider adjusting message timing to improve response rates")
                
            # Engagement recommendations
            if engagement["engagement_score"] < 0.5:
                recommendations.append("Enhance message personalization to increase engagement")
                
            # Sentiment recommendations
            if sentiment["overall_sentiment"] == "negative":
                recommendations.append("Review and adjust messaging tone to improve sentiment")
                
            return recommendations
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error generating recommendations: {str(e)}",
                error_type="recommendation_error",
                component="response_analyzer"
            )
            raise 