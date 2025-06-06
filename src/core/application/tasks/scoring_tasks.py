"""
Celery tasks for prospect scoring and qualification.
Includes functionality for:
- Individual prospect scoring
- Campaign-level prospect scoring
- Model training and evaluation
- Scoring metrics export
"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from celery import Task
from app.tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from database.models import AffiliateProspect, OutreachCampaign
from database.session import get_db
from app.services.scoring_service import LeadScoringService
from app.services.visualization_service import VisualizationService
from utils.base_task import BaseTask

logger = logging.getLogger(__name__)

class ScoringTask(BaseTask):
    """Base class for scoring tasks with common functionality."""
    
    def __init__(self):
        super().__init__()
        self.scoring_service = LeadScoringService()
        self.visualization_service = VisualizationService()

@celery_app.task(bind=True, base=ScoringTask)
def score_prospect(self, prospect_id: str) -> Dict[str, Any]:
    """Calculate and update prospect score."""
    db = next(get_db())
    
    try:
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
        if not prospect:
            return {"success": False, "error": "Prospect not found"}
        
        prospect_data = {
            'email': prospect.email,
            'first_name': prospect.first_name,
            'last_name': prospect.last_name,
            'company': prospect.company,
            'website': prospect.website,
            'social_profiles': prospect.social_profiles or {}
        }
        
        score = self.scoring_service.calculate_score(prospect_data)
        prospect.qualification_score = score
        if score >= 70:
            prospect.status = "qualified"
        
        db.commit()
        return {"success": True, "score": score}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error scoring prospect {prospect_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, base=ScoringTask)
def train_scoring_model(self) -> Dict[str, Any]:
    """Train the prospect scoring model."""
    try:
        logger.info("Training prospect scoring model...")
        success = self.scoring_service.train_model()
        
        if success:
            # Export scoring metrics
            metrics_path = self.scoring_service.export_scoring_metrics()
            if metrics_path:
                logger.info(f"Scoring metrics exported to: {metrics_path}")
            
            return {
                "success": True,
                "message": "Model trained successfully",
                "metrics_path": metrics_path
            }
        else:
            return {
                "success": False,
                "error": "Model training failed"
            }
            
    except Exception as e:
        logger.error(f"Error training scoring model: {e}")
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, base=ScoringTask)
def score_campaign_prospects(self, campaign_id: str) -> Dict[str, Any]:
    """Score all prospects for a specific campaign."""
    db = next(get_db())
    
    try:
        campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
        if not campaign:
            return {"success": False, "error": "Campaign not found"}
        
        logger.info(f"Scoring prospects for campaign: {campaign.name}")
        
        # Get all prospects for the campaign
        prospects = db.query(AffiliateProspect).filter(
            AffiliateProspect.campaign_id == campaign_id
        ).all()
        
        results = []
        for prospect in prospects:
            # Score each prospect
            score_result = score_prospect.delay(str(prospect.id))
            results.append({
                "prospect_id": str(prospect.id),
                "name": f"{prospect.first_name} {prospect.last_name}",
                "score_task_id": score_result.id
            })
        
        # Generate campaign scoring visualization
        viz_path = self.visualization_service.generate_campaign_scoring_viz(
            campaign_id=campaign_id,
            output_path=f"reports/campaign_{campaign_id}_scoring.png"
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "prospects_scored": len(results),
            "scoring_tasks": results,
            "visualization_path": viz_path
        }
        
    except Exception as e:
        logger.error(f"Error scoring campaign prospects: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, base=ScoringTask)
def score_all_campaigns(self) -> Dict[str, Any]:
    """Score prospects for all active campaigns."""
    db = next(get_db())
    
    try:
        campaigns = db.query(OutreachCampaign).filter(
            OutreachCampaign.status == "active"
        ).all()
        
        results = []
        for campaign in campaigns:
            # Score prospects for each campaign
            score_result = score_campaign_prospects.delay(str(campaign.id))
            results.append({
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "scoring_task_id": score_result.id
            })
        
        return {
            "success": True,
            "campaigns_scored": len(results),
            "scoring_tasks": results
        }
        
    except Exception as e:
        logger.error(f"Error scoring all campaigns: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()