from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import (
    AffiliateProspect,
    Campaign,
    CampaignInteraction,
    SocialProfile
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_campaign_analytics(self, campaign_id: str) -> Dict:
        """
        Get comprehensive analytics for a campaign.
        
        Args:
            campaign_id: ID of the campaign to analyze
            
        Returns:
            Dictionary containing campaign analytics
        """
        try:
            campaign = self.db.query(Campaign).get(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Get campaign interactions
            interactions = self.db.query(CampaignInteraction).filter(
                CampaignInteraction.campaign_id == campaign_id
            ).all()

            return {
                'campaign_id': campaign_id,
                'name': campaign.name,
                'status': campaign.status,
                'metrics': await self._calculate_campaign_metrics(interactions),
                'engagement_analysis': await self._analyze_campaign_engagement(interactions),
                'prospect_analysis': await self._analyze_campaign_prospects(campaign_id),
                'timeline_analysis': await self._analyze_campaign_timeline(interactions)
            }

        except Exception as e:
            logger.error(f"Error getting campaign analytics: {str(e)}")
            raise

    async def get_prospect_analytics(self, prospect_id: str) -> Dict:
        """
        Get comprehensive analytics for a prospect.
        
        Args:
            prospect_id: ID of the prospect to analyze
            
        Returns:
            Dictionary containing prospect analytics
        """
        try:
            prospect = self.db.query(AffiliateProspect).get(prospect_id)
            if not prospect:
                raise ValueError(f"Prospect not found: {prospect_id}")

            # Get prospect's interactions
            interactions = self.db.query(CampaignInteraction).filter(
                CampaignInteraction.prospect_id == prospect_id
            ).all()

            # Get social profiles
            profiles = self.db.query(SocialProfile).filter(
                SocialProfile.prospect_id == prospect_id
            ).all()

            return {
                'prospect_id': prospect_id,
                'metrics': await self._calculate_prospect_metrics(interactions),
                'engagement_analysis': await self._analyze_prospect_engagement(interactions),
                'social_analysis': await self._analyze_social_profiles(profiles),
                'campaign_history': await self._analyze_campaign_history(prospect_id)
            }

        except Exception as e:
            logger.error(f"Error getting prospect analytics: {str(e)}")
            raise

    async def _calculate_campaign_metrics(self, interactions: List[CampaignInteraction]) -> Dict:
        """Calculate key metrics for a campaign."""
        try:
            total_interactions = len(interactions)
            interaction_types = {}
            response_times = []

            for interaction in interactions:
                # Count interaction types
                interaction_type = interaction.interaction_type
                interaction_types[interaction_type] = (
                    interaction_types.get(interaction_type, 0) + 1
                )

                # Calculate response times
                if interaction_type == 'response':
                    response_time = self._calculate_response_time(interaction)
                    if response_time:
                        response_times.append(response_time)

            return {
                'total_interactions': total_interactions,
                'interaction_types': interaction_types,
                'average_response_time': (
                    sum(response_times) / len(response_times)
                    if response_times else None
                ),
                'response_rate': (
                    interaction_types.get('response', 0) / total_interactions
                    if total_interactions > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Error calculating campaign metrics: {str(e)}")
            raise

    async def _analyze_campaign_engagement(self, interactions: List[CampaignInteraction]) -> Dict:
        """Analyze engagement patterns in a campaign."""
        try:
            engagement_trend = []
            daily_engagement = {}

            for interaction in interactions:
                date = interaction.timestamp.date()
                daily_engagement[date] = daily_engagement.get(date, 0) + 1

                engagement_trend.append({
                    'timestamp': interaction.timestamp,
                    'type': interaction.interaction_type
                })

            return {
                'daily_engagement': daily_engagement,
                'engagement_trend': engagement_trend,
                'peak_engagement_day': max(daily_engagement.items(), key=lambda x: x[1])[0]
                if daily_engagement else None
            }

        except Exception as e:
            logger.error(f"Error analyzing campaign engagement: {str(e)}")
            raise

    async def _analyze_campaign_prospects(self, campaign_id: str) -> Dict:
        """Analyze prospect demographics and behavior in a campaign."""
        try:
            # Get unique prospects in campaign
            prospects = self.db.query(AffiliateProspect).join(
                CampaignInteraction
            ).filter(
                CampaignInteraction.campaign_id == campaign_id
            ).distinct().all()

            demographics = {
                'total_prospects': len(prospects),
                'companies': {},
                'industries': {},
                'locations': {}
            }

            for prospect in prospects:
                # Company analysis
                if prospect.company:
                    demographics['companies'][prospect.company] = (
                        demographics['companies'].get(prospect.company, 0) + 1
                    )

                # Industry analysis (if available)
                if hasattr(prospect, 'industry') and prospect.industry:
                    demographics['industries'][prospect.industry] = (
                        demographics['industries'].get(prospect.industry, 0) + 1
                    )

                # Location analysis (if available)
                if hasattr(prospect, 'location') and prospect.location:
                    demographics['locations'][prospect.location] = (
                        demographics['locations'].get(prospect.location, 0) + 1
                    )

            return demographics

        except Exception as e:
            logger.error(f"Error analyzing campaign prospects: {str(e)}")
            raise

    async def _analyze_campaign_timeline(self, interactions: List[CampaignInteraction]) -> Dict:
        """Analyze campaign timeline and milestones."""
        try:
            timeline = []
            milestones = {}

            for interaction in interactions:
                timeline.append({
                    'timestamp': interaction.timestamp,
                    'type': interaction.interaction_type,
                    'metadata': interaction.metadata
                })

                # Track milestones
                if interaction.interaction_type in ['campaign_start', 'campaign_end', 'first_response']:
                    milestones[interaction.interaction_type] = interaction.timestamp

            return {
                'timeline': timeline,
                'milestones': milestones,
                'duration': (
                    milestones.get('campaign_end', datetime.utcnow()) -
                    milestones.get('campaign_start', datetime.utcnow())
                ).total_seconds() / 3600  # Convert to hours
            }

        except Exception as e:
            logger.error(f"Error analyzing campaign timeline: {str(e)}")
            raise

    async def _calculate_prospect_metrics(self, interactions: List[CampaignInteraction]) -> Dict:
        """Calculate key metrics for a prospect."""
        try:
            total_interactions = len(interactions)
            interaction_types = {}
            response_times = []

            for interaction in interactions:
                # Count interaction types
                interaction_type = interaction.interaction_type
                interaction_types[interaction_type] = (
                    interaction_types.get(interaction_type, 0) + 1
                )

                # Calculate response times
                if interaction_type == 'response':
                    response_time = self._calculate_response_time(interaction)
                    if response_time:
                        response_times.append(response_time)

            return {
                'total_interactions': total_interactions,
                'interaction_types': interaction_types,
                'average_response_time': (
                    sum(response_times) / len(response_times)
                    if response_times else None
                ),
                'engagement_rate': (
                    interaction_types.get('response', 0) / total_interactions
                    if total_interactions > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Error calculating prospect metrics: {str(e)}")
            raise

    async def _analyze_prospect_engagement(self, interactions: List[CampaignInteraction]) -> Dict:
        """Analyze engagement patterns for a prospect."""
        try:
            engagement_trend = []
            campaign_engagement = {}

            for interaction in interactions:
                campaign_id = interaction.campaign_id
                campaign_engagement[campaign_id] = (
                    campaign_engagement.get(campaign_id, 0) + 1
                )

                engagement_trend.append({
                    'timestamp': interaction.timestamp,
                    'type': interaction.interaction_type,
                    'campaign_id': campaign_id
                })

            return {
                'campaign_engagement': campaign_engagement,
                'engagement_trend': engagement_trend,
                'most_engaged_campaign': max(
                    campaign_engagement.items(),
                    key=lambda x: x[1]
                )[0] if campaign_engagement else None
            }

        except Exception as e:
            logger.error(f"Error analyzing prospect engagement: {str(e)}")
            raise

    async def _analyze_social_profiles(self, profiles: List[SocialProfile]) -> Dict:
        """Analyze social media profiles of a prospect."""
        try:
            profile_analysis = {}

            for profile in profiles:
                profile_analysis[profile.platform] = {
                    'followers': profile.followers_count,
                    'engagement_rate': profile.engagement_rate,
                    'profile_url': profile.profile_url,
                    'username': profile.username
                }

            return {
                'profiles': profile_analysis,
                'total_followers': sum(
                    profile.followers_count for profile in profiles
                ),
                'average_engagement': sum(
                    profile.engagement_rate for profile in profiles
                ) / len(profiles) if profiles else 0
            }

        except Exception as e:
            logger.error(f"Error analyzing social profiles: {str(e)}")
            raise

    async def _analyze_campaign_history(self, prospect_id: str) -> Dict:
        """Analyze prospect's campaign history."""
        try:
            # Get all campaigns the prospect has been part of
            campaigns = self.db.query(Campaign).join(
                CampaignInteraction
            ).filter(
                CampaignInteraction.prospect_id == prospect_id
            ).distinct().all()

            campaign_history = []

            for campaign in campaigns:
                # Get interactions for this campaign
                interactions = self.db.query(CampaignInteraction).filter(
                    CampaignInteraction.campaign_id == campaign.id,
                    CampaignInteraction.prospect_id == prospect_id
                ).all()

                campaign_history.append({
                    'campaign_id': str(campaign.id),
                    'name': campaign.name,
                    'status': campaign.status,
                    'interaction_count': len(interactions),
                    'last_interaction': max(
                        (i.timestamp for i in interactions),
                        default=None
                    )
                })

            return {
                'total_campaigns': len(campaigns),
                'campaign_history': campaign_history,
                'active_campaigns': sum(
                    1 for c in campaign_history if c['status'] == 'active'
                )
            }

        except Exception as e:
            logger.error(f"Error analyzing campaign history: {str(e)}")
            raise

    def _calculate_response_time(self, interaction: CampaignInteraction) -> Optional[float]:
        """Calculate response time for an interaction."""
        if not interaction.metadata or 'previous_interaction_time' not in interaction.metadata:
            return None

        previous_time = interaction.metadata['previous_interaction_time']
        response_time = (interaction.timestamp - previous_time).total_seconds() / 3600  # Convert to hours
        return response_time 