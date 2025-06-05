from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import MessageTemplate, MessageType, ABTest, ABTestResult
from jinja2 import Template, Environment, select_autoescape
import random
import uuid

logger = logging.getLogger(__name__)

class MessagingService:
    """Service for handling message templates and personalization."""
    
    def __init__(self, db: Session):
        self.db = db
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    async def create_template(
        self,
        name: str,
        content: str,
        message_type: MessageType,
        subject: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new message template."""
        try:
            # Validate template syntax
            self.env.from_string(content)
            
            template = MessageTemplate(
                id=str(uuid.uuid4()),
                name=name,
                content=content,
                message_type=message_type,
                subject=subject,
                variables=variables or []
            )
            
            self.db.add(template)
            self.db.commit()
            
            return {
                "id": template.id,
                "name": template.name,
                "message_type": template.message_type,
                "created_at": template.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            self.db.rollback()
            raise
    
    async def create_ab_test(
        self,
        campaign_id: str,
        name: str,
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create an A/B test for message variants."""
        try:
            ab_test = ABTest(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                name=name,
                variants=variants
            )
            
            self.db.add(ab_test)
            self.db.commit()
            
            return {
                "id": ab_test.id,
                "name": ab_test.name,
                "variants": ab_test.variants
            }
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            self.db.rollback()
            raise
    
    async def get_personalized_message(
        self,
        template_id: str,
        data: Dict[str, Any],
        ab_test_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a personalized message from a template."""
        try:
            template = self.db.query(MessageTemplate).filter(
                MessageTemplate.id == template_id
            ).first()
            
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Select variant if A/B testing
            variant = None
            if ab_test_id:
                variant = await self._select_ab_test_variant(ab_test_id)
                if variant:
                    content = variant.get("content", template.content)
                    subject = variant.get("subject", template.subject)
                else:
                    content = template.content
                    subject = template.subject
            else:
                content = template.content
                subject = template.subject
            
            # Render template with data
            jinja_template = self.env.from_string(content)
            personalized_content = jinja_template.render(**data)
            
            if subject:
                subject_template = self.env.from_string(subject)
                personalized_subject = subject_template.render(**data)
            else:
                personalized_subject = None
            
            return {
                "content": personalized_content,
                "subject": personalized_subject,
                "variant_id": variant.get("id") if variant else None
            }
            
        except Exception as e:
            logger.error(f"Error personalizing message: {e}")
            raise
    
    async def _select_ab_test_variant(self, ab_test_id: str) -> Optional[Dict[str, Any]]:
        """Select a variant for A/B testing."""
        try:
            ab_test = self.db.query(ABTest).filter(
                ABTest.id == ab_test_id
            ).first()
            
            if not ab_test:
                return None
            
            # Get current results
            results = self.db.query(ABTestResult).filter(
                ABTestResult.ab_test_id == ab_test_id
            ).all()
            
            # If no results yet, random selection
            if not results:
                return random.choice(ab_test.variants)
            
            # Calculate success rates
            variant_stats = {}
            for result in results:
                variant_id = result.variant_id
                if variant_id not in variant_stats:
                    variant_stats[variant_id] = {
                        "sent": 0,
                        "success": 0
                    }
                variant_stats[variant_id]["sent"] += result.sent_count
                variant_stats[variant_id]["success"] += (
                    result.open_rate + result.click_rate + result.reply_rate
                ) / 3
            
            # Select variant with highest success rate
            best_variant = max(
                variant_stats.items(),
                key=lambda x: x[1]["success"] / x[1]["sent"] if x[1]["sent"] > 0 else 0
            )[0]
            
            return next(
                (v for v in ab_test.variants if v["id"] == best_variant),
                random.choice(ab_test.variants)
            )
            
        except Exception as e:
            logger.error(f"Error selecting A/B test variant: {e}")
            return None
    
    async def update_ab_test_results(
        self,
        ab_test_id: str,
        variant_id: str,
        sent_count: int,
        open_rate: float,
        click_rate: float,
        reply_rate: float
    ) -> bool:
        """Update A/B test results."""
        try:
            result = ABTestResult(
                ab_test_id=ab_test_id,
                variant_id=variant_id,
                sent_count=sent_count,
                open_rate=open_rate,
                click_rate=click_rate,
                reply_rate=reply_rate
            )
            
            self.db.add(result)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating A/B test results: {e}")
            self.db.rollback()
            return False 