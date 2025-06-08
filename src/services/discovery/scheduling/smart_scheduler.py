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

from services.monitoring import MonitoringService

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
    search_criteria: Dict[str, Any]
    priority: TaskPriority
    scheduled_time: datetime
    max_retries: int = 3
    retry_count: int = 0
    last_attempt: Optional[datetime] = None

class SmartScheduler:
    """Intelligent scheduler for scraping tasks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.tasks: List[ScrapingTask] = []
        self.platform_patterns: Dict[str, Dict[str, Any]] = {}
        self.resource_limits: Dict[str, int] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    async def schedule_task(
        self,
        platform: str,
        search_criteria: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> ScrapingTask:
        """Schedule a new scraping task."""
        try:
            # Calculate optimal execution time
            scheduled_time = await self._calculate_optimal_time(
                platform=platform,
                priority=priority
            )
            
            # Create task
            task = ScrapingTask(
                platform=platform,
                search_criteria=search_criteria,
                priority=priority,
                scheduled_time=scheduled_time
            )
            
            # Add to task queue
            self.tasks.append(task)
            self.tasks.sort(key=lambda x: (x.priority.value, x.scheduled_time))
            
            logger.info(f"Scheduled task for {platform} at {scheduled_time}")
            return task
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error scheduling task: {str(e)}",
                context={"platform": platform}
            )
            raise
            
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
            task = next((t for t in self.tasks if t.platform == task_id), None)
            if task:
                self.tasks.remove(task)
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
                "pending_tasks": len(self.tasks),
                "active_tasks": len(self.active_tasks),
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
                task for task in self.tasks
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
            if len(self.active_tasks) >= self.resource_limits.get('max_concurrent_tasks', 5):
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
                    if task.platform in self.active_tasks:
                        del self.active_tasks[task.platform]
                        
            # Start task
            self.active_tasks[task.platform] = asyncio.create_task(task_wrapper())
            
            # Remove from queue
            self.tasks.remove(task)
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error executing task: {str(e)}",
                context={"platform": task.platform}
            )
            raise 