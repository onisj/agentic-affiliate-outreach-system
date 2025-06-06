"""
Email Service

This module provides functionality for:
1. Sending emails using SMTP or SendGrid
2. Email template rendering
3. Email tracking and analytics
4. Bulk email operations
5. Rate limiting and retry mechanisms
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import jinja2
from pathlib import Path
import time
import redis
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Environment, FileSystemLoader, Template

from config.settings import settings
from database.session import get_db
from database.models import MessageLog, MessageStatus, MessageType
from app.services.validator import DataValidator

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.template_dir = Path("templates")
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir)
        )
        self.validator = DataValidator()
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.use_sendgrid = bool(settings.SENDGRID_API_KEY)
        if self.use_sendgrid:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def _get_smtp_connection(self) -> smtplib.SMTP:
        """Create and return an SMTP connection."""
        smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
        smtp.starttls()
        smtp.login(self.smtp_username, self.smtp_password)
        return smtp

    def validate_email(self, email: str) -> bool:
        """Validate an email address."""
        result = self.validator.validate_email(email)
        return result["is_valid"]

    def _check_rate_limit(self, email: str) -> bool:
        """Check if an email is rate limited."""
        key = f"email_rate:{email}"
        current = self.redis_client.get(key)
        if current and int(current) >= settings.RATE_LIMIT_PER_MINUTE:
            return False
        return True

    def _increment_rate_limit(self, email: str) -> None:
        """Increment the rate limit counter for an email."""
        key = f"email_rate:{email}"
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)  # 1 minute expiry
        pipe.execute()

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render an email template with the given context."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise

    def _send_via_smtp(self, msg: MIMEMultipart) -> None:
        """Send an email via SMTP."""
        with self._get_smtp_connection() as smtp:
            smtp.send_message(msg)

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> None:
        """Send an email via SendGrid."""
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        self.sendgrid_client.send(message)

    def render_string_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with the provided context."""
        try:
            # Create a template with default values for missing variables
            template = Template(template_string, undefined=jinja2.Undefined)
            # Add default values for missing variables
            context = {**context, "first_name": context.get("first_name", "there")}
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template string: {str(e)}")
            raise

    def personalize_message(self, template: str, context: Dict[str, Any]) -> str:
        """Render a template with the provided context.
        
        Args:
            template: Either a template string or a template name
            context: Dictionary of variables to render in the template
            
        Returns:
            Rendered template string
        """
        try:
            # If template contains template variables, treat it as a string template
            if "{{" in template and "}}" in template:
                return self.render_string_template(template, context)
            # Otherwise, treat it as a template name
            return self.render_template(template, context)
        except Exception as e:
            logger.error(f"Error personalizing message: {str(e)}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        prospect_id: Optional[str] = None,
        db: Optional[Any] = None,
        track: bool = False,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Send an email using either SMTP or SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template to use (or template string)
            context: Dictionary of variables to render in the template
            **kwargs: Additional arguments including:
                - prospect_id: ID of the prospect
                - db: Database session
                - track: Whether to track the email
                - max_retries: Maximum number of retry attempts
                
        Returns:
            Dictionary containing success status and additional information
        """
        try:
            # Validate email
            if not self.validate_email(to_email):
                return {"success": False, "error": "Invalid email address"}

            # Check rate limit
            if not self._check_rate_limit(to_email):
                return {"success": False, "error": "Rate limit exceeded"}

            # Render template
            try:
                # If template_name contains template variables, treat it as a string template
                if "{{" in template_name and "}}" in template_name:
                    content = self.render_string_template(template_name, context)
                else:
                    content = self.render_template(template_name, context)
            except Exception as e:
                logger.error(f"Error rendering template: {str(e)}")
                return {"success": False, "error": str(e)}

            # Send email
            message_id = None
            tracking_id = None
            
            # Try SendGrid first
            if self.use_sendgrid:
                try:
                    message_id = self._send_via_sendgrid(to_email, subject, content)
                except Exception as e:
                    logger.error(f"SendGrid error: {str(e)}")
                    if not self.smtp_server:  # Only fail if SMTP is not configured
                        return {"success": False, "error": str(e)}
            
            # Fall back to SMTP if SendGrid fails or is not configured
            if not message_id and self.smtp_server:
                try:
                    msg = MIMEMultipart()
                    msg["From"] = self.from_email
                    msg["To"] = to_email
                    msg["Subject"] = subject
                    msg.attach(MIMEText(content, "html"))
                    message_id = self._send_via_smtp(msg)
                except Exception as e:
                    logger.error(f"SMTP error: {str(e)}")
                    return {"success": False, "error": str(e)}
            
            if not message_id:
                return {"success": False, "error": "Failed to send email via any configured method"}

            # Track email if requested
            if track:
                tracking_id = self._track_email(message_id, to_email, subject, prospect_id)

            # Log the activity
            if not db:
                db = next(get_db())
            
            message_log = MessageLog(
                prospect_id=prospect_id,
                message_type=MessageType.EMAIL,
                subject=subject,
                content=content,
                sent_at=datetime.now(),
                status=MessageStatus.SENT
            )
            db.add(message_log)
            db.commit()
            
            # Set up tracking if requested
            if track:
                self.redis_client.hmset(
                    f"email_tracking:{message_id}",
                    {
                        "status": "delivered",
                        "opens": "0",
                        "clicks": "0",
                        "sent_at": datetime.now().isoformat()
                    }
                )
                self.redis_client.expire(f"email_tracking:{message_id}", 30 * 24 * 60 * 60)  # 30 days
            
            return {
                "success": True,
                "message_id": message_id,
                "tracking_id": tracking_id
            }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if db:
                db.rollback()
            return {"success": False, "error": str(e)}

    def send_bulk_emails(
        self,
        emails: List[Dict[str, Any]],
        template_name: str,
        subject: str,
        track: bool = False
    ) -> Dict[str, Any]:
        """Send bulk emails using a template."""
        results = {
            "total": len(emails),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        db = next(get_db())
        
        for email_data in emails:
            try:
                result = self.send_email(
                    to_email=email_data["to_email"],
                    subject=subject,
                    template_name=template_name,
                    context=email_data["context"],
                    prospect_id=email_data.get("prospect_id"),
                    db=db,
                    track=track
                )
                
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "email": email_data["to_email"],
                        "error": result["error"]
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "email": email_data["to_email"],
                    "error": str(e)
                })
        
        return results

    def get_email_status(self, message_id: str) -> Dict[str, Any]:
        """Get the status of a sent email."""
        try:
            db = next(get_db())
            message_log = db.query(MessageLog).filter(
                MessageLog.id == message_id,
                MessageLog.message_type == MessageType.EMAIL
            ).first()
            
            if not message_log:
                return {
                    "success": False,
                    "error": "Email not found"
                }
            
            # Get tracking data if available
            tracking_data = self.redis_client.hgetall(f"email_tracking:{message_id}")
            
            return {
                "success": True,
                "status": message_log.status,
                "sent_at": message_log.sent_at.isoformat(),
                "subject": message_log.subject,
                "tracking": {
                        "opens": int(tracking_data.get(b"opens", b"0")),
                        "clicks": int(tracking_data.get(b"clicks", b"0")),
                        "status": tracking_data.get(b"status", b"unknown").decode()
                    } if tracking_data else None
            }
            
        except Exception as e:
            logger.error(f"Error getting email status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def track_email_open(self, tracking_id: str) -> None:
        """Track when an email is opened."""
        try:
            key = f"email_tracking:{tracking_id}"
            pipe = self.redis_client.pipeline()
            pipe.hincrby(key, "opens", 1)
            pipe.hset(key, "last_open", datetime.now().isoformat())
            pipe.execute()
        except Exception as e:
            logger.error(f"Error tracking email open: {str(e)}")

    def track_email_click(self, tracking_id: str, url: str) -> None:
        """Track when an email link is clicked."""
        try:
            key = f"email_tracking:{tracking_id}"
            pipe = self.redis_client.pipeline()
            pipe.hincrby(key, "clicks", 1)
            pipe.hset(key, "last_click", datetime.now().isoformat())
            pipe.hset(key, "last_click_url", url)
            pipe.execute()
        except Exception as e:
            logger.error(f"Error tracking email click: {str(e)}")

    async def close(self):
        """Cleanup resources."""
        if hasattr(self, 'redis_client'):
            self.redis_client.close()