"""
Base Task

This module provides a base class for all Celery tasks with common functionality:
1. Error handling
2. Logging
3. Resource management
4. Task retry logic
"""

import logging
from typing import Any, Dict, Optional
from celery import Task
from celery.exceptions import MaxRetriesExceededError

logger = logging.getLogger(__name__)

class BaseTask(Task):
    """Base class for all tasks with common functionality."""
    
    abstract = True
    
    def __init__(self):
        """Initialize task with default settings."""
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self.retry_backoff = True
        self.retry_backoff_max = 600  # 10 minutes
        self.retry_jitter = True

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task failure."""
        logger.error(
            f"Task {task_id} failed: {str(exc)}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "traceback": einfo.traceback if einfo else None
            }
        )

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task retry."""
        logger.warning(
            f"Task {task_id} retrying: {str(exc)}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "traceback": einfo.traceback if einfo else None
            }
        )

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Handle task success."""
        logger.info(
            f"Task {task_id} completed successfully",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "result": retval
            }
        )

    def after_return(self, *args: Any, **kwargs: Any) -> None:
        """Cleanup after task completion."""
        pass

    def retry(self, exc: Exception, countdown: Optional[int] = None, **kwargs: Any) -> None:
        """Retry task with exponential backoff."""
        try:
            if countdown is None:
                countdown = self.retry_delay
                
            if self.retry_backoff:
                countdown = min(
                    countdown * 2,
                    self.retry_backoff_max
                )
                
            super().retry(
                exc=exc,
                countdown=countdown,
                max_retries=self.max_retries,
                **kwargs
            )
        except MaxRetriesExceededError:
            logger.error(
                f"Task exceeded maximum retries: {str(exc)}",
                extra={
                    "exception": str(exc),
                    "max_retries": self.max_retries
                }
            )
            raise

    def get_task_meta(self) -> Dict[str, Any]:
        """Get task metadata."""
        return {
            "name": self.name,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff": self.retry_backoff,
            "retry_backoff_max": self.retry_backoff_max,
            "retry_jitter": self.retry_jitter
        } 