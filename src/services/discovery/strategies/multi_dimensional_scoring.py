"""
Multi-Dimensional Scorer

This module implements multi-dimensional scoring for affiliate prospects,
evaluating various aspects of potential affiliates.
"""

from typing import Dict, Any
import logging

from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class MultiDimensionalScorer:
    """Multi-dimensional scoring system for affiliate prospects."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
    async def score_prospect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a prospect across multiple dimensions."""
        try:
            # Score each dimension
            audience_score = await self._score_audience_quality(data)
            content_score = await self._score_content_relevance(data)
            influence_score = await self._score_influence_level(data)
            conversion_score = await self._score_conversion_potential(data)
            engagement_score = await self._score_engagement_propensity(data)
            
            # Calculate overall score
            overall_score = await self._calculate_overall_score(
                audience_score,
                content_score,
                influence_score,
                conversion_score,
                engagement_score
            )
            
            return {
                'overall_score': overall_score,
                'dimension_scores': {
                    'audience_quality': audience_score,
                    'content_relevance': content_score,
                    'influence_level': influence_score,
                    'conversion_potential': conversion_score,
                    'engagement_propensity': engagement_score
                }
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring prospect: {str(e)}")
            raise
            
    async def _score_audience_quality(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Score audience quality dimension."""
        try:
            audience = data.get('audience', {})
            
            # Calculate engagement rate
            engagement_rate = audience.get('engagement_rate', 0)
            
            # Calculate follower authenticity
            follower_authenticity = self._calculate_follower_authenticity(audience)
            
            # Calculate audience relevance
            audience_relevance = self._calculate_audience_relevance(audience)
            
            # Calculate weighted score
            weights = {
                'engagement_rate': 0.4,
                'follower_authenticity': 0.3,
                'audience_relevance': 0.3
            }
            
            score = (
                engagement_rate * weights['engagement_rate'] +
                follower_authenticity * weights['follower_authenticity'] +
                audience_relevance * weights['audience_relevance']
            )
            
            return {
                'score': score,
                'components': {
                    'engagement_rate': engagement_rate,
                    'follower_authenticity': follower_authenticity,
                    'audience_relevance': audience_relevance
                },
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring audience quality: {str(e)}")
            return {'score': 0.0}
            
    async def _score_content_relevance(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Score content relevance dimension."""
        try:
            content = data.get('content', {})
            
            # Calculate topic alignment
            topic_alignment = self._calculate_topic_alignment(content)
            
            # Calculate brand compatibility
            brand_compatibility = self._calculate_brand_compatibility(content)
            
            # Calculate content quality
            content_quality = self._calculate_content_quality(content)
            
            # Calculate weighted score
            weights = {
                'topic_alignment': 0.4,
                'brand_compatibility': 0.3,
                'content_quality': 0.3
            }
            
            score = (
                topic_alignment * weights['topic_alignment'] +
                brand_compatibility * weights['brand_compatibility'] +
                content_quality * weights['content_quality']
            )
            
            return {
                'score': score,
                'components': {
                    'topic_alignment': topic_alignment,
                    'brand_compatibility': brand_compatibility,
                    'content_quality': content_quality
                },
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring content relevance: {str(e)}")
            return {'score': 0.0}
            
    async def _score_influence_level(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Score influence level dimension."""
        try:
            influence = data.get('influence', {})
            
            # Calculate reach
            reach = self._calculate_reach(influence)
            
            # Calculate authority
            authority = self._calculate_authority(influence)
            
            # Calculate trust signals
            trust_signals = self._calculate_trust_signals(influence)
            
            # Calculate weighted score
            weights = {
                'reach': 0.4,
                'authority': 0.3,
                'trust_signals': 0.3
            }
            
            score = (
                reach * weights['reach'] +
                authority * weights['authority'] +
                trust_signals * weights['trust_signals']
            )
            
            return {
                'score': score,
                'components': {
                    'reach': reach,
                    'authority': authority,
                    'trust_signals': trust_signals
                },
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring influence level: {str(e)}")
            return {'score': 0.0}
            
    async def _score_conversion_potential(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Score conversion potential dimension."""
        try:
            conversion = data.get('conversion', {})
            
            # Calculate historical performance
            historical_performance = self._calculate_historical_performance(conversion)
            
            # Calculate audience demographics
            audience_demographics = self._calculate_audience_demographics(conversion)
            
            # Calculate conversion likelihood
            conversion_likelihood = self._calculate_conversion_likelihood(conversion)
            
            # Calculate weighted score
            weights = {
                'historical_performance': 0.4,
                'audience_demographics': 0.3,
                'conversion_likelihood': 0.3
            }
            
            score = (
                historical_performance * weights['historical_performance'] +
                audience_demographics * weights['audience_demographics'] +
                conversion_likelihood * weights['conversion_likelihood']
            )
            
            return {
                'score': score,
                'components': {
                    'historical_performance': historical_performance,
                    'audience_demographics': audience_demographics,
                    'conversion_likelihood': conversion_likelihood
                },
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring conversion potential: {str(e)}")
            return {'score': 0.0}
            
    async def _score_engagement_propensity(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Score engagement propensity dimension."""
        try:
            engagement = data.get('engagement', {})
            
            # Calculate response likelihood
            response_likelihood = self._calculate_response_likelihood(engagement)
            
            # Calculate communication style
            communication_style = self._calculate_communication_style(engagement)
            
            # Calculate engagement history
            engagement_history = self._calculate_engagement_history(engagement)
            
            # Calculate weighted score
            weights = {
                'response_likelihood': 0.4,
                'communication_style': 0.3,
                'engagement_history': 0.3
            }
            
            score = (
                response_likelihood * weights['response_likelihood'] +
                communication_style * weights['communication_style'] +
                engagement_history * weights['engagement_history']
            )
            
            return {
                'score': score,
                'components': {
                    'response_likelihood': response_likelihood,
                    'communication_style': communication_style,
                    'engagement_history': engagement_history
                },
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring engagement propensity: {str(e)}")
            return {'score': 0.0}
            
    async def _calculate_overall_score(
        self,
        audience_score: Dict[str, float],
        content_score: Dict[str, float],
        influence_score: Dict[str, float],
        conversion_score: Dict[str, float],
        engagement_score: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate overall prospect score."""
        try:
            # Define dimension weights
            weights = {
                'audience_quality': 0.25,
                'content_relevance': 0.25,
                'influence_level': 0.2,
                'conversion_potential': 0.15,
                'engagement_propensity': 0.15
            }
            
            # Calculate weighted overall score
            overall_score = (
                audience_score['score'] * weights['audience_quality'] +
                content_score['score'] * weights['content_relevance'] +
                influence_score['score'] * weights['influence_level'] +
                conversion_score['score'] * weights['conversion_potential'] +
                engagement_score['score'] * weights['engagement_propensity']
            )
            
            return {
                'score': overall_score,
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating overall score: {str(e)}")
            return {'score': 0.0}
            
    def _calculate_follower_authenticity(self, audience: Dict[str, Any]) -> float:
        """Calculate follower authenticity score."""
        try:
            # Extract metrics
            followers = audience.get('followers', 0)
            active_followers = audience.get('active_followers', 0)
            verified_followers = audience.get('verified_followers', 0)
            
            # Calculate ratios
            active_ratio = active_followers / followers if followers > 0 else 0
            verified_ratio = verified_followers / followers if followers > 0 else 0
            
            # Calculate weighted score
            weights = {
                'active_ratio': 0.6,
                'verified_ratio': 0.4
            }
            
            return (
                active_ratio * weights['active_ratio'] +
                verified_ratio * weights['verified_ratio']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating follower authenticity: {str(e)}")
            return 0.0
            
    def _calculate_audience_relevance(self, audience: Dict[str, Any]) -> float:
        """Calculate audience relevance score."""
        try:
            # Extract metrics
            target_demographics = audience.get('target_demographics', {})
            actual_demographics = audience.get('actual_demographics', {})
            
            # Calculate demographic overlap
            overlap = sum(
                min(target_demographics.get(k, 0), actual_demographics.get(k, 0))
                for k in set(target_demographics) | set(actual_demographics)
            )
            
            return min(overlap, 1.0)
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating audience relevance: {str(e)}")
            return 0.0
            
    def _calculate_topic_alignment(self, content: Dict[str, Any]) -> float:
        """Calculate topic alignment score."""
        try:
            # Extract metrics
            target_topics = content.get('target_topics', [])
            content_topics = content.get('content_topics', [])
            
            # Calculate topic overlap
            overlap = len(set(target_topics) & set(content_topics))
            total = len(set(target_topics) | set(content_topics))
            
            return overlap / total if total > 0 else 0
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating topic alignment: {str(e)}")
            return 0.0
            
    def _calculate_brand_compatibility(self, content: Dict[str, Any]) -> float:
        """Calculate brand compatibility score."""
        try:
            # Extract metrics
            brand_values = content.get('brand_values', {})
            content_values = content.get('content_values', {})
            
            # Calculate value alignment
            alignment = sum(
                min(brand_values.get(k, 0), content_values.get(k, 0))
                for k in set(brand_values) | set(content_values)
            )
            
            return min(alignment, 1.0)
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating brand compatibility: {str(e)}")
            return 0.0
            
    def _calculate_content_quality(self, content: Dict[str, Any]) -> float:
        """Calculate content quality score."""
        try:
            # Extract metrics
            engagement_rate = content.get('engagement_rate', 0)
            content_frequency = content.get('content_frequency', 0)
            content_consistency = content.get('content_consistency', 0)
            
            # Calculate weighted score
            weights = {
                'engagement_rate': 0.4,
                'content_frequency': 0.3,
                'content_consistency': 0.3
            }
            
            return (
                engagement_rate * weights['engagement_rate'] +
                content_frequency * weights['content_frequency'] +
                content_consistency * weights['content_consistency']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating content quality: {str(e)}")
            return 0.0
            
    def _calculate_reach(self, influence: Dict[str, Any]) -> float:
        """Calculate reach score."""
        try:
            # Extract metrics
            followers = influence.get('followers', 0)
            engagement = influence.get('engagement', 0)
            
            # Calculate normalized reach
            normalized_followers = min(followers / 10000, 1)  # Cap at 10k followers
            normalized_engagement = min(engagement / 1000, 1)  # Cap at 1k engagement
            
            # Calculate weighted score
            weights = {
                'followers': 0.6,
                'engagement': 0.4
            }
            
            return (
                normalized_followers * weights['followers'] +
                normalized_engagement * weights['engagement']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating reach: {str(e)}")
            return 0.0
            
    def _calculate_authority(self, influence: Dict[str, Any]) -> float:
        """Calculate authority score."""
        try:
            # Extract metrics
            expertise = influence.get('expertise', 0)
            credibility = influence.get('credibility', 0)
            industry_standing = influence.get('industry_standing', 0)
            
            # Calculate weighted score
            weights = {
                'expertise': 0.4,
                'credibility': 0.3,
                'industry_standing': 0.3
            }
            
            return (
                expertise * weights['expertise'] +
                credibility * weights['credibility'] +
                industry_standing * weights['industry_standing']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating authority: {str(e)}")
            return 0.0
            
    def _calculate_trust_signals(self, influence: Dict[str, Any]) -> float:
        """Calculate trust signals score."""
        try:
            # Extract metrics
            verification = influence.get('verification', 0)
            testimonials = influence.get('testimonials', 0)
            partnerships = influence.get('partnerships', 0)
            
            # Calculate weighted score
            weights = {
                'verification': 0.4,
                'testimonials': 0.3,
                'partnerships': 0.3
            }
            
            return (
                verification * weights['verification'] +
                testimonials * weights['testimonials'] +
                partnerships * weights['partnerships']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating trust signals: {str(e)}")
            return 0.0
            
    def _calculate_historical_performance(self, conversion: Dict[str, Any]) -> float:
        """Calculate historical performance score."""
        try:
            # Extract metrics
            conversion_rate = conversion.get('conversion_rate', 0)
            revenue_generated = conversion.get('revenue_generated', 0)
            customer_lifetime_value = conversion.get('customer_lifetime_value', 0)
            
            # Calculate weighted score
            weights = {
                'conversion_rate': 0.4,
                'revenue_generated': 0.3,
                'customer_lifetime_value': 0.3
            }
            
            return (
                conversion_rate * weights['conversion_rate'] +
                revenue_generated * weights['revenue_generated'] +
                customer_lifetime_value * weights['customer_lifetime_value']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating historical performance: {str(e)}")
            return 0.0
            
    def _calculate_audience_demographics(self, conversion: Dict[str, Any]) -> float:
        """Calculate audience demographics score."""
        try:
            # Extract metrics
            target_demographics = conversion.get('target_demographics', {})
            actual_demographics = conversion.get('actual_demographics', {})
            
            # Calculate demographic match
            match = sum(
                min(target_demographics.get(k, 0), actual_demographics.get(k, 0))
                for k in set(target_demographics) | set(actual_demographics)
            )
            
            return min(match, 1.0)
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating audience demographics: {str(e)}")
            return 0.0
            
    def _calculate_conversion_likelihood(self, conversion: Dict[str, Any]) -> float:
        """Calculate conversion likelihood score."""
        try:
            # Extract metrics
            intent_signals = conversion.get('intent_signals', 0)
            purchase_history = conversion.get('purchase_history', 0)
            engagement_level = conversion.get('engagement_level', 0)
            
            # Calculate weighted score
            weights = {
                'intent_signals': 0.4,
                'purchase_history': 0.3,
                'engagement_level': 0.3
            }
            
            return (
                intent_signals * weights['intent_signals'] +
                purchase_history * weights['purchase_history'] +
                engagement_level * weights['engagement_level']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating conversion likelihood: {str(e)}")
            return 0.0
            
    def _calculate_response_likelihood(self, engagement: Dict[str, Any]) -> float:
        """Calculate response likelihood score."""
        try:
            # Extract metrics
            response_rate = engagement.get('response_rate', 0)
            response_time = engagement.get('response_time', 0)
            interaction_frequency = engagement.get('interaction_frequency', 0)
            
            # Calculate weighted score
            weights = {
                'response_rate': 0.4,
                'response_time': 0.3,
                'interaction_frequency': 0.3
            }
            
            return (
                response_rate * weights['response_rate'] +
                response_time * weights['response_time'] +
                interaction_frequency * weights['interaction_frequency']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating response likelihood: {str(e)}")
            return 0.0
            
    def _calculate_communication_style(self, engagement: Dict[str, Any]) -> float:
        """Calculate communication style score."""
        try:
            # Extract metrics
            tone = engagement.get('tone', 0)
            professionalism = engagement.get('professionalism', 0)
            consistency = engagement.get('consistency', 0)
            
            # Calculate weighted score
            weights = {
                'tone': 0.4,
                'professionalism': 0.3,
                'consistency': 0.3
            }
            
            return (
                tone * weights['tone'] +
                professionalism * weights['professionalism'] +
                consistency * weights['consistency']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating communication style: {str(e)}")
            return 0.0
            
    def _calculate_engagement_history(self, engagement: Dict[str, Any]) -> float:
        """Calculate engagement history score."""
        try:
            # Extract metrics
            engagement_duration = engagement.get('engagement_duration', 0)
            engagement_consistency = engagement.get('engagement_consistency', 0)
            engagement_quality = engagement.get('engagement_quality', 0)
            
            # Calculate weighted score
            weights = {
                'engagement_duration': 0.4,
                'engagement_consistency': 0.3,
                'engagement_quality': 0.3
            }
            
            return (
                engagement_duration * weights['engagement_duration'] +
                engagement_consistency * weights['engagement_consistency'] +
                engagement_quality * weights['engagement_quality']
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating engagement history: {str(e)}")
            return 0.0 