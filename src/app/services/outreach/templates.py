"""
Message Templates Service

This module contains message templates and personalization logic for different channels.
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """Message template types"""
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP = "follow_up"
    PARTNERSHIP_PROPOSAL = "partnership_proposal"
    THANK_YOU = "thank_you"
    REMINDER = "reminder"

class MessageTemplates:
    """Message templates for different channels and scenarios"""
    
    TEMPLATES = {
        "linkedin": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name},

I came across your profile and was impressed by your work in {industry}. Your content about {topic} particularly caught my attention.

I'm reaching out because I think you might be interested in our affiliate program. We offer competitive commissions and a supportive community of creators.

Would you be open to a quick chat about potential collaboration?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

I wanted to follow up on my previous message about our affiliate program. I understand you're busy, but I'd love to share more details about how we could work together.

Let me know if you'd like to schedule a quick call.

Best regards,
{signature}
            """
        },
        "twitter": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name}! 👋

I've been following your amazing content about {topic}. Your insights are truly valuable!

I'd love to chat about our affiliate program. We offer great opportunities for creators like you.

DM me if you're interested in learning more! 

{hashtags}
            """,
            TemplateType.FOLLOW_UP: """
Hey {first_name}! 

Just checking if you had a chance to look into our affiliate program. I'd be happy to answer any questions you might have.

Let's connect! 

{hashtags}
            """
        },
        "instagram": {
            TemplateType.INITIAL_OUTREACH: """
Hey {first_name}! 👋

Love your content about {topic}! Your style is exactly what we're looking for in our affiliate program.

We offer competitive rates and creative freedom. Would you be interested in learning more?

DM me to chat! 

{hashtags}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name}! 

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested! 

{hashtags}
            """
        },
        "facebook": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name},

I've been following your page and really enjoy your content about {topic}. Your insights are valuable to the community.

I'm reaching out because I think you'd be a great fit for our affiliate program. We offer competitive commissions and a supportive community.

Would you be interested in learning more?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

I wanted to follow up on my message about our affiliate program. I'd be happy to share more details about how we could work together.

Let me know if you'd like to schedule a quick call.

Best regards,
{signature}
            """
        },
        "whatsapp": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name}! 👋

I came across your work in {industry} and was really impressed. Your content about {topic} is particularly engaging.

I'm reaching out about our affiliate program. We offer competitive rates and a great community of creators.

Would you be interested in learning more?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested!

Best regards,
{signature}
            """
        },
        "youtube": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name},

I've been watching your videos about {topic} and really enjoy your content. Your style and expertise are exactly what we're looking for.

I'm reaching out about our affiliate program. We offer competitive rates and creative freedom.

Would you be interested in learning more?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested!

Best regards,
{signature}
            """
        },
        "tiktok": {
            TemplateType.INITIAL_OUTREACH: """
Hey {first_name}! 👋

Love your TikTok content about {topic}! Your style is exactly what we're looking for in our affiliate program.

We offer competitive rates and creative freedom. Would you be interested in learning more?

DM me to chat! 

{hashtags}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name}! 

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested! 

{hashtags}
            """
        },
        "reddit": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name},

I've been following your posts in r/{subreddit} and really appreciate your insights about {topic}.

I'm reaching out about our affiliate program. We offer competitive rates and a great community of creators.

Would you be interested in learning more?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested!

Best regards,
{signature}
            """
        },
        "telegram": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name}! 👋

I came across your channel and was impressed by your content about {topic}.

I'm reaching out about our affiliate program. We offer competitive rates and a great community of creators.

Would you be interested in learning more?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested!

Best regards,
{signature}
            """
        },
        "discord": {
            TemplateType.INITIAL_OUTREACH: """
Hi {first_name}! 👋

I've been following your server and really enjoy your content about {topic}.

I'm reaching out about our affiliate program. We offer competitive rates and a great community of creators.

Would you be interested in learning more?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Hi {first_name},

Just following up about our affiliate program. I'd love to share more details about how we could collaborate.

Let me know if you're interested!

Best regards,
{signature}
            """
        },
        "email": {
            TemplateType.INITIAL_OUTREACH: """
Subject: Partnership Opportunity - {company_name} Affiliate Program

Hi {first_name},

I hope this email finds you well. I came across your work in {industry} and was particularly impressed by your expertise in {topic}.

I'm reaching out because I think you'd be a great fit for our affiliate program. We offer:
- Competitive commission rates
- Dedicated support team
- Creative freedom
- Regular payouts
- Growing community of creators

Would you be interested in learning more about how we could work together?

Best regards,
{signature}
            """,
            TemplateType.FOLLOW_UP: """
Subject: Following Up - {company_name} Affiliate Program

Hi {first_name},

I wanted to follow up on my previous email about our affiliate program. I understand you're busy, but I'd love to share more details about how we could collaborate.

Let me know if you'd like to schedule a quick call to discuss further.

Best regards,
{signature}
            """
        }
    }

    @classmethod
    def get_template(cls, channel: str, template_type: TemplateType) -> Optional[str]:
        """Get a message template for a specific channel and type"""
        try:
            channel_templates = cls.TEMPLATES.get(channel.lower())
            if not channel_templates:
                logger.warning(f"No templates found for channel: {channel}")
                return None

            template = channel_templates.get(template_type)
            if not template:
                logger.warning(f"No template of type {template_type} found for channel: {channel}")
                return None

            return template.strip()

        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return None

    @classmethod
    def format_template(cls, template: str, context: Dict[str, Any]) -> str:
        """Format a template with context variables"""
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error(f"Missing context variable: {str(e)}")
            return template
        except Exception as e:
            logger.error(f"Error formatting template: {str(e)}")
            return template 