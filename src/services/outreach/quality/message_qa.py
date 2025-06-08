"""
Message Quality Assurance

This module implements the message quality assurance system for the Agentic Affiliate Outreach System.
It handles grammar checking, tone analysis, cultural sensitivity screening, and spam filter testing.
"""

from typing import Dict, List, Optional, Any
from services.monitoring import MonitoringService
from services.analytics import AnalyticsService

class MessageQualityAssurance:
    """Ensures message quality through various checks and optimizations."""
    
    def __init__(
        self,
        monitoring_service: MonitoringService,
        analytics_service: AnalyticsService
    ):
        """Initialize the message quality assurance system."""
        self.monitoring_service = monitoring_service
        self.analytics_service = analytics_service
        self.quality_thresholds = {
            "grammar_score": 0.95,
            "tone_score": 0.90,
            "cultural_sensitivity_score": 0.95,
            "spam_score": 0.10
        }
        
    async def check_message_quality(
        self,
        message: str,
        channel: str,
        brand_voice: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive quality checks on a message."""
        try:
            # Perform all quality checks
            grammar_check = await self._check_grammar(message)
            tone_analysis = await self._analyze_tone(message, brand_voice)
            cultural_check = await self._check_cultural_sensitivity(message)
            spam_check = await self._test_spam_filters(message, channel)
            
            # Combine results
            quality_report = {
                "grammar": grammar_check,
                "tone": tone_analysis,
                "cultural_sensitivity": cultural_check,
                "spam_check": spam_check,
                "overall_score": self._calculate_overall_score(
                    grammar_check,
                    tone_analysis,
                    cultural_check,
                    spam_check
                )
            }
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "message_quality_checked",
                {
                    "channel": channel,
                    "quality_report": quality_report
                }
            )
            
            return quality_report
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "message_quality_check_failed",
                str(e),
                {"channel": channel}
            )
            raise
    
    async def _check_grammar(self, message: str) -> Dict[str, Any]:
        """Check message grammar and spelling."""
        try:
            # Get grammar check results from analytics service
            grammar_results = await self.analytics_service.check_grammar(message)
            
            return {
                "score": grammar_results.get("score", 0.0),
                "errors": grammar_results.get("errors", []),
                "suggestions": grammar_results.get("suggestions", []),
                "passes_threshold": grammar_results.get("score", 0.0) >= self.quality_thresholds["grammar_score"]
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "grammar_check_failed",
                str(e)
            )
            raise
    
    async def _analyze_tone(
        self,
        message: str,
        brand_voice: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze message tone and adjust if needed."""
        try:
            # Get tone analysis from analytics service
            tone_results = await self.analytics_service.analyze_tone(
                message=message,
                brand_voice=brand_voice
            )
            
            return {
                "score": tone_results.get("score", 0.0),
                "tone": tone_results.get("tone", {}),
                "suggestions": tone_results.get("suggestions", []),
                "passes_threshold": tone_results.get("score", 0.0) >= self.quality_thresholds["tone_score"]
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "tone_analysis_failed",
                str(e)
            )
            raise
    
    async def _check_cultural_sensitivity(self, message: str) -> Dict[str, Any]:
        """Check message for cultural sensitivity issues."""
        try:
            # Get cultural sensitivity check from analytics service
            sensitivity_results = await self.analytics_service.check_cultural_sensitivity(message)
            
            return {
                "score": sensitivity_results.get("score", 0.0),
                "issues": sensitivity_results.get("issues", []),
                "suggestions": sensitivity_results.get("suggestions", []),
                "passes_threshold": sensitivity_results.get("score", 0.0) >= self.quality_thresholds["cultural_sensitivity_score"]
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "cultural_sensitivity_check_failed",
                str(e)
            )
            raise
    
    async def _test_spam_filters(
        self,
        message: str,
        channel: str
    ) -> Dict[str, Any]:
        """Test message against spam filters."""
        try:
            # Get spam check results from analytics service
            spam_results = await self.analytics_service.test_spam_filters(
                message=message,
                channel=channel
            )
            
            return {
                "score": spam_results.get("score", 0.0),
                "triggers": spam_results.get("triggers", []),
                "suggestions": spam_results.get("suggestions", []),
                "passes_threshold": spam_results.get("score", 0.0) <= self.quality_thresholds["spam_score"]
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "spam_check_failed",
                str(e),
                {"channel": channel}
            )
            raise
    
    def _calculate_overall_score(
        self,
        grammar_check: Dict[str, Any],
        tone_analysis: Dict[str, Any],
        cultural_check: Dict[str, Any],
        spam_check: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score."""
        try:
            # Weighted average of all scores
            weights = {
                "grammar": 0.3,
                "tone": 0.3,
                "cultural_sensitivity": 0.2,
                "spam": 0.2
            }
            
            overall_score = (
                grammar_check["score"] * weights["grammar"] +
                tone_analysis["score"] * weights["tone"] +
                cultural_check["score"] * weights["cultural_sensitivity"] +
                (1 - spam_check["score"]) * weights["spam"]
            )
            
            return round(overall_score, 2)
            
        except Exception as e:
            self.monitoring_service.record_error(
                "overall_score_calculation_failed",
                str(e)
            )
            raise
    
    async def optimize_message(
        self,
        message: str,
        quality_report: Dict[str, Any]
    ) -> str:
        """Optimize message based on quality report."""
        try:
            optimized_message = message
            
            # Apply grammar suggestions
            if quality_report["grammar"]["suggestions"]:
                optimized_message = await self._apply_grammar_suggestions(
                    optimized_message,
                    quality_report["grammar"]["suggestions"]
                )
            
            # Apply tone suggestions
            if quality_report["tone"]["suggestions"]:
                optimized_message = await self._apply_tone_suggestions(
                    optimized_message,
                    quality_report["tone"]["suggestions"]
                )
            
            # Apply cultural sensitivity suggestions
            if quality_report["cultural_sensitivity"]["suggestions"]:
                optimized_message = await self._apply_cultural_suggestions(
                    optimized_message,
                    quality_report["cultural_sensitivity"]["suggestions"]
                )
            
            # Apply spam filter suggestions
            if quality_report["spam_check"]["suggestions"]:
                optimized_message = await self._apply_spam_suggestions(
                    optimized_message,
                    quality_report["spam_check"]["suggestions"]
                )
            
            return optimized_message
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "message_optimization_failed",
                str(e)
            )
            raise
    
    async def _apply_grammar_suggestions(
        self,
        message: str,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """Apply grammar suggestions to message."""
        try:
            # Apply grammar suggestions from analytics service
            return await self.analytics_service.apply_grammar_suggestions(
                message=message,
                suggestions=suggestions
            )
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "grammar_suggestions_application_failed",
                str(e)
            )
            raise
    
    async def _apply_tone_suggestions(
        self,
        message: str,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """Apply tone suggestions to message."""
        try:
            # Apply tone suggestions from analytics service
            return await self.analytics_service.apply_tone_suggestions(
                message=message,
                suggestions=suggestions
            )
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "tone_suggestions_application_failed",
                str(e)
            )
            raise
    
    async def _apply_cultural_suggestions(
        self,
        message: str,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """Apply cultural sensitivity suggestions to message."""
        try:
            # Apply cultural suggestions from analytics service
            return await self.analytics_service.apply_cultural_suggestions(
                message=message,
                suggestions=suggestions
            )
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "cultural_suggestions_application_failed",
                str(e)
            )
            raise
    
    async def _apply_spam_suggestions(
        self,
        message: str,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """Apply spam filter suggestions to message."""
        try:
            # Apply spam suggestions from analytics service
            return await self.analytics_service.apply_spam_suggestions(
                message=message,
                suggestions=suggestions
            )
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "spam_suggestions_application_failed",
                str(e)
            )
            raise 