"""
Campaign Orchestration Engine

This module implements the core campaign orchestration logic that manages
multi-channel outreach campaigns with intelligent sequencing and personalization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

class CampaignStatus(Enum):
    """Campaign status types"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MessageChannel(Enum):
    """Available message channels"""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"

class MessageStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"

@dataclass
class ProspectData:
    """Prospect information for personalization"""
    prospect_id: str
    name: str
    company: Optional[str]
    title: Optional[str]
    industry: Optional[str]
    location: Optional[str]
    platform: str
    profile_url: str
    bio: Optional[str]
    recent_posts: List[Dict[str, Any]] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    engagement_history: Dict[str, Any] = field(default_factory=dict)
    contact_info: Dict[str, str] = field(default_factory=dict)

@dataclass
class MessageTemplate:
    """Message template with personalization placeholders"""
    template_id: str
    name: str
    subject_template: Optional[str]
    body_template: str
    channel: MessageChannel
    personalization_fields: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CampaignMessage:
    """Individual message in a campaign sequence"""
    message_id: str
    prospect_id: str
    campaign_id: str
    sequence_step: int
    channel: MessageChannel
    subject: Optional[str]
    content: str
    scheduled_time: datetime
    status: MessageStatus
    personalization_data: Dict[str, Any] = field(default_factory=dict)
    delivery_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CampaignSequence:
    """Defines the sequence of messages in a campaign"""
    sequence_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    total_steps: int = 0
    default_delays: Dict[int, timedelta] = field(default_factory=dict)

@dataclass
class Campaign:
    """Campaign configuration and state"""
    campaign_id: str
    name: str
    description: str
    status: CampaignStatus
    sequence: CampaignSequence
    target_prospects: List[str]
    personalization_config: Dict[str, Any]
    timing_config: Dict[str, Any]
    ab_test_config: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

class PersonalizationEngine:
    """AI-powered personalization engine for messages"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.get('model', 'gpt-4'),
            temperature=config.get('temperature', 0.3),
            max_tokens=config.get('max_tokens', 1000)
        )
    
    async def personalize_message(
        self, 
        template: MessageTemplate, 
        prospect: ProspectData,
        context: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Generate personalized message content"""
        logger.info(f"Personalizing message for prospect: {prospect.prospect_id}")
        
        # Create personalization prompt
        prompt = self._create_personalization_prompt(template, prospect, context or {})
        
        try:
            # Generate personalized content
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Parse the response to extract subject and body
            personalized_content = self._parse_personalization_response(response.content)
            
            return personalized_content
            
        except Exception as e:
            logger.error(f"Error personalizing message: {str(e)}")
            # Fallback to template with basic variable substitution
            return self._basic_personalization(template, prospect)
    
    def _create_personalization_prompt(
        self, 
        template: MessageTemplate, 
        prospect: ProspectData,
        context: Dict[str, Any]
    ) -> str:
        """Create prompt for AI personalization"""
        prompt = f"""
        You are an expert at creating personalized outreach messages for affiliate marketing.
        
        Prospect Information:
        - Name: {prospect.name}
        - Company: {prospect.company or 'Unknown'}
        - Title: {prospect.title or 'Unknown'}
        - Industry: {prospect.industry or 'Unknown'}
        - Location: {prospect.location or 'Unknown'}
        - Platform: {prospect.platform}
        - Bio: {prospect.bio or 'No bio available'}
        - Interests: {', '.join(prospect.interests) if prospect.interests else 'None specified'}
        
        Message Template:
        Subject: {template.subject_template or 'No subject template'}
        Body: {template.body_template}
        
        Context: {context}
        
        Instructions:
        1. Personalize the message to feel genuinely crafted for this specific prospect
        2. Reference relevant details from their profile naturally
        3. Maintain a professional but friendly tone
        4. Keep the core message and call-to-action from the template
        5. Ensure the message feels authentic and not obviously automated
        6. Respect cultural and professional norms
        
        Please provide the personalized message in this format:
        SUBJECT: [personalized subject line]
        BODY: [personalized message body]
        """
        
        return prompt
    
    def _parse_personalization_response(self, response: str) -> Dict[str, str]:
        """Parse AI response to extract subject and body"""
        lines = response.strip().split('\n')
        subject = ""
        body = ""
        
        current_section = None
        for line in lines:
            if line.startswith('SUBJECT:'):
                subject = line.replace('SUBJECT:', '').strip()
                current_section = 'subject'
            elif line.startswith('BODY:'):
                body = line.replace('BODY:', '').strip()
                current_section = 'body'
            elif current_section == 'body' and line.strip():
                body += '\n' + line
        
        return {
            'subject': subject,
            'body': body.strip()
        }
    
    def _basic_personalization(self, template: MessageTemplate, prospect: ProspectData) -> Dict[str, str]:
        """Fallback basic personalization using simple variable substitution"""
        variables = {
            'name': prospect.name,
            'first_name': prospect.name.split()[0] if prospect.name else '',
            'company': prospect.company or '',
            'title': prospect.title or '',
            'industry': prospect.industry or '',
            'location': prospect.location or ''
        }
        
        subject = template.subject_template or ''
        body = template.body_template
        
        # Simple variable substitution
        for var, value in variables.items():
            subject = subject.replace(f'{{{var}}}', value)
            body = body.replace(f'{{{var}}}', value)
        
        return {
            'subject': subject,
            'body': body
        }

class TimingOptimizer:
    """Optimizes message timing based on prospect behavior and platform data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timezone_data = config.get('timezone_data', {})
        self.platform_optimal_times = config.get('platform_optimal_times', {})
    
    async def calculate_optimal_send_time(
        self, 
        prospect: ProspectData, 
        channel: MessageChannel,
        base_time: datetime = None
    ) -> datetime:
        """Calculate optimal send time for a prospect"""
        base_time = base_time or datetime.now()
        
        # Get prospect's timezone
        prospect_timezone = self._get_prospect_timezone(prospect)
        
        # Get platform-specific optimal times
        optimal_hours = self.platform_optimal_times.get(channel.value, [9, 14, 17])
        
        # Get prospect's historical engagement patterns
        engagement_patterns = self._analyze_engagement_patterns(prospect)
        
        # Calculate optimal time
        optimal_time = self._calculate_optimal_time(
            base_time, 
            prospect_timezone, 
            optimal_hours, 
            engagement_patterns
        )
        
        return optimal_time
    
    def _get_prospect_timezone(self, prospect: ProspectData) -> str:
        """Determine prospect's timezone from location data"""
        # This would use a timezone mapping service
        # Placeholder implementation
        return 'UTC'
    
    def _analyze_engagement_patterns(self, prospect: ProspectData) -> Dict[str, Any]:
        """Analyze prospect's historical engagement patterns"""
        # This would analyze when the prospect is most active
        # Placeholder implementation
        return {
            'preferred_hours': [9, 14, 17],
            'preferred_days': ['monday', 'tuesday', 'wednesday', 'thursday'],
            'response_rate_by_hour': {}
        }
    
    def _calculate_optimal_time(
        self, 
        base_time: datetime, 
        timezone: str, 
        optimal_hours: List[int],
        engagement_patterns: Dict[str, Any]
    ) -> datetime:
        """Calculate the optimal send time"""
        # Simple implementation - use next optimal hour
        current_hour = base_time.hour
        next_optimal_hour = min([h for h in optimal_hours if h > current_hour], default=optimal_hours[0])
        
        if next_optimal_hour <= current_hour:
            # Next day
            optimal_time = base_time.replace(hour=next_optimal_hour, minute=0, second=0) + timedelta(days=1)
        else:
            # Same day
            optimal_time = base_time.replace(hour=next_optimal_hour, minute=0, second=0)
        
        return optimal_time

class CampaignOrchestrator:
    """Main orchestrator for managing outreach campaigns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.personalization_engine = PersonalizationEngine(config.get('personalization', {}))
        self.timing_optimizer = TimingOptimizer(config.get('timing', {}))
        self.active_campaigns: Dict[str, Campaign] = {}
        self.message_queue: List[CampaignMessage] = []
    
    async def create_campaign(
        self, 
        name: str,
        description: str,
        sequence: CampaignSequence,
        prospects: List[ProspectData],
        config: Dict[str, Any]
    ) -> Campaign:
        """Create a new outreach campaign"""
        campaign_id = f"campaign_{datetime.now().timestamp()}"
        
        campaign = Campaign(
            campaign_id=campaign_id,
            name=name,
            description=description,
            status=CampaignStatus.DRAFT,
            sequence=sequence,
            target_prospects=[p.prospect_id for p in prospects],
            personalization_config=config.get('personalization', {}),
            timing_config=config.get('timing', {}),
            ab_test_config=config.get('ab_testing')
        )
        
        self.active_campaigns[campaign_id] = campaign
        
        logger.info(f"Created campaign: {campaign_id}")
        return campaign
    
    async def start_campaign(self, campaign_id: str) -> bool:
        """Start an active campaign"""
        campaign = self.active_campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")
        
        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError(f"Campaign must be in DRAFT status to start")
        
        campaign.status = CampaignStatus.ACTIVE
        campaign.started_at = datetime.now()
        
        # Generate and schedule initial messages
        await self._generate_campaign_messages(campaign)
        
        logger.info(f"Started campaign: {campaign_id}")
        return True
    
    async def _generate_campaign_messages(self, campaign: Campaign) -> None:
        """Generate all messages for a campaign"""
        for prospect_id in campaign.target_prospects:
            # Get prospect data (this would come from the database)
            prospect = await self._get_prospect_data(prospect_id)
            
            # Generate messages for each step in the sequence
            for step_index, step in enumerate(campaign.sequence.steps):
                message = await self._create_campaign_message(
                    campaign, 
                    prospect, 
                    step_index, 
                    step
                )
                self.message_queue.append(message)
    
    async def _create_campaign_message(
        self, 
        campaign: Campaign, 
        prospect: ProspectData,
        step_index: int,
        step_config: Dict[str, Any]
    ) -> CampaignMessage:
        """Create a single campaign message"""
        # Get message template
        template = await self._get_message_template(step_config['template_id'])
        
        # Personalize the message
        personalized_content = await self.personalization_engine.personalize_message(
            template, 
            prospect,
            step_config.get('context', {})
        )
        
        # Calculate optimal send time
        base_delay = campaign.sequence.default_delays.get(step_index, timedelta(days=1))
        base_time = datetime.now() + (base_delay * step_index)
        
        optimal_time = await self.timing_optimizer.calculate_optimal_send_time(
            prospect,
            template.channel,
            base_time
        )
        
        # Create message
        message = CampaignMessage(
            message_id=f"msg_{datetime.now().timestamp()}_{prospect.prospect_id}_{step_index}",
            prospect_id=prospect.prospect_id,
            campaign_id=campaign.campaign_id,
            sequence_step=step_index,
            channel=template.channel,
            subject=personalized_content.get('subject'),
            content=personalized_content['body'],
            scheduled_time=optimal_time,
            status=MessageStatus.SCHEDULED,
            personalization_data=personalized_content
        )
        
        return message
    
    async def _get_prospect_data(self, prospect_id: str) -> ProspectData:
        """Retrieve prospect data from database"""
        # This would query the database for prospect information
        # Placeholder implementation
        return ProspectData(
            prospect_id=prospect_id,
            name="John Doe",
            company="Example Corp",
            title="Marketing Manager",
            industry="Technology",
            location="San Francisco, CA",
            platform="linkedin",
            profile_url="https://linkedin.com/in/johndoe",
            bio="Marketing professional with 5+ years experience"
        )
    
    async def _get_message_template(self, template_id: str) -> MessageTemplate:
        """Retrieve message template from database"""
        # This would query the database for template information
        # Placeholder implementation
        return MessageTemplate(
            template_id=template_id,
            name="Initial Outreach",
            subject_template="Partnership opportunity with {company}",
            body_template="Hi {first_name},\n\nI hope this message finds you well...",
            channel=MessageChannel.EMAIL
        )
    
    async def process_message_queue(self) -> Dict[str, Any]:
        """Process scheduled messages in the queue"""
        current_time = datetime.now()
        messages_sent = 0
        messages_failed = 0
        
        for message in self.message_queue[:]:  # Copy to avoid modification during iteration
            if message.status == MessageStatus.SCHEDULED and message.scheduled_time <= current_time:
                try:
                    # Send the message
                    success = await self._send_message(message)
                    if success:
                        message.status = MessageStatus.SENT
                        messages_sent += 1
                    else:
                        message.status = MessageStatus.FAILED
                        messages_failed += 1
                    
                    # Remove from queue
                    self.message_queue.remove(message)
                    
                except Exception as e:
                    logger.error(f"Error sending message {message.message_id}: {str(e)}")
                    message.status = MessageStatus.FAILED
                    messages_failed += 1
        
        return {
            "messages_sent": messages_sent,
            "messages_failed": messages_failed,
            "queue_size": len(self.message_queue)
        }
    
    async def _send_message(self, message: CampaignMessage) -> bool:
        """Send a message through the appropriate channel"""
        logger.info(f"Sending message {message.message_id} via {message.channel.value}")
        
        # This would integrate with the actual delivery services
        # Placeholder implementation
        if message.channel == MessageChannel.EMAIL:
            return await self._send_email(message)
        elif message.channel == MessageChannel.LINKEDIN:
            return await self._send_linkedin_message(message)
        else:
            logger.warning(f"Unsupported channel: {message.channel}")
            return False
    
    async def _send_email(self, message: CampaignMessage) -> bool:
        """Send email message"""
        # Integration with email service
        return True
    
    async def _send_linkedin_message(self, message: CampaignMessage) -> bool:
        """Send LinkedIn message"""
        # Integration with LinkedIn API
        return True
    
    def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get current campaign status and metrics"""
        campaign = self.active_campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")
        
        # Calculate metrics
        total_messages = len([m for m in self.message_queue if m.campaign_id == campaign_id])
        sent_messages = len([m for m in self.message_queue if m.campaign_id == campaign_id and m.status == MessageStatus.SENT])
        
        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "created_at": campaign.created_at.isoformat(),
            "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
            "total_prospects": len(campaign.target_prospects),
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "completion_rate": sent_messages / total_messages if total_messages > 0 else 0
        }
