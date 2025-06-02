from celery import Celery
from config import settings

celery_app = Celery(
    "affiliate_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks.outreach_tasks', 'tasks.scoring_tasks', 'tasks.response_handler', 'tasks.sequence_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.outreach_tasks.send_outreach_message': {'queue': 'outreach_queue'},
        'tasks.scoring_tasks.score_prospect': {'queue': 'scoring_queue'},
        'tasks.response_handler.handle_prospect_response': {'queue': 'response_queue'},
        'tasks.sequence_tasks.process_sequence_step': {'queue': 'sequence_queue'},
    },
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
)