"""
Email Client

This module provides a client for sending emails using SMTP, including
authentication, rate limiting, and message sending capabilities.
"""

import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from config.settings import get_settings
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()

class EmailClient(BaseAPIClient):
    """Email client with rate limiting and authentication"""
    
    def __init__(self):
        super().__init__('Email')
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        
        # Rate limiting settings
        self.rate_limits = {
            'email': {'calls': 100, 'period': 3600},  # 100 emails per hour
            'batch': {'calls': 1000, 'period': 86400}  # 1000 batch emails per day
        }
        self.call_timestamps = {
            'email': [],
            'batch': []
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with SMTP server"""
        try:
            smtp = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            )
            await smtp.connect()
            await smtp.login(self.smtp_username, self.smtp_password)
            await smtp.quit()
            return True
                
        except Exception as e:
            self.log_api_error('authentication', e)
            return False
    
    async def send_message(
        self,
        recipient: str,
        message: str,
        subject: str = "New Message",
        html: bool = False
    ) -> bool:
        """Send an email message"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('email'):
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            if html:
                msg.attach(MIMEText(message, 'html'))
            else:
                msg.attach(MIMEText(message, 'plain'))
            
            smtp = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            )
            await smtp.connect()
            await smtp.login(self.smtp_username, self.smtp_password)
            await smtp.send_message(msg)
            await smtp.quit()
            
            return True
                
        except Exception as e:
            self.log_api_error('send_message', e)
            return False
    
    async def get_user_profile(self, email: str) -> Optional[Dict[str, Any]]:
        """Get an email user's profile (not applicable for email)"""
        return None
    
    async def send_batch_emails(
        self,
        recipients: List[str],
        message: str,
        subject: str = "New Message",
        html: bool = False
    ) -> bool:
        """Send emails to multiple recipients"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('batch'):
                return False
            
            smtp = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            )
            await smtp.connect()
            await smtp.login(self.smtp_username, self.smtp_password)
            
            for recipient in recipients:
                msg = MIMEMultipart()
                msg['From'] = self.from_email
                msg['To'] = recipient
                msg['Subject'] = subject
                
                if html:
                    msg.attach(MIMEText(message, 'html'))
                else:
                    msg.attach(MIMEText(message, 'plain'))
                
                await smtp.send_message(msg)
            
            await smtp.quit()
            return True
                
        except Exception as e:
            self.log_api_error('send_batch_emails', e)
            return False
    
    async def send_template_email(
        self,
        recipient: str,
        template_name: str,
        template_data: Dict[str, Any],
        subject: str = "New Message"
    ) -> bool:
        """Send an email using a template"""
        try:
            if not await self.authenticate():
                return False
                
            if not await self.handle_rate_limit('email'):
                return False
            
            # TODO: Implement template rendering
            message = f"Template: {template_name}\nData: {template_data}"
            
            return await self.send_message(
                recipient=recipient,
                message=message,
                subject=subject,
                html=True
            )
                
        except Exception as e:
            self.log_api_error('send_template_email', e)
            return False 