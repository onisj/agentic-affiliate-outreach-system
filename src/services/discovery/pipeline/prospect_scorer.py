"""
Prospect Scorer

This module implements multi-dimensional scoring for prospects in the discovery pipeline,
evaluating various aspects of potential affiliates.
"""

from typing import Dict, Any
import logging
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class ProspectScorer:
    """Scores prospects based on multiple dimensions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.scaler = MinMaxScaler()
        
        # Initialize scoring weights
        self.weights = {
            'audience_quality': 0.25,
            'content_relevance': 0.25,
            'influence_level': 0.20,
            'conversion_potential': 0.15,
            'engagement_propensity': 0.15
        }
        
    async def score_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a prospect across multiple dimensions."""
        try:
            # Score each dimension
            audience_score = await self._score_audience_quality(prospect_data)
            content_score = await self._score_content_relevance(prospect_data)
            influence_score = await self._score_influence_level(prospect_data)
            conversion_score = await self._score_conversion_potential(prospect_data)
            engagement_score = await self._score_engagement_propensity(prospect_data)
            
            # Calculate weighted composite score
            composite_score = await self._calculate_composite_score({
                'audience_quality': audience_score,
                'content_relevance': content_score,
                'influence_level': influence_score,
                'conversion_potential': conversion_score,
                'engagement_propensity': engagement_score
            })
            
            return {
                'composite_score': composite_score,
                'dimension_scores': {
                    'audience_quality': audience_score,
                    'content_relevance': content_score,
                    'influence_level': influence_score,
                    'conversion_potential': conversion_score,
                    'engagement_propensity': engagement_score
                },
                'weights': self.weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring prospect: {str(e)}")
            raise
            
    async def _score_audience_quality(self, data: Dict[str, Any]) -> float:
        """Score audience quality dimension."""
        try:
            network = data.get('network', {})
            metrics = network.get('metrics', {})
            
            # Extract metrics
            size = metrics.get('size', 0)
            density = metrics.get('density', 0)
            centrality = metrics.get('centrality', 0)
            clustering = metrics.get('clustering', 0)
            
            # Calculate sub-scores
            size_score = self._normalize_score(size, 0, 1000000)
            density_score = self._normalize_score(density, 0, 1)
            centrality_score = self._normalize_score(centrality, 0, 1)
            clustering_score = self._normalize_score(clustering, 0, 1)
            
            # Calculate weighted score
            weights = {
                'size': 0.3,
                'density': 0.2,
                'centrality': 0.3,
                'clustering': 0.2
            }
            
            score = (
                size_score * weights['size'] +
                density_score * weights['density'] +
                centrality_score * weights['centrality'] +
                clustering_score * weights['clustering']
            )
            
            return score
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring audience quality: {str(e)}")
            return 0.0
            
    async def _score_content_relevance(self, data: Dict[str, Any]) -> float:
        """Score content relevance dimension."""
        try:
            content = data.get('content', [])
            if not content:
                return 0.0
                
            # Calculate content metrics
            total_posts = len(content)
            avg_engagement = np.mean([
                post.get('engagement', {}).get('likes', 0) +
                post.get('engagement', {}).get('comments', 0) +
                post.get('engagement', {}).get('shares', 0)
                for post in content
            ])
            
            # Calculate content diversity
            content_types = set(post.get('type') for post in content)
            diversity_score = len(content_types) / 5  # Assuming 5 possible content types
            
            # Calculate content quality
            quality_scores = []
            for post in content:
                score = 0
                if post.get('text'):
                    score += 0.3
                if post.get('media'):
                    score += 0.3
                if post.get('engagement', {}).get('likes', 0) > 0:
                    score += 0.2
                if post.get('engagement', {}).get('comments', 0) > 0:
                    score += 0.2
                quality_scores.append(score)
            
            avg_quality = np.mean(quality_scores) if quality_scores else 0
            
            # Calculate weighted score
            weights = {
                'volume': 0.3,
                'engagement': 0.3,
                'diversity': 0.2,
                'quality': 0.2
            }
            
            score = (
                self._normalize_score(total_posts, 0, 100) * weights['volume'] +
                self._normalize_score(avg_engagement, 0, 1000) * weights['engagement'] +
                diversity_score * weights['diversity'] +
                avg_quality * weights['quality']
            )
            
            return score
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring content relevance: {str(e)}")
            return 0.0
            
    async def _score_influence_level(self, data: Dict[str, Any]) -> float:
        """Score influence level dimension."""
        try:
            engagement = data.get('engagement', {})
            network = data.get('network', {})
            
            # Extract metrics
            followers = engagement.get('followers', 0)
            engagement_rate = engagement.get('engagement_rate', 0)
            influence_score = network.get('metrics', {}).get('centrality', 0)
            
            # Calculate sub-scores
            follower_score = self._normalize_score(followers, 0, 1000000)
            engagement_score = self._normalize_score(engagement_rate, 0, 1)
            influence_score = self._normalize_score(influence_score, 0, 1)
            
            # Calculate weighted score
            weights = {
                'followers': 0.4,
                'engagement': 0.3,
                'influence': 0.3
            }
            
            score = (
                follower_score * weights['followers'] +
                engagement_score * weights['engagement'] +
                influence_score * weights['influence']
            )
            
            return score
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring influence level: {str(e)}")
            return 0.0
            
    async def _score_conversion_potential(self, data: Dict[str, Any]) -> float:
        """Score conversion potential dimension."""
        try:
            engagement = data.get('engagement', {})
            content = data.get('content', [])
            
            # Extract metrics
            click_through_rate = engagement.get('click_through_rate', 0)
            conversion_rate = engagement.get('conversion_rate', 0)
            
            # Calculate content conversion potential
            conversion_scores = []
            for post in content:
                score = 0
                if post.get('type') == 'promotional':
                    score += 0.4
                if post.get('engagement', {}).get('clicks', 0) > 0:
                    score += 0.3
                if post.get('engagement', {}).get('conversions', 0) > 0:
                    score += 0.3
                conversion_scores.append(score)
            
            avg_conversion_potential = np.mean(conversion_scores) if conversion_scores else 0
            
            # Calculate weighted score
            weights = {
                'ctr': 0.3,
                'conversion_rate': 0.3,
                'content_potential': 0.4
            }
            
            score = (
                self._normalize_score(click_through_rate, 0, 1) * weights['ctr'] +
                self._normalize_score(conversion_rate, 0, 1) * weights['conversion_rate'] +
                avg_conversion_potential * weights['content_potential']
            )
            
            return score
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring conversion potential: {str(e)}")
            return 0.0
            
    async def _score_engagement_propensity(self, data: Dict[str, Any]) -> float:
        """Score engagement propensity dimension."""
        try:
            engagement = data.get('engagement', {})
            content = data.get('content', [])
            
            # Extract metrics
            response_rate = engagement.get('response_rate', 0)
            response_time = engagement.get('avg_response_time', 0)
            
            # Calculate content engagement
            engagement_scores = []
            for post in content:
                score = 0
                if post.get('engagement', {}).get('likes', 0) > 0:
                    score += 0.3
                if post.get('engagement', {}).get('comments', 0) > 0:
                    score += 0.4
                if post.get('engagement', {}).get('shares', 0) > 0:
                    score += 0.3
                engagement_scores.append(score)
            
            avg_engagement = np.mean(engagement_scores) if engagement_scores else 0
            
            # Calculate weighted score
            weights = {
                'response_rate': 0.3,
                'response_time': 0.2,
                'content_engagement': 0.5
            }
            
            score = (
                self._normalize_score(response_rate, 0, 1) * weights['response_rate'] +
                (1 - self._normalize_score(response_time, 0, 24)) * weights['response_time'] +
                avg_engagement * weights['content_engagement']
            )
            
            return score
            
        except Exception as e:
            self.monitoring.log_error(f"Error scoring engagement propensity: {str(e)}")
            return 0.0
            
    async def _calculate_composite_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calculate weighted composite score."""
        try:
            score = sum(
                dimension_scores[dimension] * weight
                for dimension, weight in self.weights.items()
            )
            
            return min(max(score, 0), 1)  # Normalize to [0, 1]
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating composite score: {str(e)}")
            return 0.0
            
    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize a score to range [0, 1]."""
        try:
            if max_val == min_val:
                return 0.0
            return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
        except:
            return 0.0 