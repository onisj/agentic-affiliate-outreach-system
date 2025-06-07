from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from database.models import CampaignInteraction
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

logger = logging.getLogger(__name__)

class TimingOptimizer:
    def __init__(self, db: Session):
        self.db = db
        self.time_windows = {
            'morning': (8, 12),    # 8 AM - 12 PM
            'afternoon': (12, 17), # 12 PM - 5 PM
            'evening': (17, 21)    # 5 PM - 9 PM
        }

    async def get_optimal_timing(self,
                               prospect_context: Dict,
                               campaign_constraints: Dict) -> Dict:
        """
        Determine optimal timing for outreach to a prospect.
        
        Args:
            prospect_context: Dictionary containing prospect information
            campaign_constraints: Dictionary containing campaign timing constraints
            
        Returns:
            Dictionary containing timing recommendations
        """
        try:
            # Get prospect's timezone
            timezone = prospect_context.get('timezone', 'UTC')
            tz = pytz.timezone(timezone)

            # Get historical interaction data
            interactions = await self._get_historical_interactions(
                prospect_context['prospect']['id']
            )

            # Analyze interaction patterns
            patterns = await self._analyze_interaction_patterns(interactions, tz)

            # Get optimal time windows
            optimal_windows = await self._get_optimal_windows(
                patterns,
                campaign_constraints,
                tz
            )

            return {
                'recommended_times': optimal_windows,
                'timezone': timezone,
                'confidence_score': patterns['confidence_score'],
                'analysis': {
                    'patterns': patterns['patterns'],
                    'response_times': patterns['response_times'],
                    'engagement_times': patterns['engagement_times']
                }
            }

        except Exception as e:
            logger.error(f"Error getting optimal timing: {str(e)}")
            raise

    async def _get_historical_interactions(self, prospect_id: str) -> List[CampaignInteraction]:
        """Get historical interactions for a prospect."""
        try:
            return self.db.query(CampaignInteraction).filter(
                CampaignInteraction.prospect_id == prospect_id
            ).order_by(CampaignInteraction.timestamp).all()

        except Exception as e:
            logger.error(f"Error getting historical interactions: {str(e)}")
            return []

    async def _analyze_interaction_patterns(self,
                                          interactions: List[CampaignInteraction],
                                          timezone: pytz.timezone) -> Dict:
        """Analyze interaction patterns from historical data."""
        try:
            patterns = {
                'hourly_distribution': defaultdict(int),
                'daily_distribution': defaultdict(int),
                'response_times': [],
                'engagement_times': []
            }

            for interaction in interactions:
                # Convert to prospect's timezone
                local_time = interaction.timestamp.astimezone(timezone)
                
                # Record hourly distribution
                patterns['hourly_distribution'][local_time.hour] += 1
                
                # Record daily distribution
                patterns['daily_distribution'][local_time.weekday()] += 1
                
                # Record response times
                if interaction.interaction_type == 'response':
                    patterns['response_times'].append(local_time)
                
                # Record engagement times
                if interaction.interaction_type in ['click', 'open']:
                    patterns['engagement_times'].append(local_time)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(patterns)

            return {
                'patterns': patterns,
                'confidence_score': confidence_score,
                'response_times': self._analyze_response_times(patterns['response_times']),
                'engagement_times': self._analyze_engagement_times(patterns['engagement_times'])
            }

        except Exception as e:
            logger.error(f"Error analyzing interaction patterns: {str(e)}")
            raise

    async def _get_optimal_windows(self,
                                 patterns: Dict,
                                 constraints: Dict,
                                 timezone: pytz.timezone) -> List[Dict]:
        """Get optimal time windows for outreach."""
        try:
            optimal_windows = []
            
            # Get best hours based on historical data
            best_hours = self._get_best_hours(patterns['patterns']['hourly_distribution'])
            
            # Get best days based on historical data
            best_days = self._get_best_days(patterns['patterns']['daily_distribution'])
            
            # Generate time windows
            for day in best_days:
                for hour in best_hours:
                    # Check if within campaign constraints
                    if self._is_within_constraints(day, hour, constraints, timezone):
                        optimal_windows.append({
                            'day': day,
                            'hour': hour,
                            'timezone': str(timezone),
                            'confidence': patterns['confidence_score']
                        })

            return optimal_windows

        except Exception as e:
            logger.error(f"Error getting optimal windows: {str(e)}")
            return []

    def _calculate_confidence_score(self, patterns: Dict) -> float:
        """Calculate confidence score for timing recommendations."""
        try:
            # Calculate data sufficiency
            total_interactions = sum(patterns['hourly_distribution'].values())
            data_sufficiency = min(total_interactions / 50, 1.0)  # Cap at 50 interactions
            
            # Calculate pattern consistency
            hourly_consistency = self._calculate_distribution_consistency(
                patterns['hourly_distribution']
            )
            daily_consistency = self._calculate_distribution_consistency(
                patterns['daily_distribution']
            )
            
            # Calculate response rate
            response_rate = len(patterns['response_times']) / total_interactions if total_interactions > 0 else 0
            
            # Combine scores
            confidence_score = (
                data_sufficiency * 0.4 +
                hourly_consistency * 0.3 +
                daily_consistency * 0.2 +
                response_rate * 0.1
            )
            
            return confidence_score

        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.0

    def _calculate_distribution_consistency(self, distribution: Dict) -> float:
        """Calculate consistency of a time distribution."""
        try:
            if not distribution:
                return 0.0
                
            values = list(distribution.values())
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            
            # Convert variance to consistency score (0 to 1)
            consistency = 1 / (1 + variance)
            
            return consistency

        except Exception as e:
            logger.error(f"Error calculating distribution consistency: {str(e)}")
            return 0.0

    def _get_best_hours(self, hourly_distribution: Dict) -> List[int]:
        """Get best hours based on historical data."""
        try:
            if not hourly_distribution:
                return list(range(9, 17))  # Default to business hours
                
            # Sort hours by interaction count
            sorted_hours = sorted(
                hourly_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Get top 3 hours
            best_hours = [hour for hour, _ in sorted_hours[:3]]
            
            return best_hours

        except Exception as e:
            logger.error(f"Error getting best hours: {str(e)}")
            return list(range(9, 17))

    def _get_best_days(self, daily_distribution: Dict) -> List[int]:
        """Get best days based on historical data."""
        try:
            if not daily_distribution:
                return list(range(0, 5))  # Default to weekdays
                
            # Sort days by interaction count
            sorted_days = sorted(
                daily_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Get top 3 days
            best_days = [day for day, _ in sorted_days[:3]]
            
            return best_days

        except Exception as e:
            logger.error(f"Error getting best days: {str(e)}")
            return list(range(0, 5))

    def _is_within_constraints(self,
                             day: int,
                             hour: int,
                             constraints: Dict,
                             timezone: pytz.timezone) -> bool:
        """Check if time window is within campaign constraints."""
        try:
            # Get current time in prospect's timezone
            now = datetime.now(timezone)
            
            # Create time window
            window_time = now.replace(
                hour=hour,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # Check if within campaign time range
            if 'start_date' in constraints and window_time < constraints['start_date']:
                return False
                
            if 'end_date' in constraints and window_time > constraints['end_date']:
                return False
            
            # Check if within business hours
            if hour < 9 or hour > 17:
                return False
            
            # Check if on weekend
            if day >= 5:  # 5 and 6 are Saturday and Sunday
                return False
            
            return True

        except Exception as e:
            logger.error(f"Error checking time constraints: {str(e)}")
            return False

    def _analyze_response_times(self, response_times: List[datetime]) -> Dict:
        """Analyze response time patterns."""
        try:
            if not response_times:
                return {
                    'average_response_time': None,
                    'response_time_distribution': {}
                }
            
            # Calculate average response time
            response_hours = [t.hour for t in response_times]
            avg_response_hour = sum(response_hours) / len(response_hours)
            
            # Calculate response time distribution
            distribution = defaultdict(int)
            for hour in response_hours:
                distribution[hour] += 1
            
            return {
                'average_response_time': avg_response_hour,
                'response_time_distribution': dict(distribution)
            }

        except Exception as e:
            logger.error(f"Error analyzing response times: {str(e)}")
            return {
                'average_response_time': None,
                'response_time_distribution': {}
            }

    def _analyze_engagement_times(self, engagement_times: List[datetime]) -> Dict:
        """Analyze engagement time patterns."""
        try:
            if not engagement_times:
                return {
                    'average_engagement_time': None,
                    'engagement_time_distribution': {}
                }
            
            # Calculate average engagement time
            engagement_hours = [t.hour for t in engagement_times]
            avg_engagement_hour = sum(engagement_hours) / len(engagement_hours)
            
            # Calculate engagement time distribution
            distribution = defaultdict(int)
            for hour in engagement_hours:
                distribution[hour] += 1
            
            return {
                'average_engagement_time': avg_engagement_hour,
                'engagement_time_distribution': dict(distribution)
            }

        except Exception as e:
            logger.error(f"Error analyzing engagement times: {str(e)}")
            return {
                'average_engagement_time': None,
                'engagement_time_distribution': {}
            } 