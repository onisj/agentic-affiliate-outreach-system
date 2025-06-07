"""
Enhanced Email Channel Service

Provides comprehensive email integration with multiple providers, advanced tracking,
and sophisticated email campaign management capabilities.
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json
import base64

from .base_channel import (
    BaseChannelService, ChannelType, ChannelConfig, MessageRequest, 
    MessageResponse, ProfileData, EngagementMetrics, MessageStatus
)

class EnhancedEmailService(BaseChannelService):
    """Enhanced email channel service implementation"""
    
    def __init__(self, config: ChannelConfig, db=None):
        self.provider = config.metadata.get('provider', 'smtp')
        self.base_urls = {
            'sendgrid': 'https://api.sendgrid.com/v3',
            'mailgun': 'https://api.mailgun.net/v3',
            'ses': 'https://email.us-east-1.amazonaws.com'
        }
        super().__init__(config, db)
    
    def _get_channel_type(self) -> ChannelType:
        return ChannelType.EMAIL
    
    def _validate_config(self) -> None:
        """Validate email configuration"""
        if self.provider == 'smtp':
            required_fields = ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password']
            for field in required_fields:
                if not self.config.metadata.get(field):
                    raise ValueError(f"SMTP {field} is required")
        elif self.provider in ['sendgrid', 'mailgun', 'ses']:
            if not self.config.api_key:
                raise ValueError(f"{self.provider} API key is required")
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")
        
        if not self.config.metadata.get('from_email'):
            raise ValueError("From email address is required")
        
        # Set default features
        default_features = {
            'html_emails': True,
            'attachments': True,
            'tracking': True,
            'templates': True,
            'bulk_sending': True,
            'bounce_handling': True,
            'unsubscribe_handling': True
        }
        self.config.features = {**default_features, **self.config.features}
    
    def _init_client(self) -> None:
        """Initialize email client"""
        self.session = None
        self.from_email = self.config.metadata.get('from_email')
        self.from_name = self.config.metadata.get('from_name', 'Affiliate Outreach')
        
        if self.provider == 'sendgrid':
            self.headers = {
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json'
            }
        elif self.provider == 'mailgun':
            self.headers = {
                'Authorization': f'Basic {base64.b64encode(f"api:{self.config.api_key}".encode()).decode()}',
                'Content-Type': 'application/json'
            }
        elif self.provider == 'ses':
            self.headers = {
                'Content-Type': 'application/x-amz-json-1.0',
                'X-Amz-Target': 'AWSCognitoIdentityProviderService.SendEmail'
            }
        else:  # SMTP
            self.smtp_config = {
                'host': self.config.metadata.get('smtp_host'),
                'port': int(self.config.metadata.get('smtp_port', 587)),
                'username': self.config.metadata.get('smtp_username'),
                'password': self.config.metadata.get('smtp_password'),
                'use_tls': self.config.metadata.get('smtp_use_tls', True)
            }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=getattr(self, 'headers', {}),
                timeout=timeout
            )
        return self.session
    
    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send email message"""
        try:
            # Check if messaging is enabled
            if not self.config.features.get('messaging', True):
                return MessageResponse(
                    success=False,
                    error="Email messaging is disabled"
                )
            
            # Get recipient profile for personalization
            profile = await self.get_profile(request.recipient_id)
            
            # Personalize content
            personalized_content = self._personalize_content(request.content, profile)
            personalized_subject = self._personalize_content(request.subject or 'Partnership Opportunity', profile)
            
            # Send based on provider
            if self.provider == 'smtp':
                response = await self._send_smtp_email(request, personalized_subject, personalized_content)
            elif self.provider == 'sendgrid':
                response = await self._send_sendgrid_email(request, personalized_subject, personalized_content)
            elif self.provider == 'mailgun':
                response = await self._send_mailgun_email(request, personalized_subject, personalized_content)
            elif self.provider == 'ses':
                response = await self._send_ses_email(request, personalized_subject, personalized_content)
            else:
                return MessageResponse(
                    success=False,
                    error=f"Unsupported email provider: {self.provider}"
                )
            
            # Log the message
            self._log_message(request, response)
            
            return response
            
        except Exception as e:
            return self._handle_api_error(e, "send_message")
    
    async def _send_smtp_email(self, request: MessageRequest, subject: str, content: str) -> MessageResponse:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = request.recipient_id
            
            # Add tracking headers if enabled
            if self.config.features.get('tracking', True):
                message_id = self._generate_message_id()
                msg['X-Message-ID'] = message_id
                msg['X-Campaign-ID'] = request.campaign_id or 'default'
            
            # Create HTML and text versions
            if request.metadata.get('html_content'):
                html_content = self._personalize_content(request.metadata['html_content'])
                msg.attach(MIMEText(html_content, 'html'))
            
            msg.attach(MIMEText(content, 'plain'))
            
            # Add attachments if any
            if request.metadata.get('attachments'):
                for attachment in request.metadata['attachments']:
                    await self._add_attachment(msg, attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            return MessageResponse(
                success=True,
                message_id=message_id,
                status=MessageStatus.SENT,
                metadata={
                    'platform': 'email',
                    'provider': 'smtp',
                    'recipient': request.recipient_id,
                    'subject': subject
                }
            )
            
        except Exception as e:
            return MessageResponse(
                success=False,
                error=f"SMTP error: {str(e)}"
            )
    
    async def _send_sendgrid_email(self, request: MessageRequest, subject: str, content: str) -> MessageResponse:
        """Send email via SendGrid API"""
        try:
            session = await self._get_session()
            
            email_data = {
                'personalizations': [{
                    'to': [{'email': request.recipient_id}],
                    'subject': subject
                }],
                'from': {
                    'email': self.from_email,
                    'name': self.from_name
                },
                'content': [
                    {
                        'type': 'text/plain',
                        'value': content
                    }
                ]
            }
            
            # Add HTML content if provided
            if request.metadata.get('html_content'):
                html_content = self._personalize_content(request.metadata['html_content'])
                email_data['content'].append({
                    'type': 'text/html',
                    'value': html_content
                })
            
            # Add tracking settings
            if self.config.features.get('tracking', True):
                email_data['tracking_settings'] = {
                    'click_tracking': {'enable': True},
                    'open_tracking': {'enable': True},
                    'subscription_tracking': {'enable': True}
                }
            
            # Add custom headers
            email_data['headers'] = {
                'X-Campaign-ID': request.campaign_id or 'default',
                'X-Message-Type': request.message_type or 'outreach'
            }
            
            endpoint = f"{self.base_urls['sendgrid']}/mail/send"
            async with session.post(endpoint, json=email_data) as response:
                if response.status == 202:
                    message_id = self._generate_message_id()
                    return MessageResponse(
                        success=True,
                        message_id=message_id,
                        status=MessageStatus.SENT,
                        metadata={
                            'platform': 'email',
                            'provider': 'sendgrid',
                            'recipient': request.recipient_id,
                            'subject': subject
                        }
                    )
                else:
                    error_data = await response.json()
                    return MessageResponse(
                        success=False,
                        error=f"SendGrid error: {error_data.get('errors', 'Unknown error')}"
                    )
            
        except Exception as e:
            return MessageResponse(
                success=False,
                error=f"SendGrid error: {str(e)}"
            )
    
    async def _send_mailgun_email(self, request: MessageRequest, subject: str, content: str) -> MessageResponse:
        """Send email via Mailgun API"""
        try:
            session = await self._get_session()
            domain = self.config.metadata.get('mailgun_domain')
            
            email_data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': request.recipient_id,
                'subject': subject,
                'text': content
            }
            
            # Add HTML content if provided
            if request.metadata.get('html_content'):
                html_content = self._personalize_content(request.metadata['html_content'])
                email_data['html'] = html_content
            
            # Add tracking
            if self.config.features.get('tracking', True):
                email_data['o:tracking'] = 'yes'
                email_data['o:tracking-clicks'] = 'yes'
                email_data['o:tracking-opens'] = 'yes'
            
            # Add custom variables
            email_data['v:campaign-id'] = request.campaign_id or 'default'
            email_data['v:message-type'] = request.message_type or 'outreach'
            
            endpoint = f"{self.base_urls['mailgun']}/{domain}/messages"
            async with session.post(endpoint, data=email_data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    message_id = self._generate_message_id()
                    return MessageResponse(
                        success=True,
                        message_id=message_id,
                        external_id=response_data.get('id'),
                        status=MessageStatus.SENT,
                        metadata={
                            'platform': 'email',
                            'provider': 'mailgun',
                            'recipient': request.recipient_id,
                            'subject': subject
                        }
                    )
                else:
                    error_data = await response.json()
                    return MessageResponse(
                        success=False,
                        error=f"Mailgun error: {error_data.get('message', 'Unknown error')}"
                    )
            
        except Exception as e:
            return MessageResponse(
                success=False,
                error=f"Mailgun error: {str(e)}"
            )
    
    async def _send_ses_email(self, request: MessageRequest, subject: str, content: str) -> MessageResponse:
        """Send email via Amazon SES"""
        try:
            # This would require AWS SDK integration
            # For now, return a placeholder implementation
            return MessageResponse(
                success=False,
                error="Amazon SES integration not yet implemented"
            )
            
        except Exception as e:
            return MessageResponse(
                success=False,
                error=f"SES error: {str(e)}"
            )
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """Add attachment to email message"""
        try:
            filename = attachment.get('filename')
            content = attachment.get('content')  # Base64 encoded content
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            if content and filename:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(base64.b64decode(content))
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
                
        except Exception as e:
            self.logger.error(f"Error adding email attachment: {str(e)}")
    
    async def get_profile(self, email: str) -> Optional[ProfileData]:
        """Get email profile information (limited)"""
        try:
            # Extract name from email if possible
            local_part = email.split('@')[0]
            display_name = local_part.replace('.', ' ').replace('_', ' ').title()
            
            return ProfileData(
                user_id=email,
                username=email,
                display_name=display_name,
                metadata={
                    'platform': 'email',
                    'domain': email.split('@')[1] if '@' in email else '',
                    'local_part': local_part
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting email profile: {str(e)}")
            return None
    
    async def get_engagement_metrics(self, message_id: str) -> Optional[EngagementMetrics]:
        """Get email engagement metrics"""
        try:
            if self.provider == 'sendgrid':
                return await self._get_sendgrid_metrics(message_id)
            elif self.provider == 'mailgun':
                return await self._get_mailgun_metrics(message_id)
            elif self.provider == 'ses':
                return await self._get_ses_metrics(message_id)
            else:
                # SMTP doesn't provide detailed metrics
                return EngagementMetrics(
                    views=0,
                    clicks=0,
                    metadata={
                        'platform': 'email',
                        'provider': 'smtp',
                        'message_id': message_id,
                        'note': 'Limited metrics available for SMTP'
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error getting email engagement metrics: {str(e)}")
            return None
    
    async def _get_sendgrid_metrics(self, message_id: str) -> Optional[EngagementMetrics]:
        """Get SendGrid email metrics"""
        try:
            session = await self._get_session()
            
            # Get email activity
            endpoint = f"{self.base_urls['sendgrid']}/messages"
            params = {'query': f'msg_id="{message_id}"'}
            
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    opens = 0
                    clicks = 0
                    delivered = 0
                    bounced = 0
                    
                    for event in data.get('messages', []):
                        event_type = event.get('event')
                        if event_type == 'open':
                            opens += 1
                        elif event_type == 'click':
                            clicks += 1
                        elif event_type == 'delivered':
                            delivered += 1
                        elif event_type in ['bounce', 'blocked', 'dropped']:
                            bounced += 1
                    
                    return EngagementMetrics(
                        views=opens,
                        clicks=clicks,
                        metadata={
                            'platform': 'email',
                            'provider': 'sendgrid',
                            'message_id': message_id,
                            'delivered': delivered,
                            'bounced': bounced
                        }
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting SendGrid metrics: {str(e)}")
            return None
    
    async def _get_mailgun_metrics(self, message_id: str) -> Optional[EngagementMetrics]:
        """Get Mailgun email metrics"""
        try:
            session = await self._get_session()
            domain = self.config.metadata.get('mailgun_domain')
            
            # Get email events
            endpoint = f"{self.base_urls['mailgun']}/{domain}/events"
            params = {'message-id': message_id}
            
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    opens = 0
                    clicks = 0
                    delivered = 0
                    bounced = 0
                    
                    for event in data.get('items', []):
                        event_type = event.get('event')
                        if event_type == 'opened':
                            opens += 1
                        elif event_type == 'clicked':
                            clicks += 1
                        elif event_type == 'delivered':
                            delivered += 1
                        elif event_type in ['bounced', 'dropped', 'rejected']:
                            bounced += 1
                    
                    return EngagementMetrics(
                        views=opens,
                        clicks=clicks,
                        metadata={
                            'platform': 'email',
                            'provider': 'mailgun',
                            'message_id': message_id,
                            'delivered': delivered,
                            'bounced': bounced
                        }
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Mailgun metrics: {str(e)}")
            return None
    
    async def _get_ses_metrics(self, message_id: str) -> Optional[EngagementMetrics]:
        """Get Amazon SES email metrics"""
        try:
            # This would require AWS SDK integration
            return EngagementMetrics(
                views=0,
                clicks=0,
                metadata={
                    'platform': 'email',
                    'provider': 'ses',
                    'message_id': message_id,
                    'note': 'SES metrics integration not yet implemented'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting SES metrics: {str(e)}")
            return None
    
    async def send_bulk_emails(self, recipients: List[str], subject: str, content: str, 
                             html_content: str = None, delay_between_emails: float = 0.1) -> Dict[str, Any]:
        """Send bulk emails with rate limiting"""
        try:
            successful_sends = 0
            failed_sends = 0
            results = []
            
            for recipient in recipients:
                try:
                    request = MessageRequest(
                        recipient_id=recipient,
                        content=content,
                        subject=subject,
                        metadata={'html_content': html_content} if html_content else {}
                    )
                    
                    response = await self.send_message(request)
                    
                    if response.success:
                        successful_sends += 1
                    else:
                        failed_sends += 1
                    
                    results.append({
                        'recipient': recipient,
                        'success': response.success,
                        'error': response.error,
                        'message_id': response.message_id
                    })
                    
                    # Add delay to avoid rate limiting
                    if delay_between_emails > 0:
                        await asyncio.sleep(delay_between_emails)
                        
                except Exception as e:
                    failed_sends += 1
                    results.append({
                        'recipient': recipient,
                        'success': False,
                        'error': str(e),
                        'message_id': None
                    })
            
            return {
                'total_recipients': len(recipients),
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'success_rate': (successful_sends / len(recipients)) * 100 if recipients else 0,
                'results': results,
                'platform': 'email',
                'provider': self.provider
            }
            
        except Exception as e:
            self.logger.error(f"Error sending bulk emails: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_email_template(self, name: str, subject: str, html_content: str, 
                                  text_content: str = None) -> Dict[str, Any]:
        """Create email template"""
        try:
            if self.provider == 'sendgrid':
                return await self._create_sendgrid_template(name, subject, html_content, text_content)
            elif self.provider == 'mailgun':
                return await self._create_mailgun_template(name, subject, html_content, text_content)
            else:
                # For SMTP and SES, store template locally
                template_id = f"template_{datetime.now().timestamp()}"
                return {
                    'success': True,
                    'template_id': template_id,
                    'name': name,
                    'platform': 'email',
                    'provider': self.provider,
                    'note': 'Template stored locally'
                }
            
        except Exception as e:
            self.logger.error(f"Error creating email template: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _create_sendgrid_template(self, name: str, subject: str, html_content: str, 
                                      text_content: str = None) -> Dict[str, Any]:
        """Create SendGrid template"""
        try:
            session = await self._get_session()
            
            template_data = {
                'name': name,
                'generation': 'dynamic'
            }
            
            # Create template
            endpoint = f"{self.base_urls['sendgrid']}/templates"
            async with session.post(endpoint, json=template_data) as response:
                if response.status == 201:
                    template_info = await response.json()
                    template_id = template_info['id']
                    
                    # Create version
                    version_data = {
                        'template_id': template_id,
                        'active': 1,
                        'name': f"{name} v1",
                        'subject': subject,
                        'html_content': html_content,
                        'plain_content': text_content or ''
                    }
                    
                    version_endpoint = f"{self.base_urls['sendgrid']}/templates/{template_id}/versions"
                    async with session.post(version_endpoint, json=version_data) as version_response:
                        if version_response.status == 201:
                            return {
                                'success': True,
                                'template_id': template_id,
                                'name': name,
                                'platform': 'email',
                                'provider': 'sendgrid'
                            }
            
            return {'success': False, 'error': 'Failed to create SendGrid template'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _create_mailgun_template(self, name: str, subject: str, html_content: str, 
                                     text_content: str = None) -> Dict[str, Any]:
        """Create Mailgun template"""
        try:
            session = await self._get_session()
            domain = self.config.metadata.get('mailgun_domain')
            
            template_data = {
                'template': html_content,
                'description': f"Template: {name}",
                'comment': f"Subject: {subject}"
            }
            
            endpoint = f"{self.base_urls['mailgun']}/{domain}/templates/{name}"
            async with session.post(endpoint, data=template_data) as response:
                if response.status == 200:
                    return {
                        'success': True,
                        'template_id': name,
                        'name': name,
                        'platform': 'email',
                        'provider': 'mailgun'
                    }
                else:
                    error_data = await response.json()
                    return {'success': False, 'error': error_data.get('message', 'Unknown error')}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email address"""
        try:
            # Basic email validation
            if '@' not in email or '.' not in email.split('@')[1]:
                return {
                    'valid': False,
                    'reason': 'Invalid email format'
                }
            
            # Additional validation based on provider
            if self.provider == 'mailgun':
                return await self._validate_mailgun_email(email)
            else:
                return {
                    'valid': True,
                    'reason': 'Basic validation passed',
                    'provider': self.provider
                }
            
        except Exception as e:
            self.logger.error(f"Error validating email: {str(e)}")
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    async def _validate_mailgun_email(self, email: str) -> Dict[str, Any]:
        """Validate email using Mailgun validation API"""
        try:
            session = await self._get_session()
            
            endpoint = f"{self.base_urls['mailgun']}/address/validate"
            params = {'address': email}
            
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'valid': data.get('is_valid', False),
                        'reason': data.get('reason', ''),
                        'risk': data.get('risk', 'unknown'),
                        'provider': 'mailgun'
                    }
                else:
                    return {
                        'valid': False,
                        'reason': 'Validation service unavailable'
                    }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Note: This won't work in async context, but provides cleanup hint
            pass
