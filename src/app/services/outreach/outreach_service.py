from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, Campaign, CampaignInteraction
from services.intelligence.personalization import PersonalizationService
from services.intelligence.timing import TimingOptimizer

logger = logging.getLogger(__name__)

class OutreachService:
    def __init__(self, 
                 db: Session,
                 personalization_service: PersonalizationService,
                 timing_optimizer: TimingOptimizer):
        self.db = db
        self.personalization_service = personalization_service
        self.timing_optimizer = timing_optimizer

    async def create_campaign(self,
                            name: str,
                            description: str,
                            target_prospects: List[str],
                            start_date: datetime,
                            end_date: datetime) -> Dict:
        """
        Create a new outreach campaign.
        
        Args:
            name: Campaign name
            description: Campaign description
            target_prospects: List of prospect IDs to target
            start_date: Campaign start date
            end_date: Campaign end date
            
        Returns:
            Dictionary containing campaign details
        """
        try:
            # Create campaign
            campaign = Campaign(
                name=name,
                description=description,
                status='draft',
                start_date=start_date,
                end_date=end_date
            )
            self.db.add(campaign)
            self.db.flush()

            # Validate prospects
            for prospect_id in target_prospects:
                prospect = self.db.query(AffiliateProspect).get(prospect_id)
                if not prospect:
                    raise ValueError(f"Prospect not found: {prospect_id}")

            # Create campaign interactions
            for prospect_id in target_prospects:
                interaction = CampaignInteraction(
                    prospect_id=prospect_id,
                    campaign_id=campaign.id,
                    interaction_type='campaign_created',
                    timestamp=datetime.utcnow()
                )
                self.db.add(interaction)

            self.db.commit()
            return {
                'id': str(campaign.id),
                'name': campaign.name,
                'status': campaign.status,
                'start_date': campaign.start_date,
                'end_date': campaign.end_date,
                'target_count': len(target_prospects)
            }

        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            self.db.rollback()
            raise

    async def personalize_message(self,
                                prospect_id: str,
                                campaign_id: str,
                                template_id: str) -> Dict:
        """
        Generate a personalized message for a prospect.
        
        Args:
            prospect_id: ID of the prospect
            campaign_id: ID of the campaign
            template_id: ID of the message template
            
        Returns:
            Dictionary containing personalized message
        """
        try:
            prospect = self.db.query(AffiliateProspect).get(prospect_id)
            if not prospect:
                raise ValueError(f"Prospect not found: {prospect_id}")

            campaign = self.db.query(Campaign).get(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Get prospect context
            context = await self._get_prospect_context(prospect_id)

            # Generate personalized message
            personalized_message = await self.personalization_service.generate_message(
                template_id=template_id,
                prospect_context=context
            )

            # Record interaction
            interaction = CampaignInteraction(
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                interaction_type='message_generated',
                timestamp=datetime.utcnow(),
                metadata={'template_id': template_id}
            )
            self.db.add(interaction)
            self.db.commit()

            return {
                'prospect_id': prospect_id,
                'campaign_id': campaign_id,
                'message': personalized_message,
                'generated_at': datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error personalizing message: {str(e)}")
            self.db.rollback()
            raise

    async def optimize_timing(self,
                            prospect_id: str,
                            campaign_id: str) -> Dict:
        """
        Determine optimal timing for outreach to a prospect.
        
        Args:
            prospect_id: ID of the prospect
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary containing timing recommendations
        """
        try:
            prospect = self.db.query(AffiliateProspect).get(prospect_id)
            if not prospect:
                raise ValueError(f"Prospect not found: {prospect_id}")

            campaign = self.db.query(Campaign).get(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Get prospect's timezone and activity patterns
            context = await self._get_prospect_context(prospect_id)

            # Get optimal timing
            timing = await self.timing_optimizer.get_optimal_timing(
                prospect_context=context,
                campaign_constraints={
                    'start_date': campaign.start_date,
                    'end_date': campaign.end_date
                }
            )

            return {
                'prospect_id': prospect_id,
                'campaign_id': campaign_id,
                'recommended_times': timing['recommended_times'],
                'timezone': timing['timezone'],
                'confidence_score': timing['confidence_score']
            }

        except Exception as e:
            logger.error(f"Error optimizing timing: {str(e)}")
            raise

    async def _get_prospect_context(self, prospect_id: str) -> Dict:
        """Get comprehensive context for a prospect."""
        try:
            prospect = self.db.query(AffiliateProspect).get(prospect_id)
            if not prospect:
                raise ValueError(f"Prospect not found: {prospect_id}")

            # Get social profiles
            profiles = self.db.query(SocialProfile).filter(
                SocialProfile.prospect_id == prospect_id
            ).all()

            # Get previous interactions
            interactions = self.db.query(CampaignInteraction).filter(
                CampaignInteraction.prospect_id == prospect_id
            ).all()

            return {
                'prospect': {
                    'id': str(prospect.id),
                    'email': prospect.email,
                    'name': f"{prospect.first_name} {prospect.last_name}",
                    'company': prospect.company,
                    'website': prospect.website,
                    'score': prospect.score
                },
                'social_profiles': [
                    {
                        'platform': profile.platform,
                        'username': profile.username,
                        'followers': profile.followers_count,
                        'engagement': profile.engagement_rate
                    }
                    for profile in profiles
                ],
                'interactions': [
                    {
                        'type': interaction.interaction_type,
                        'timestamp': interaction.timestamp,
                        'metadata': interaction.metadata
                    }
                    for interaction in interactions
                ]
            }

        except Exception as e:
            logger.error(f"Error getting prospect context: {str(e)}")
            raise 