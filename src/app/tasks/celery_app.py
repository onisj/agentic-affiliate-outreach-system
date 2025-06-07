from celery import Celery
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'affiliate_outreach',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.scoring_tasks',
        'app.tasks.outreach_tasks',
        'app.tasks.analysis_tasks'
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'scoring': {
            'exchange': 'scoring',
            'routing_key': 'scoring',
        },
        'outreach': {
            'exchange': 'outreach',
            'routing_key': 'outreach',
        },
        'analysis': {
            'exchange': 'analysis',
            'routing_key': 'analysis',
        }
    }
)

# Configure logging
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
)

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    logger.info(f'Request: {self.request!r}') 