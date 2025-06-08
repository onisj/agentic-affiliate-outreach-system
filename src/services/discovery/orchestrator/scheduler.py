"""
Smart Scheduler

This module implements intelligent scheduling of scraping tasks based on
platform-specific patterns, rate limits, and resource availability.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Priority levels for scraping tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ScrapingTask:
    """Represents a scheduled scraping task."""
    platform: str
    target_url: str
    task_type: str  # 'profile', 'content', 'network', 'engagement'
    priority: int
    scheduled_time: datetime
    retry_count: int = 0
    max_retries: int = 3

class SmartScheduler:
    """Manages and schedules scraping tasks across platforms."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.task_queue: List[ScrapingTask] = []
        self.running_tasks: Dict[str, ScrapingTask] = {}
        self.platform_patterns: Dict[str, Dict[str, Any]] = {}
        self.resource_limits: Dict[str, int] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    def schedule_task(self, task: ScrapingTask) -> None:
        """Add a new task to the queue."""
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: (x.priority, x.scheduled_time))
        
    def get_next_task(self) -> Optional[ScrapingTask]:
        """Get the next task to execute."""
        if not self.task_queue:
            return None
            
        current_time = datetime.utcnow()
        for task in self.task_queue:
            if task.scheduled_time <= current_time:
                self.task_queue.remove(task)
                return task
        return None
    
    def reschedule_task(self, task: ScrapingTask) -> None:
        """Reschedule a failed task with exponential backoff."""
        if task.retry_count >= task.max_retries:
            self.logger.error(f"Task {task.target_url} exceeded max retries")
            return
            
        delay = 2 ** task.retry_count  # Exponential backoff
        task.retry_count += 1
        task.scheduled_time = datetime.utcnow() + timedelta(minutes=delay)
        self.schedule_task(task)
    
    def update_task_status(self, task_id: str, status: str) -> None:
        """Update the status of a running task."""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if status == 'completed':
                del self.running_tasks[task_id]
            elif status == 'failed':
                self.reschedule_task(task)
                del self.running_tasks[task_id]
    
    async def run(self) -> None:
        """Main scheduler loop."""
        while True:
            task = self.get_next_task()
            if task:
                self.running_tasks[task.target_url] = task
                # Task execution would be handled by the task manager
                
            await asyncio.sleep(1)  # Prevent CPU spinning
            
    async def start_scheduling(self):
        """Start the scheduling loop."""
        try:
            while True:
                # Process due tasks
                await self._process_due_tasks()
                
                # Update platform patterns
                await self._update_platform_patterns()
                
                # Check resource limits
                await self._check_resource_limits()
                
                # Wait before next iteration
                await asyncio.sleep(self.config.get('scheduler_interval', 60))
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error in scheduling loop: {str(e)}"
            )
            raise
            
    async def cancel_task(self, task_id: str):
        """Cancel a scheduled task."""
        try:
            task = next((t for t in self.task_queue if t.target_url == task_id), None)
            if task:
                self.task_queue.remove(task)
                logger.info(f"Cancelled task for {task_id}")
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error cancelling task: {str(e)}",
                context={"task_id": task_id}
            )
            raise
            
    async def get_schedule_status(self) -> Dict[str, Any]:
        """Get current scheduling status."""
        try:
            return {
                "pending_tasks": len(self.task_queue),
                "active_tasks": len(self.running_tasks),
                "platform_patterns": self.platform_patterns,
                "resource_limits": self.resource_limits
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting schedule status: {str(e)}"
            )
            raise
            
    async def _calculate_optimal_time(
        self,
        platform: str,
        priority: TaskPriority
    ) -> datetime:
        """Calculate optimal execution time for a task."""
        try:
            now = datetime.now()
            
            # Get platform-specific patterns
            patterns = self.platform_patterns.get(platform, {})
            
            # Calculate base delay based on priority
            base_delay = {
                TaskPriority.LOW: 3600,  # 1 hour
                TaskPriority.MEDIUM: 1800,  # 30 minutes
                TaskPriority.HIGH: 300,  # 5 minutes
                TaskPriority.CRITICAL: 60  # 1 minute
            }[priority]
            
            # Adjust for platform patterns
            if patterns:
                # Consider time of day
                hour = now.hour
                if hour in patterns.get('peak_hours', []):
                    base_delay *= 1.5
                elif hour in patterns.get('off_hours', []):
                    base_delay *= 0.5
                    
                # Consider day of week
                weekday = now.weekday()
                if weekday in patterns.get('busy_days', []):
                    base_delay *= 1.2
                    
            return now + timedelta(seconds=base_delay)
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error calculating optimal time: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def _process_due_tasks(self):
        """Process tasks that are due for execution."""
        try:
            now = datetime.now()
            due_tasks = [
                task for task in self.task_queue
                if task.scheduled_time <= now
            ]
            
            for task in due_tasks:
                if await self._can_execute_task(task):
                    await self._execute_task(task)
                else:
                    # Reschedule with backoff
                    task.scheduled_time = now + timedelta(
                        minutes=2 ** task.retry_count
                    )
                    task.retry_count += 1
                    
        except Exception as e:
            self.monitoring.log_error(
                f"Error processing due tasks: {str(e)}"
            )
            raise
            
    async def _update_platform_patterns(self):
        """Update platform-specific patterns based on historical data."""
        try:
            # This would typically involve analyzing historical scraping data
            # to identify optimal times and patterns
            pass
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating platform patterns: {str(e)}"
            )
            raise
            
    async def _check_resource_limits(self):
        """Check and update resource usage limits."""
        try:
            # This would typically involve checking system resources
            # and adjusting limits accordingly
            pass
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error checking resource limits: {str(e)}"
            )
            raise
            
    async def _can_execute_task(self, task: ScrapingTask) -> bool:
        """Check if a task can be executed."""
        try:
            # Check retry limit
            if task.retry_count >= task.max_retries:
                return False
                
            # Check resource limits
            if len(self.running_tasks) >= self.resource_limits.get('max_concurrent_tasks', 5):
                return False
                
            return True
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error checking task execution: {str(e)}",
                context={"platform": task.platform}
            )
            raise
            
    async def _execute_task(self, task: ScrapingTask):
        """Execute a scraping task."""
        try:
            # Create and start task
            async def task_wrapper():
                try:
                    # Execute scraping
                    # This would typically call the appropriate scraper
                    pass
                finally:
                    # Clean up
                    if task.target_url in self.running_tasks:
                        del self.running_tasks[task.target_url]
                        
            # Start task
            self.active_tasks[task.target_url] = asyncio.create_task(task_wrapper())
            
            # Remove from queue
            self.task_queue.remove(task)
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error executing task: {str(e)}",
                context={"platform": task.platform}
            )
            raise 