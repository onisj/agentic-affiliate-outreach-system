from typing import Dict, Any
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email messages."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send_message(
        self,
        to: Dict[str, Any],
        subject: str,
        content: str
    ) -> bool:
        """Send an email message."""
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = to.get("email")
            message["Subject"] = subject
            
            # Add HTML content
            message.attach(MIMEText(content, "html"))
            
            # Send message
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def close(self):
        """Close any open connections."""
        pass  # No persistent connections to close 