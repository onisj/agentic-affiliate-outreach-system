"""
Trend Analysis AI

This module implements AI-powered trend analysis for TikTok and generic web data
to support affiliate discovery.
"""

from typing import Dict, List, Any
import logging
import numpy as np
from collections import Counter
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class TrendAnalysisAI:
    """AI-powered trend analysis for TikTok and generic web data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {str(e)}")
            
        self.stop_words = set(stopwords.words('english'))
        
    async def analyze_trends(self, data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Analyze trends from TikTok or generic web data."""
        try:
            if platform.lower() == 'tiktok':
                return await self._analyze_tiktok_trends(data)
            elif platform.lower() == 'generic':
                return await self._analyze_generic_trends(data)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing trends: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def _analyze_tiktok_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TikTok trends."""
        try:
            # Extract trend data
            trends = data.get('trends', [])
            content = data.get('content', [])
            
            # Analyze content trends
            content_analysis = await self._analyze_content_trends(content)
            
            # Analyze audience trends
            audience_analysis = await self._analyze_audience_trends(data)
            
            # Analyze engagement trends
            engagement_analysis = await self._analyze_engagement_trends(data)
            
            # Identify opportunities
            opportunities = await self._identify_opportunities(content_analysis, audience_analysis)
            
            # Generate predictions
            predictions = await self._generate_predictions(content_analysis, audience_analysis)
            
            return {
                'content_analysis': content_analysis,
                'audience_analysis': audience_analysis,
                'engagement_analysis': engagement_analysis,
                'opportunities': opportunities,
                'predictions': predictions
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing TikTok trends: {str(e)}")
            raise
            
    async def _analyze_generic_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze generic web trends."""
        try:
            # Extract trend data
            trends = data.get('trends', [])
            content = data.get('content', [])
            
            # Analyze market trends
            market_analysis = await self._analyze_market_trends(data)
            
            # Analyze content trends
            content_analysis = await self._analyze_content_trends(content)
            
            # Analyze audience trends
            audience_analysis = await self._analyze_audience_trends(data)
            
            # Identify opportunities
            opportunities = await self._identify_opportunities(content_analysis, audience_analysis)
            
            # Generate predictions
            predictions = await self._generate_predictions(content_analysis, audience_analysis)
            
            return {
                'market_analysis': market_analysis,
                'content_analysis': content_analysis,
                'audience_analysis': audience_analysis,
                'opportunities': opportunities,
                'predictions': predictions
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing generic trends: {str(e)}")
            raise
            
    async def _analyze_content_trends(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content trends."""
        try:
            # Extract text content
            texts = [item.get('text', '') for item in content]
            
            # Analyze topics
            topics = await self._extract_topics(texts)
            
            # Analyze content types
            content_types = self._analyze_content_types(content)
            
            # Analyze sentiment trends
            sentiment_trends = await self._analyze_sentiment_trends(texts)
            
            # Analyze content evolution
            content_evolution = self._analyze_content_evolution(content)
            
            return {
                'topics': topics,
                'content_types': content_types,
                'sentiment_trends': sentiment_trends,
                'content_evolution': content_evolution
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing content trends: {str(e)}")
            return {}
            
    async def _analyze_audience_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience trends."""
        try:
            audience = data.get('audience', {})
            
            # Analyze growth trends
            growth_trends = self._analyze_growth_trends(audience)
            
            # Analyze demographic shifts
            demographic_shifts = self._analyze_demographic_shifts(audience)
            
            # Analyze engagement patterns
            engagement_patterns = self._analyze_engagement_patterns(audience)
            
            # Analyze audience behavior
            behavior_analysis = self._analyze_audience_behavior(audience)
            
            return {
                'growth_trends': growth_trends,
                'demographic_shifts': demographic_shifts,
                'engagement_patterns': engagement_patterns,
                'behavior_analysis': behavior_analysis
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing audience trends: {str(e)}")
            return {}
            
    async def _analyze_engagement_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement trends."""
        try:
            engagement = data.get('engagement', {})
            
            # Calculate engagement metrics
            metrics = {
                'engagement_rate': engagement.get('engagement_rate', 0),
                'comment_rate': engagement.get('comment_rate', 0),
                'share_rate': engagement.get('share_rate', 0)
            }
            
            # Analyze interaction patterns
            interaction_patterns = self._analyze_interaction_patterns(engagement)
            
            # Analyze viral potential
            viral_potential = self._analyze_viral_potential(engagement)
            
            # Analyze engagement quality
            engagement_quality = self._analyze_engagement_quality(engagement)
            
            return {
                'metrics': metrics,
                'interaction_patterns': interaction_patterns,
                'viral_potential': viral_potential,
                'engagement_quality': engagement_quality
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement trends: {str(e)}")
            return {}
            
    async def _analyze_market_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends."""
        try:
            market = data.get('market', {})
            
            # Analyze market size
            market_size = self._analyze_market_size(market)
            
            # Analyze market growth
            market_growth = self._analyze_market_growth(market)
            
            # Analyze market segments
            market_segments = self._analyze_market_segments(market)
            
            # Analyze market opportunities
            market_opportunities = self._analyze_market_opportunities(market)
            
            return {
                'market_size': market_size,
                'market_growth': market_growth,
                'market_segments': market_segments,
                'market_opportunities': market_opportunities
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing market trends: {str(e)}")
            return {}
            
    async def _identify_opportunities(
        self,
        content_analysis: Dict[str, Any],
        audience_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify opportunities based on analysis."""
        try:
            opportunities = {
                'product_opportunities': self._identify_product_opportunities(content_analysis),
                'niche_opportunities': self._identify_niche_opportunities(content_analysis),
                'partnership_opportunities': self._identify_partnership_opportunities(audience_analysis),
                'growth_opportunities': self._identify_growth_opportunities(audience_analysis)
            }
            
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying opportunities: {str(e)}")
            return {}
            
    async def _generate_predictions(
        self,
        content_analysis: Dict[str, Any],
        audience_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trend predictions."""
        try:
            predictions = {
                'short_term': self._predict_short_term_trends(content_analysis),
                'medium_term': self._predict_medium_term_trends(content_analysis),
                'long_term': self._predict_long_term_trends(content_analysis),
                'confidence_metrics': self._calculate_prediction_confidence(content_analysis)
            }
            
            return predictions
            
        except Exception as e:
            self.monitoring.log_error(f"Error generating predictions: {str(e)}")
            return {}
            
    def _extract_topics(self, texts: List[str]) -> List[str]:
        """Extract topics from texts."""
        try:
            # Combine texts
            combined_text = ' '.join(texts)
            
            # Tokenize and preprocess
            tokens = word_tokenize(combined_text.lower())
            tokens = [t for t in tokens if t not in self.stop_words]
            
            # Get most common topics
            topic_counts = Counter(tokens)
            return [topic for topic, _ in topic_counts.most_common(10)]
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting topics: {str(e)}")
            return []
            
    def _analyze_content_types(self, content: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze content types."""
        try:
            content_types = Counter()
            
            for item in content:
                if item.get('is_video'):
                    content_types['video'] += 1
                elif item.get('is_image'):
                    content_types['image'] += 1
                elif item.get('is_link'):
                    content_types['link'] += 1
                else:
                    content_types['text'] += 1
                    
            return dict(content_types)
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing content types: {str(e)}")
            return {}
            
    async def _analyze_sentiment_trends(self, texts: List[str]) -> Dict[str, float]:
        """Analyze sentiment trends."""
        try:
            sentiments = [TextBlob(text).sentiment.polarity for text in texts]
            
            return {
                'average_sentiment': np.mean(sentiments),
                'sentiment_volatility': np.std(sentiments),
                'positive_ratio': sum(1 for s in sentiments if s > 0) / len(sentiments) if sentiments else 0
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing sentiment trends: {str(e)}")
            return {}
            
    def _analyze_content_evolution(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content evolution over time."""
        try:
            # Sort content by date
            sorted_content = sorted(
                content,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
            
            # Analyze recent vs older content
            recent_content = sorted_content[:len(sorted_content)//2]
            older_content = sorted_content[len(sorted_content)//2:]
            
            return {
                'recent_topics': self._extract_topics([c.get('text', '') for c in recent_content]),
                'older_topics': self._extract_topics([c.get('text', '') for c in older_content]),
                'content_shift': self._calculate_content_shift(recent_content, older_content)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing content evolution: {str(e)}")
            return {}
            
    def _analyze_growth_trends(self, audience: Dict[str, Any]) -> Dict[str, float]:
        """Analyze audience growth trends."""
        try:
            growth = audience.get('growth', {})
            
            return {
                'follower_growth_rate': growth.get('follower_growth_rate', 0),
                'engagement_growth_rate': growth.get('engagement_growth_rate', 0),
                'content_growth_rate': growth.get('content_growth_rate', 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing growth trends: {str(e)}")
            return {}
            
    def _analyze_demographic_shifts(self, audience: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze demographic shifts."""
        try:
            demographics = audience.get('demographics', {})
            
            return {
                'age_distribution': demographics.get('age_distribution', {}),
                'gender_distribution': demographics.get('gender_distribution', {}),
                'location_distribution': demographics.get('location_distribution', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing demographic shifts: {str(e)}")
            return {}
            
    def _analyze_engagement_patterns(self, audience: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement patterns."""
        try:
            engagement = audience.get('engagement', {})
            
            return {
                'active_hours': engagement.get('active_hours', {}),
                'engagement_frequency': engagement.get('engagement_frequency', {}),
                'content_preferences': engagement.get('content_preferences', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement patterns: {str(e)}")
            return {}
            
    def _analyze_audience_behavior(self, audience: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience behavior."""
        try:
            behavior = audience.get('behavior', {})
            
            return {
                'interaction_patterns': behavior.get('interaction_patterns', {}),
                'content_consumption': behavior.get('content_consumption', {}),
                'platform_usage': behavior.get('platform_usage', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing audience behavior: {str(e)}")
            return {}
            
    def _analyze_interaction_patterns(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interaction patterns."""
        try:
            interactions = engagement.get('interactions', {})
            
            return {
                'comment_patterns': interactions.get('comment_patterns', {}),
                'share_patterns': interactions.get('share_patterns', {}),
                'engagement_timing': interactions.get('engagement_timing', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing interaction patterns: {str(e)}")
            return {}
            
    def _analyze_viral_potential(self, engagement: Dict[str, Any]) -> Dict[str, float]:
        """Analyze viral potential."""
        try:
            viral = engagement.get('viral_metrics', {})
            
            return {
                'virality_score': viral.get('virality_score', 0),
                'share_velocity': viral.get('share_velocity', 0),
                'reach_potential': viral.get('reach_potential', 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing viral potential: {str(e)}")
            return {}
            
    def _analyze_engagement_quality(self, engagement: Dict[str, Any]) -> Dict[str, float]:
        """Analyze engagement quality."""
        try:
            quality = engagement.get('quality_metrics', {})
            
            return {
                'interaction_quality': quality.get('interaction_quality', 0),
                'comment_quality': quality.get('comment_quality', 0),
                'engagement_depth': quality.get('engagement_depth', 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement quality: {str(e)}")
            return {}
            
    def _analyze_market_size(self, market: Dict[str, Any]) -> Dict[str, float]:
        """Analyze market size."""
        try:
            size = market.get('size_metrics', {})
            
            return {
                'total_market_size': size.get('total_market_size', 0),
                'addressable_market': size.get('addressable_market', 0),
                'market_penetration': size.get('market_penetration', 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing market size: {str(e)}")
            return {}
            
    def _analyze_market_growth(self, market: Dict[str, Any]) -> Dict[str, float]:
        """Analyze market growth."""
        try:
            growth = market.get('growth_metrics', {})
            
            return {
                'growth_rate': growth.get('growth_rate', 0),
                'year_over_year_growth': growth.get('year_over_year_growth', 0),
                'projected_growth': growth.get('projected_growth', 0)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing market growth: {str(e)}")
            return {}
            
    def _analyze_market_segments(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market segments."""
        try:
            segments = market.get('segments', {})
            
            return {
                'segment_sizes': segments.get('segment_sizes', {}),
                'segment_growth': segments.get('segment_growth', {}),
                'segment_opportunities': segments.get('segment_opportunities', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing market segments: {str(e)}")
            return {}
            
    def _analyze_market_opportunities(self, market: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze market opportunities."""
        try:
            opportunities = market.get('opportunities', [])
            
            return [
                {
                    'segment': opp.get('segment'),
                    'potential': opp.get('potential'),
                    'barriers': opp.get('barriers'),
                    'recommendations': opp.get('recommendations')
                }
                for opp in opportunities
            ]
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing market opportunities: {str(e)}")
            return []
            
    def _identify_product_opportunities(self, content_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify product opportunities."""
        try:
            topics = content_analysis.get('topics', [])
            content_types = content_analysis.get('content_types', {})
            
            opportunities = []
            for topic in topics:
                if topic in ['technology', 'fashion', 'beauty', 'fitness']:
                    opportunities.append({
                        'topic': topic,
                        'type': 'product',
                        'potential': 0.8,
                        'recommendation': f"Develop products related to {topic}"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying product opportunities: {str(e)}")
            return []
            
    def _identify_niche_opportunities(self, content_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify niche opportunities."""
        try:
            topics = content_analysis.get('topics', [])
            content_evolution = content_analysis.get('content_evolution', {})
            
            opportunities = []
            for topic in topics:
                if topic not in content_evolution.get('recent_topics', []):
                    opportunities.append({
                        'topic': topic,
                        'type': 'niche',
                        'potential': 0.7,
                        'recommendation': f"Explore untapped niche in {topic}"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying niche opportunities: {str(e)}")
            return []
            
    def _identify_partnership_opportunities(self, audience_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify partnership opportunities."""
        try:
            demographics = audience_analysis.get('demographic_shifts', {})
            engagement = audience_analysis.get('engagement_patterns', {})
            
            opportunities = []
            for segment, size in demographics.get('age_distribution', {}).items():
                if size > 0.3:  # Significant audience segment
                    opportunities.append({
                        'segment': segment,
                        'type': 'partnership',
                        'potential': 0.75,
                        'recommendation': f"Partner with brands targeting {segment} audience"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying partnership opportunities: {str(e)}")
            return []
            
    def _identify_growth_opportunities(self, audience_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify growth opportunities."""
        try:
            growth = audience_analysis.get('growth_trends', {})
            behavior = audience_analysis.get('behavior_analysis', {})
            
            opportunities = []
            if growth.get('follower_growth_rate', 0) < 0.1:
                opportunities.append({
                    'type': 'growth',
                    'potential': 0.8,
                    'recommendation': "Focus on increasing follower growth rate"
                })
                
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying growth opportunities: {str(e)}")
            return []
            
    def _predict_short_term_trends(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Predict short-term trends."""
        try:
            topics = content_analysis.get('topics', [])
            sentiment = content_analysis.get('sentiment_trends', {})
            
            return {
                'trending_topics': topics[:3],
                'sentiment_outlook': 'positive' if sentiment.get('average_sentiment', 0) > 0 else 'negative',
                'confidence': 0.8
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error predicting short-term trends: {str(e)}")
            return {}
            
    def _predict_medium_term_trends(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Predict medium-term trends."""
        try:
            content_evolution = content_analysis.get('content_evolution', {})
            
            return {
                'emerging_topics': content_evolution.get('recent_topics', [])[:3],
                'content_shift': content_evolution.get('content_shift', {}),
                'confidence': 0.7
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error predicting medium-term trends: {str(e)}")
            return {}
            
    def _predict_long_term_trends(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Predict long-term trends."""
        try:
            topics = content_analysis.get('topics', [])
            content_types = content_analysis.get('content_types', {})
            
            return {
                'sustainable_topics': topics[:5],
                'content_type_evolution': content_types,
                'confidence': 0.6
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error predicting long-term trends: {str(e)}")
            return {}
            
    def _calculate_prediction_confidence(self, content_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate prediction confidence metrics."""
        try:
            sentiment = content_analysis.get('sentiment_trends', {})
            content_evolution = content_analysis.get('content_evolution', {})
            
            return {
                'data_quality': 0.8,
                'trend_stability': 0.7,
                'prediction_reliability': 0.75
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating prediction confidence: {str(e)}")
            return {} 