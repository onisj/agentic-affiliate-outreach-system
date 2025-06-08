"""
Personalization Engine

This module provides intelligent message personalization based on prospect data,
engagement history, and behavioral patterns.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from database.models import Prospect, MessageTemplate, EngagementLog
from services.monitoring import MonitoringService
from services.analytics import UserAnalytics
from .context_engine import ContextEngine

class PersonalizationEngine:
    """Provides intelligent message personalization capabilities."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        self.user_analytics = UserAnalytics(user_id)
        self.context_engine = ContextEngine(user_id)
        
    async def personalize_message(
        self,
        prospect: Prospect,
        template: MessageTemplate,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Personalize a message for a prospect."""
        try:
            # Get context
            context = await self.context_engine.get_context(
                prospect=prospect,
                template=template,
                additional_context=additional_context
            )
            
            # Get personalization factors
            factors = await self._get_personalization_factors(
                prospect=prospect,
                template=template,
                context=context
            )
            
            # Generate personalized message
            message = await self._generate_personalized_message(
                template=template,
                factors=factors,
                context=context
            )
            
            return {
                "message": message,
                "factors": factors,
                "context": context,
                "confidence_score": await self._calculate_confidence_score(factors)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error personalizing message: {str(e)}",
                error_type="personalization_error",
                component="personalization_engine",
                context={"prospect_id": prospect.id, "template_id": template.id}
            )
            raise
            
    async def _get_personalization_factors(
        self,
        prospect: Prospect,
        template: MessageTemplate,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get personalization factors for the message."""
        try:
            return {
                "demographic": await self._get_demographic_factors(prospect),
                "behavioral": await self._get_behavioral_factors(prospect, context),
                "preferential": await self._get_preferential_factors(prospect),
                "contextual": await self._get_contextual_factors(context)
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting personalization factors: {str(e)}",
                error_type="factor_error",
                component="personalization_engine",
                context={"prospect_id": prospect.id}
            )
            raise
            
    async def _generate_personalized_message(
        self,
        template: MessageTemplate,
        factors: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Generate a personalized message."""
        try:
            # Get base template
            message = template.content
            
            # Apply demographic personalization
            message = await self._apply_demographic_personalization(
                message=message,
                factors=factors["demographic"]
            )
            
            # Apply behavioral personalization
            message = await self._apply_behavioral_personalization(
                message=message,
                factors=factors["behavioral"]
            )
            
            # Apply preferential personalization
            message = await self._apply_preferential_personalization(
                message=message,
                factors=factors["preferential"]
            )
            
            # Apply contextual personalization
            message = await self._apply_contextual_personalization(
                message=message,
                factors=factors["contextual"],
                context=context
            )
            
            return message
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error generating personalized message: {str(e)}",
                error_type="generation_error",
                component="personalization_engine"
            )
            raise
            
    async def _calculate_confidence_score(self, factors: Dict[str, Any]) -> float:
        """Calculate confidence score for personalization."""
        try:
            # Calculate confidence based on factor quality and completeness
            scores = []
            
            for factor_type, factor_data in factors.items():
                if factor_data:
                    completeness = len(factor_data) / len(self._get_required_factors(factor_type))
                    quality = await self._calculate_factor_quality(factor_data)
                    scores.append((completeness + quality) / 2)
                    
            return sum(scores) / len(scores) if scores else 0
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating confidence score: {str(e)}",
                error_type="calculation_error",
                component="personalization_engine"
            )
            raise
            
    async def _get_required_factors(self, factor_type: str) -> List[str]:
        """Get required factors for a factor type."""
        try:
            factor_requirements = {
                "demographic": ["age", "location", "occupation"],
                "behavioral": ["engagement_level", "interaction_history", "response_patterns"],
                "preferential": ["content_preferences", "channel_preferences", "timing_preferences"],
                "contextual": ["current_context", "temporal_factors", "platform_context"]
            }
            
            return factor_requirements.get(factor_type, [])
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting required factors: {str(e)}",
                error_type="factor_error",
                component="personalization_engine"
            )
            raise 