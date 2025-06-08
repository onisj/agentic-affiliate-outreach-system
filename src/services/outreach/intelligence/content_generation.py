"""
Content Generation AI Service

This module provides AI-powered content generation capabilities for
creating personalized messages across different channels.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from src.database.models import (
    User, Prospect, MessageTemplate,
    EngagementLog, ChannelMetrics
)
from src.services.monitoring.monitoring import MonitoringService
from src.services.analytics.channel_analytics import ChannelAnalytics

class ContentGenerationAI:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.monitoring = MonitoringService()
        self.analytics = ChannelAnalytics(user_id)

    async def generate_content(
        self,
        prospect: Prospect,
        template: MessageTemplate,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized content based on prospect data and context"""
        try:
            # Get prospect profile
            profile = await self._get_prospect_profile(prospect)
            
            # Get engagement history
            history = await self._get_engagement_history(prospect)
            
            # Get channel context
            channel_context = await self._get_channel_context(
                prospect=prospect,
                template=template
            )
            
            # Generate content strategy
            strategy = await self._generate_content_strategy(
                profile=profile,
                history=history,
                context=channel_context
            )
            
            # Generate content variations
            variations = await self._generate_content_variations(
                template=template,
                strategy=strategy,
                context=context
            )
            
            # Select optimal variation
            optimal_variation = await self._select_optimal_variation(
                variations=variations,
                strategy=strategy,
                context=context
            )
            
            return optimal_variation
        except Exception as e:
            self.monitoring.log_error(
                f"Error generating content: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_prospect_profile(self, prospect: Prospect) -> Dict[str, Any]:
        """Get comprehensive prospect profile"""
        try:
            return {
                "basic_info": prospect.basic_info,
                "professional_info": prospect.professional_info,
                "social_profiles": prospect.social_profiles,
                "interests": prospect.interests,
                "preferences": prospect.preferences
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting prospect profile: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_engagement_history(self, prospect: Prospect) -> Dict[str, Any]:
        """Get prospect engagement history"""
        try:
            return await EngagementLog.get_prospect_history(
                prospect_id=prospect.id,
                user_id=self.user_id
            )
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting engagement history: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _get_channel_context(
        self,
        prospect: Prospect,
        template: MessageTemplate
    ) -> Dict[str, Any]:
        """Get channel-specific context"""
        try:
            return {
                "channel": template.channel,
                "channel_metrics": await ChannelMetrics.get_channel_metrics(
                    user_id=self.user_id,
                    channel=template.channel
                ),
                "channel_preferences": prospect.channel_preferences.get(
                    template.channel, {}
                )
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting channel context: {str(e)}",
                context={"prospect_id": prospect.id, "user_id": self.user_id}
            )
            raise

    async def _generate_content_strategy(
        self,
        profile: Dict[str, Any],
        history: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content strategy based on profile, history, and context"""
        try:
            # Analyze profile
            profile_analysis = await self._analyze_profile(profile)
            
            # Analyze history
            history_analysis = await self._analyze_history(history)
            
            # Analyze context
            context_analysis = await self._analyze_context(context)
            
            # Generate strategy
            strategy = {
                "tone": await self._determine_tone(
                    profile=profile_analysis,
                    history=history_analysis,
                    context=context_analysis
                ),
                "style": await self._determine_style(
                    profile=profile_analysis,
                    history=history_analysis,
                    context=context_analysis
                ),
                "key_points": await self._determine_key_points(
                    profile=profile_analysis,
                    history=history_analysis,
                    context=context_analysis
                ),
                "call_to_action": await self._determine_call_to_action(
                    profile=profile_analysis,
                    history=history_analysis,
                    context=context_analysis
                )
            }
            
            return strategy
        except Exception as e:
            self.monitoring.log_error(
                f"Error generating content strategy: {str(e)}",
                context={"user_id": self.user_id}
            )
            raise

    async def _generate_content_variations(
        self,
        template: MessageTemplate,
        strategy: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate content variations based on strategy"""
        try:
            variations = []
            
            # Generate variations for different tones
            for tone in strategy["tone"]:
                variation = await self._generate_variation(
                    template=template,
                    tone=tone,
                    strategy=strategy,
                    context=context
                )
                variations.append(variation)
            
            # Generate variations for different styles
            for style in strategy["style"]:
                variation = await self._generate_variation(
                    template=template,
                    style=style,
                    strategy=strategy,
                    context=context
                )
                variations.append(variation)
            
            return variations
        except Exception as e:
            self.monitoring.log_error(
                f"Error generating content variations: {str(e)}",
                context={"user_id": self.user_id}
            )
            raise

    async def _select_optimal_variation(
        self,
        variations: List[Dict[str, Any]],
        strategy: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select optimal content variation"""
        try:
            # Score each variation
            scored_variations = []
            for variation in variations:
                score = await self._score_variation(
                    variation=variation,
                    strategy=strategy,
                    context=context
                )
                scored_variations.append((variation, score))
            
            # Select variation with highest score
            optimal_variation = max(scored_variations, key=lambda x: x[1])[0]
            
            return optimal_variation
        except Exception as e:
            self.monitoring.log_error(
                f"Error selecting optimal variation: {str(e)}",
                context={"user_id": self.user_id}
            )
            raise 