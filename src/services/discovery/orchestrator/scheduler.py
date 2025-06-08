"""
Smart Scheduler

This module implements intelligent scheduling for scraping tasks across platforms,
considering rate limits, priorities, and resource constraints.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from services.monitoring import MonitoringService
from services.discovery.adapters.rate_limiter import RateLimiter

class SmartScheduler:
    """Manages and schedules scraping tasks across platforms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize smart scheduler."""
        self.config = config or {}
        self.monitoring = MonitoringService()
        
        # Initialize scheduling parameters
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 5)
        self.task_timeout = self.config.get('task_timeout', 300)  # 5 minutes
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 60)  # 1 minute
        
        # Initialize rate limiters
        self.rate_limiters = {
            'linkedin': RateLimiter(self.config.get('linkedin_rate_limits')),
            'twitter': RateLimiter(self.config.get('twitter_rate_limits')),
            'youtube': RateLimiter(self.config.get('youtube_rate_limits')),
            'tiktok': RateLimiter(self.config.get('tiktok_rate_limits')),
            'instagram': RateLimiter(self.config.get('instagram_rate_limits')),
            'reddit': RateLimiter(self.config.get('reddit_rate_limits'))
        }
        
        # Initialize task queue
        self.task_queue = asyncio.Queue()
        self.running_tasks = set()
        
    async def schedule_task(
        self,
        task_type: str,
        platform: str,
        target: str,
        priority: int = 1,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Schedule a new scraping task."""
        try:
            # Generate task ID
            task_id = f"{platform}_{task_type}_{datetime.utcnow().timestamp()}"
            
            # Create task
            task = {
                'id': task_id,
                'type': task_type,
                'platform': platform,
                'target': target,
                'priority': priority,
                'context': context or {},
                'status': 'pending',
                'created_at': datetime.utcnow(),
                'attempts': 0
            }
            
            # Add to queue
            await self.task_queue.put(task)
            
            # Record metric
            self.monitoring.record_metric(
                'scheduled_tasks',
                1,
                {
                    'platform': platform,
                    'task_type': task_type,
                    'priority': str(priority)
                }
            )
            
            return task_id
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error scheduling task: {str(e)}",
                error_type="scheduling_error",
                component="smart_scheduler",
                context={
                    'task_type': task_type,
                    'platform': platform,
                    'target': target
                }
            )
            raise
            
    async def start(self):
        """Start the scheduler."""
        try:
            # Start task processor
            asyncio.create_task(self._process_tasks())
            
            # Start rate limit monitor
            asyncio.create_task(self._monitor_rate_limits())
            
            self.monitoring.log_info(
                "Smart scheduler started",
                component="smart_scheduler"
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error starting scheduler: {str(e)}",
                error_type="scheduler_start_error",
                component="smart_scheduler"
            )
            raise
            
    async def stop(self):
        """Stop the scheduler."""
        try:
            # Cancel all running tasks
            for task in self.running_tasks:
                task.cancel()
                
            # Clear queue
            while not self.task_queue.empty():
                self.task_queue.get_nowait()
                
            self.monitoring.log_info(
                "Smart scheduler stopped",
                component="smart_scheduler"
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error stopping scheduler: {str(e)}",
                error_type="scheduler_stop_error",
                component="smart_scheduler"
            )
            raise
            
    async def _process_tasks(self):
        """Process tasks from the queue."""
        while True:
            try:
                # Get next task
                task = await self.task_queue.get()
                
                # Check if we can run more tasks
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    # Put task back in queue
                    await self.task_queue.put(task)
                    await asyncio.sleep(1)
                    continue
                    
                # Create task coroutine
                task_coro = self._execute_task(task)
                
                # Add to running tasks
                running_task = asyncio.create_task(task_coro)
                self.running_tasks.add(running_task)
                
                # Remove from running tasks when done
                running_task.add_done_callback(self.running_tasks.discard)
                
            except Exception as e:
                self.monitoring.log_error(
                    f"Error processing task: {str(e)}",
                    error_type="task_processing_error",
                    component="smart_scheduler"
                )
                await asyncio.sleep(1)
                
    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a scheduled task."""
        try:
            # Update task status
            task['status'] = 'running'
            task['started_at'] = datetime.utcnow()
            
            # Get rate limiter
            rate_limiter = self.rate_limiters.get(task['platform'])
            if not rate_limiter:
                raise ValueError(f"No rate limiter for platform: {task['platform']}")
                
            # Acquire rate limit permission
            await rate_limiter.acquire()
            
            try:
                # Execute task
                result = await self._run_task(task)
                
                # Update task status
                task['status'] = 'completed'
                task['completed_at'] = datetime.utcnow()
                task['result'] = result
                
            except Exception as e:
                # Handle task failure
                task['status'] = 'failed'
                task['error'] = str(e)
                task['attempts'] += 1
                
                if task['attempts'] < self.retry_attempts:
                    # Reschedule task
                    await asyncio.sleep(self.retry_delay)
                    await self.task_queue.put(task)
                else:
                    # Task failed permanently
                    self.monitoring.log_error(
                        f"Task failed permanently: {str(e)}",
                        error_type="task_failure",
                        component="smart_scheduler",
                        context=task
                    )
                    
            finally:
                # Release rate limit
                rate_limiter.release()
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error executing task: {str(e)}",
                error_type="task_execution_error",
                component="smart_scheduler",
                context=task
            )
            raise
            
    async def _run_task(self, task: Dict[str, Any]) -> Any:
        """Run the actual task."""
        # Implementation depends on task type and platform
        pass
        
    async def _monitor_rate_limits(self):
        """Monitor rate limits for all platforms."""
        while True:
            try:
                for platform, rate_limiter in self.rate_limiters.items():
                    # Get rate limit status
                    status = rate_limiter.get_status()
                    
                    # Record metrics
                    self.monitoring.record_metric(
                        'rate_limit_remaining',
                        status['remaining'],
                        {'platform': platform}
                    )
                    
                    self.monitoring.record_metric(
                        'rate_limit_reset',
                        status['reset_time'].timestamp(),
                        {'platform': platform}
                    )
                    
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.monitoring.log_error(
                    f"Error monitoring rate limits: {str(e)}",
                    error_type="rate_limit_monitoring_error",
                    component="smart_scheduler"
                )
                await asyncio.sleep(60)
                
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'rate_limits': {
                platform: limiter.get_status()
                for platform, limiter in self.rate_limiters.items()
            }
        } 