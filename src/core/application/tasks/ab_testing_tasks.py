"""
Celery tasks for A/B testing functionality.
Includes tasks for:
- Creating and managing A/B tests
- Collecting and analyzing test results
- Generating test reports and visualizations
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from celery import Task
from app.tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from database.models import OutreachCampaign, MessageTemplate, ABTest, ABTestResult, MessageLog
from database.session import get_db
from app.services.ab_testing import ABTestingService
from utils.base_task import BaseTask
import pandas as pd

logger = logging.getLogger(__name__)

class ABTestingTask(BaseTask):
    """Base class for A/B testing tasks with common functionality."""
    
    def __init__(self):
        super().__init__()
        self.ab_testing_service = ABTestingService()

@celery_app.task(bind=True, base=ABTestingTask)
def create_ab_test(
    self,
    campaign_id: str,
    template_ids: List[str],
    test_duration_days: int = 7,
    sample_size_per_variant: int = 100
) -> Dict[str, Any]:
    """Create and start a new A/B test."""
    try:
        test = self.ab_testing_service.create_test(
            campaign_id=campaign_id,
            template_ids=template_ids,
            test_duration_days=test_duration_days,
            sample_size_per_variant=sample_size_per_variant
        )
        
        # Schedule test completion task
        test_end_time = datetime.now() + timedelta(days=test_duration_days)
        complete_test.apply_async(
            args=[campaign_id],
            eta=test_end_time
        )
        
        return {
            "success": True,
            "test": test,
            "end_time": test_end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, base=ABTestingTask)
def complete_test(self, campaign_id: str) -> Dict[str, Any]:
    """Complete an A/B test and generate final results."""
    try:
        # Get final results
        results = {}
        for metric in self.ab_testing_service.metrics.keys():
            results[metric] = self.ab_testing_service.get_test_results(
                campaign_id,
                metric
            )
        
        # Export results
        output_path = self.ab_testing_service.export_test_results(campaign_id)
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "results": results,
            "report_path": output_path
        }
        
    except Exception as e:
        logger.error(f"Error completing A/B test: {e}")
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, base=ABTestingTask)
def get_test_results(
    self,
    campaign_id: str,
    metric: Optional[str] = None
) -> Dict[str, Any]:
    """Get A/B test results for a specific campaign."""
    try:
        if metric:
            results = self.ab_testing_service.get_test_results(campaign_id, metric)
            return {
                "success": True,
                "campaign_id": campaign_id,
                "metric": metric,
                "results": results
            }
        else:
            # Get results for all metrics
            results = {}
            for metric in self.ab_testing_service.metrics.keys():
                results[metric] = self.ab_testing_service.get_test_results(
                    campaign_id,
                    metric
                )
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "results": results
            }
            
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}")
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, base=ABTestingTask)
def export_test_results(self, campaign_id: str) -> Dict[str, Any]:
    """Export A/B test results to a report."""
    try:
        output_path = self.ab_testing_service.export_test_results(campaign_id)
        
        if output_path:
            return {
                "success": True,
                "campaign_id": campaign_id,
                "report_path": output_path
            }
        else:
            return {
                "success": False,
                "error": "Failed to export results"
            }
            
    except Exception as e:
        logger.error(f"Error exporting A/B test results: {e}")
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, base=ABTestingTask)
def update_test_metrics(self, campaign_id: str) -> Dict[str, Any]:
    """Update metrics for an ongoing A/B test."""
    try:
        results = {}
        for metric in self.ab_testing_service.metrics.keys():
            results[metric] = self.ab_testing_service.update_test_metrics(
                campaign_id,
                metric
            )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "updated_metrics": results
        }
        
    except Exception as e:
        logger.error(f"Error updating A/B test metrics: {e}")
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, base=ABTestingTask)
def schedule_metric_updates(self, campaign_id: str) -> Dict[str, Any]:
    """Schedule periodic metric updates for an A/B test."""
    try:
        # Schedule updates every hour
        update_test_metrics.apply_async(
            args=[campaign_id],
            countdown=3600  # 1 hour
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": "Metric updates scheduled"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling metric updates: {e}")
        return {"success": False, "error": str(e)} 