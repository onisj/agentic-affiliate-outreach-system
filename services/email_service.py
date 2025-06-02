from typing import Dict, Any
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    
    def personalize_message(self, content: str, prospect_data: Dict[str, Any]) -> str:
        """Personalize message content using Jinja2."""
        try:
            template = Template(content)
            context = {
                'first_name': prospect_data.get('first_name', 'there'),
                'last_name': prospect_data.get('last_name', ''),
                'company': prospect_data.get('company', 'your company'),
                'company_mention': f"I noticed you work at {prospect_data.get('company', 'your company')}",
                'email': prospect_data.get('email', '')
            }
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error personalizing message: {str(e)}")
            raise
    
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send email using SendGrid."""
        try:
            message = Mail(
                from_email='no-reply@yourcompany.com',
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            response = self.sg.send(message)
            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False