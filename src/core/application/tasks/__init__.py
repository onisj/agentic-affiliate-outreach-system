# __init__.py

"""
Core Tasks Package

This package contains all Celery tasks for background processing.
Tasks are organized by domain and functionality.
"""

from app.tasks.scoring_tasks import (
    score_prospect,
    train_scoring_model,
    score_campaign_prospects,
    score_all_campaigns
)

from app.tasks.ab_testing_tasks import (
    create_ab_test,
    complete_test,
    get_test_results,
    export_test_results,
    update_test_metrics,
    schedule_metric_updates
)

from app.tasks.outreach_tasks import send_outreach_message
from app.tasks.response_handler import handle_prospect_response

from app.tasks.sequence_tasks import (
    process_sequence_step
)

__all__ = [
    # Scoring tasks
    "score_prospect",
    "train_scoring_model",
    "score_campaign_prospects",
    "score_all_campaigns",
    
    # A/B testing tasks
    "create_ab_test",
    "complete_test",
    "get_test_results",
    "export_test_results",
    "update_test_metrics",
    "schedule_metric_updates",
    
    # Outreach tasks
    "send_outreach_message",
    
    # Sequence tasks
    "process_sequence_step"
]