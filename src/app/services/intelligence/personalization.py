from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, CampaignInteraction, Content
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class PersonalizationService:
    def __init__(self, db: Session):
        self.db = db
        self.template_variables = {
            'prospect': [
                'first_name',
                'last_name',
                'company',
                'website',
                'industry'
            ],
            'campaign': [
                'name',
                'type',
                'goal'
            ],
            'content': [
                'title',
                'description',
                'url'
            ]
        }

    async def generate_message(self,
                             template_id: str,
                             prospect_context: Dict) -> Dict:
        """
        Generate a personalized message using a template and prospect context.
        
        Args:
            template_id: ID of the message template
            prospect_context: Dictionary containing prospect information
            
        Returns:
            Dictionary containing personalized message
        """
        try:
            # Get template
            template = self.db.query(Content).get(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            # Extract template content
            template_content = template.data.get('content', '')
            template_type = template.data.get('type', 'email')

            # Generate personalized content
            personalized_content = await self._personalize_content(
                template_content,
                prospect_context,
                template_type
            )

            # Generate subject if it's an email
            subject = None
            if template_type == 'email':
                subject = await self._generate_subject(
                    template.data.get('subject', ''),
                    prospect_context
                )

            return {
                'template_id': template_id,
                'type': template_type,
                'content': personalized_content,
                'subject': subject,
                'personalization_data': {
                    'variables_used': self._get_used_variables(personalized_content),
                    'prospect_context': prospect_context
                }
            }

        except Exception as e:
            logger.error(f"Error generating message: {str(e)}")
            raise

    async def _personalize_content(self,
                                 content: str,
                                 context: Dict,
                                 content_type: str) -> str:
        """Personalize content with prospect context."""
        try:
            # Replace template variables
            personalized = content
            
            # Replace prospect variables
            for var in self.template_variables['prospect']:
                if var in context.get('prospect', {}):
                    placeholder = f"{{prospect.{var}}}"
                    value = context['prospect'][var]
                    personalized = personalized.replace(placeholder, str(value))

            # Replace campaign variables
            for var in self.template_variables['campaign']:
                if var in context.get('campaign', {}):
                    placeholder = f"{{campaign.{var}}}"
                    value = context['campaign'][var]
                    personalized = personalized.replace(placeholder, str(value))

            # Replace content variables
            for var in self.template_variables['content']:
                if var in context.get('content', {}):
                    placeholder = f"{{content.{var}}}"
                    value = context['content'][var]
                    personalized = personalized.replace(placeholder, str(value))

            # Add dynamic content based on type
            if content_type == 'email':
                personalized = await self._add_email_personalization(
                    personalized,
                    context
                )
            elif content_type == 'social':
                personalized = await self._add_social_personalization(
                    personalized,
                    context
                )

            return personalized

        except Exception as e:
            logger.error(f"Error personalizing content: {str(e)}")
            raise

    async def _generate_subject(self,
                              template_subject: str,
                              context: Dict) -> str:
        """Generate personalized email subject."""
        try:
            # Replace variables in subject
            subject = template_subject
            
            # Replace prospect variables
            for var in self.template_variables['prospect']:
                if var in context.get('prospect', {}):
                    placeholder = f"{{prospect.{var}}}"
                    value = context['prospect'][var]
                    subject = subject.replace(placeholder, str(value))

            # Add dynamic subject line if empty
            if not subject.strip():
                subject = await self._generate_dynamic_subject(context)

            return subject

        except Exception as e:
            logger.error(f"Error generating subject: {str(e)}")
            return "Important Message"

    async def _add_email_personalization(self,
                                       content: str,
                                       context: Dict) -> str:
        """Add email-specific personalization."""
        try:
            # Add personalized greeting
            greeting = await self._generate_greeting(context)
            content = f"{greeting}\n\n{content}"

            # Add personalized signature
            signature = await self._generate_signature(context)
            content = f"{content}\n\n{signature}"

            return content

        except Exception as e:
            logger.error(f"Error adding email personalization: {str(e)}")
            return content

    async def _add_social_personalization(self,
                                        content: str,
                                        context: Dict) -> str:
        """Add social media-specific personalization."""
        try:
            # Add relevant hashtags
            hashtags = await self._generate_hashtags(context)
            if hashtags:
                content = f"{content}\n\n{hashtags}"

            # Add call to action
            cta = await self._generate_cta(context)
            if cta:
                content = f"{content}\n\n{cta}"

            return content

        except Exception as e:
            logger.error(f"Error adding social personalization: {str(e)}")
            return content

    async def _generate_greeting(self, context: Dict) -> str:
        """Generate personalized greeting."""
        try:
            prospect = context.get('prospect', {})
            first_name = prospect.get('first_name', '')
            
            if first_name:
                return f"Hi {first_name},"
            return "Hello,"

        except Exception as e:
            logger.error(f"Error generating greeting: {str(e)}")
            return "Hello,"

    async def _generate_signature(self, context: Dict) -> str:
        """Generate personalized signature."""
        try:
            return "Best regards,\nThe Team"
        except Exception as e:
            logger.error(f"Error generating signature: {str(e)}")
            return "Best regards"

    async def _generate_hashtags(self, context: Dict) -> str:
        """Generate relevant hashtags."""
        try:
            hashtags = []
            
            # Add industry hashtags
            if 'industry' in context.get('prospect', {}):
                industry = context['prospect']['industry']
                hashtags.append(f"#{industry.replace(' ', '')}")
            
            # Add campaign hashtags
            if 'campaign' in context:
                campaign_name = context['campaign'].get('name', '')
                if campaign_name:
                    hashtags.append(f"#{campaign_name.replace(' ', '')}")
            
            return ' '.join(hashtags) if hashtags else ''

        except Exception as e:
            logger.error(f"Error generating hashtags: {str(e)}")
            return ''

    async def _generate_cta(self, context: Dict) -> str:
        """Generate call to action."""
        try:
            campaign = context.get('campaign', {})
            campaign_type = campaign.get('type', '')
            
            if campaign_type == 'partnership':
                return "Interested in partnering with us? Let's talk!"
            elif campaign_type == 'promotion':
                return "Ready to promote our products? Get started today!"
            else:
                return "Learn more about our affiliate program!"

        except Exception as e:
            logger.error(f"Error generating CTA: {str(e)}")
            return "Learn more!"

    async def _generate_dynamic_subject(self, context: Dict) -> str:
        """Generate dynamic subject line."""
        try:
            prospect = context.get('prospect', {})
            campaign = context.get('campaign', {})
            
            # Get prospect's company
            company = prospect.get('company', '')
            
            # Get campaign goal
            goal = campaign.get('goal', '')
            
            if company and goal:
                return f"Partner with {company} - {goal}"
            elif company:
                return f"Exciting Partnership Opportunity with {company}"
            else:
                return "Exciting Partnership Opportunity"

        except Exception as e:
            logger.error(f"Error generating dynamic subject: {str(e)}")
            return "Exciting Partnership Opportunity"

    def _get_used_variables(self, content: str) -> List[str]:
        """Get list of variables used in content."""
        try:
            used_vars = []
            
            # Check for all possible variables
            for category, variables in self.template_variables.items():
                for var in variables:
                    placeholder = f"{{{category}.{var}}}"
                    if placeholder in content:
                        used_vars.append(f"{category}.{var}")
            
            return used_vars

        except Exception as e:
            logger.error(f"Error getting used variables: {str(e)}")
            return []

    async def analyze_personalization_effectiveness(self,
                                                  prospect_id: str) -> Dict:
        """
        Analyze effectiveness of personalization for a prospect.
        
        Args:
            prospect_id: ID of the prospect to analyze
            
        Returns:
            Dictionary containing personalization effectiveness analysis
        """
        try:
            # Get prospect's interactions
            interactions = self.db.query(CampaignInteraction).filter(
                CampaignInteraction.prospect_id == prospect_id
            ).all()

            # Analyze personalization effectiveness
            effectiveness = {
                'total_interactions': len(interactions),
                'personalized_interactions': 0,
                'response_rate': 0,
                'engagement_rate': 0,
                'variable_effectiveness': {}
            }

            for interaction in interactions:
                if interaction.metadata and 'personalization_data' in interaction.metadata:
                    effectiveness['personalized_interactions'] += 1
                    
                    # Analyze variable effectiveness
                    used_vars = interaction.metadata['personalization_data'].get(
                        'variables_used', []
                    )
                    for var in used_vars:
                        if var not in effectiveness['variable_effectiveness']:
                            effectiveness['variable_effectiveness'][var] = {
                                'count': 0,
                                'responses': 0
                            }
                        effectiveness['variable_effectiveness'][var]['count'] += 1
                        
                        if interaction.interaction_type == 'response':
                            effectiveness['variable_effectiveness'][var]['responses'] += 1

            # Calculate rates
            if effectiveness['total_interactions'] > 0:
                effectiveness['response_rate'] = (
                    sum(1 for i in interactions if i.interaction_type == 'response') /
                    effectiveness['total_interactions']
                )
                effectiveness['engagement_rate'] = (
                    sum(1 for i in interactions if i.interaction_type in ['click', 'open']) /
                    effectiveness['total_interactions']
                )

            # Calculate variable effectiveness
            for var, stats in effectiveness['variable_effectiveness'].items():
                if stats['count'] > 0:
                    stats['effectiveness'] = stats['responses'] / stats['count']
                else:
                    stats['effectiveness'] = 0

            return effectiveness

        except Exception as e:
            logger.error(f"Error analyzing personalization effectiveness: {str(e)}")
            raise 