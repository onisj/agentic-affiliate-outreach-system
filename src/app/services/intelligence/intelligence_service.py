from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, CampaignInteraction
from services.intelligence.scoring import ScoringService
from services.intelligence.sentiment import SentimentAnalyzer
from services.intelligence.personalization import PersonalizationService
from services.intelligence.timing import TimingOptimizer

logger = logging.getLogger(__name__)

class IntelligenceService:
    def __init__(self,
                 db: Session,
                 scoring_service: ScoringService,
                 sentiment_analyzer: SentimentAnalyzer,
                 personalization_service: PersonalizationService,
                 timing_optimizer: TimingOptimizer):
        self.db = db
        self.scoring_service = scoring_service
        self.sentiment_analyzer = sentiment_analyzer
        self.personalization_service = personalization_service
        self.timing_optimizer = timing_optimizer

    async def analyze_prospect(self, prospect_id: str) -> Dict:
        """
        Perform comprehensive analysis of a prospect.
        
        Args:
            prospect_id: ID of the prospect to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            prospect = self.db.query(AffiliateProspect).get(prospect_id)
            if not prospect:
                raise ValueError(f"Prospect not found: {prospect_id}")

            # Get prospect's interactions
            interactions = self.db.query(CampaignInteraction).filter(
                CampaignInteraction.prospect_id == prospect_id
            ).all()

            # Perform various analyses
            scoring_analysis = await self.scoring_service.analyze_prospect(prospect_id)
            sentiment_analysis = await self._analyze_interaction_sentiment(interactions)
            engagement_analysis = await self._analyze_engagement_patterns(interactions)
            timing_analysis = await self.timing_optimizer.analyze_timing_patterns(interactions)

            return {
                'prospect_id': prospect_id,
                'scoring_analysis': scoring_analysis,
                'sentiment_analysis': sentiment_analysis,
                'engagement_analysis': engagement_analysis,
                'timing_analysis': timing_analysis,
                'recommendations': await self._generate_recommendations(
                    scoring_analysis,
                    sentiment_analysis,
                    engagement_analysis,
                    timing_analysis
                )
            }

        except Exception as e:
            logger.error(f"Error analyzing prospect: {str(e)}")
            raise

    async def _analyze_interaction_sentiment(self, interactions: List[CampaignInteraction]) -> Dict:
        """Analyze sentiment of prospect interactions."""
        try:
            sentiment_scores = []
            for interaction in interactions:
                if interaction.metadata and 'content' in interaction.metadata:
                    sentiment = await self.sentiment_analyzer.analyze_sentiment(
                        interaction.metadata['content']
                    )
                    sentiment_scores.append({
                        'timestamp': interaction.timestamp,
                        'sentiment': sentiment
                    })

            return {
                'overall_sentiment': self._calculate_overall_sentiment(sentiment_scores),
                'sentiment_trend': self._analyze_sentiment_trend(sentiment_scores),
                'sentiment_scores': sentiment_scores
            }

        except Exception as e:
            logger.error(f"Error analyzing interaction sentiment: {str(e)}")
            raise

    async def _analyze_engagement_patterns(self, interactions: List[CampaignInteraction]) -> Dict:
        """Analyze engagement patterns from interactions."""
        try:
            engagement_metrics = {
                'total_interactions': len(interactions),
                'interaction_types': {},
                'response_times': [],
                'engagement_trend': []
            }

            for interaction in interactions:
                # Count interaction types
                interaction_type = interaction.interaction_type
                engagement_metrics['interaction_types'][interaction_type] = (
                    engagement_metrics['interaction_types'].get(interaction_type, 0) + 1
                )

                # Calculate response times
                if interaction_type == 'response':
                    response_time = self._calculate_response_time(interaction)
                    if response_time:
                        engagement_metrics['response_times'].append(response_time)

                # Track engagement trend
                engagement_metrics['engagement_trend'].append({
                    'timestamp': interaction.timestamp,
                    'type': interaction_type
                })

            return {
                'metrics': engagement_metrics,
                'patterns': self._identify_engagement_patterns(engagement_metrics),
                'recommendations': self._generate_engagement_recommendations(engagement_metrics)
            }

        except Exception as e:
            logger.error(f"Error analyzing engagement patterns: {str(e)}")
            raise

    def _calculate_overall_sentiment(self, sentiment_scores: List[Dict]) -> float:
        """Calculate overall sentiment score from individual scores."""
        if not sentiment_scores:
            return 0.0
        return sum(score['sentiment'] for score in sentiment_scores) / len(sentiment_scores)

    def _analyze_sentiment_trend(self, sentiment_scores: List[Dict]) -> Dict:
        """Analyze sentiment trend over time."""
        if not sentiment_scores:
            return {'trend': 'neutral', 'confidence': 0.0}

        # Sort by timestamp
        sorted_scores = sorted(sentiment_scores, key=lambda x: x['timestamp'])
        
        # Calculate trend
        if len(sorted_scores) < 2:
            return {'trend': 'neutral', 'confidence': 0.0}

        first_sentiment = sorted_scores[0]['sentiment']
        last_sentiment = sorted_scores[-1]['sentiment']
        sentiment_change = last_sentiment - first_sentiment

        return {
            'trend': 'positive' if sentiment_change > 0.1 else 'negative' if sentiment_change < -0.1 else 'neutral',
            'confidence': abs(sentiment_change)
        }

    def _calculate_response_time(self, interaction: CampaignInteraction) -> Optional[float]:
        """Calculate response time for an interaction."""
        if not interaction.metadata or 'previous_interaction_time' not in interaction.metadata:
            return None

        previous_time = interaction.metadata['previous_interaction_time']
        response_time = (interaction.timestamp - previous_time).total_seconds() / 3600  # Convert to hours
        return response_time

    def _identify_engagement_patterns(self, metrics: Dict) -> List[Dict]:
        """Identify patterns in engagement metrics."""
        patterns = []

        # Analyze response time patterns
        if metrics['response_times']:
            avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
            patterns.append({
                'type': 'response_time',
                'pattern': 'quick' if avg_response_time < 24 else 'slow',
                'confidence': 0.8
            })

        # Analyze interaction frequency
        if metrics['total_interactions'] > 0:
            patterns.append({
                'type': 'interaction_frequency',
                'pattern': 'high' if metrics['total_interactions'] > 5 else 'low',
                'confidence': 0.7
            })

        return patterns

    def _generate_engagement_recommendations(self, metrics: Dict) -> List[Dict]:
        """Generate recommendations based on engagement metrics."""
        recommendations = []

        # Response time recommendations
        if metrics['response_times']:
            avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
            if avg_response_time > 48:  # More than 48 hours
                recommendations.append({
                    'type': 'timing',
                    'recommendation': 'Consider sending follow-up messages earlier',
                    'priority': 'high'
                })

        # Interaction frequency recommendations
        if metrics['total_interactions'] < 3:
            recommendations.append({
                'type': 'engagement',
                'recommendation': 'Increase interaction frequency',
                'priority': 'medium'
            })

        return recommendations

    async def _generate_recommendations(self,
                                      scoring_analysis: Dict,
                                      sentiment_analysis: Dict,
                                      engagement_analysis: Dict,
                                      timing_analysis: Dict) -> List[Dict]:
        """Generate comprehensive recommendations based on all analyses."""
        recommendations = []

        # Scoring-based recommendations
        if scoring_analysis['score'] < 0.5:
            recommendations.append({
                'type': 'scoring',
                'recommendation': 'Focus on improving prospect score through targeted engagement',
                'priority': 'high'
            })

        # Sentiment-based recommendations
        if sentiment_analysis['overall_sentiment'] < 0:
            recommendations.append({
                'type': 'sentiment',
                'recommendation': 'Address negative sentiment through personalized communication',
                'priority': 'high'
            })

        # Engagement-based recommendations
        recommendations.extend(engagement_analysis['recommendations'])

        # Timing-based recommendations
        if timing_analysis['optimal_times']:
            recommendations.append({
                'type': 'timing',
                'recommendation': f"Schedule interactions during optimal times: {timing_analysis['optimal_times']}",
                'priority': 'medium'
            })

        return recommendations 