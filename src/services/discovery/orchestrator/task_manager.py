"""
Scraper Manager

This module implements the intelligent web scraping orchestration system that
manages multiple platform-specific scrapers with rate limiting, proxy rotation,
and intelligent retry mechanisms.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass

from src.services.monitoring.monitoring import MonitoringService
from services.discovery.adapters.base_scraper import BaseScraper
from .proxy_manager import ProxyManager
from adapters.rate_limiter import RateLimiter
from services.discovery.models.data_models import DataObject

logger = logging.getLogger(__name__)

@dataclass
class TaskResult:
    task_id: str
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class ScraperManager:
    """Manages and orchestrates multiple platform-specific scrapers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.proxy_manager = ProxyManager(config.get('proxy_config', {}))
        self.rate_limiter = RateLimiter(config.get('rate_limit_config', {}))
        self.scrapers: Dict[str, BaseScraper] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        
    async def register_scraper(self, platform: str, scraper: BaseScraper):
        """Register a platform-specific scraper."""
        try:
            self.scrapers[platform] = scraper
            logger.info(f"Registered scraper for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error registering scraper: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def start_scraping(
        self,
        platform: str,
        search_criteria: Dict[str, Any],
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Start scraping process for a specific platform."""
        try:
            if platform not in self.scrapers:
                raise ValueError(f"No scraper registered for platform: {platform}")
                
            # Get proxy for this scraping session
            proxy = await self.proxy_manager.get_proxy(platform)
            
            # Check rate limits
            await self.rate_limiter.wait_if_needed(platform)
            
            # Start scraping task
            scraper = self.scrapers[platform]
            scraper.set_proxy(proxy)
            
            results = await scraper.scrape(search_criteria)
            
            # Update metrics
            self.monitoring.record_metric(
                f"scraping_{platform}_results",
                len(results)
            )
            
            return results[:max_results]
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error during scraping: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def stop_scraping(self, platform: str):
        """Stop scraping process for a specific platform."""
        try:
            if platform in self.active_tasks:
                self.active_tasks[platform].cancel()
                del self.active_tasks[platform]
                logger.info(f"Stopped scraping for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error stopping scraping: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def get_scraping_status(self, platform: str) -> Dict[str, Any]:
        """Get current status of scraping process."""
        try:
            if platform not in self.scrapers:
                return {"status": "not_registered"}
                
            scraper = self.scrapers[platform]
            return {
                "status": "active" if platform in self.active_tasks else "idle",
                "metrics": scraper.get_metrics(),
                "rate_limit": self.rate_limiter.get_status(platform),
                "proxy": self.proxy_manager.get_current_proxy(platform)
            }
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting scraping status: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def rotate_proxies(self, platform: str):
        """Rotate proxies for a specific platform."""
        try:
            await self.proxy_manager.rotate_proxy(platform)
            logger.info(f"Rotated proxy for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error rotating proxy: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def update_rate_limits(
        self,
        platform: str,
        new_limits: Dict[str, Any]
    ):
        """Update rate limits for a specific platform."""
        try:
            await self.rate_limiter.update_limits(platform, new_limits)
            logger.info(f"Updated rate limits for platform: {platform}")
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating rate limits: {str(e)}",
                context={"platform": platform}
            )
            raise

class TaskManager:
    """Coordinates task execution and monitors progress."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize task manager."""
        self.config = config or {}
        self.monitoring = MonitoringService()
        
        # Initialize task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        self.failed_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Initialize result storage
        self.task_results: Dict[str, DataObject] = {}
        
        # Initialize task dependencies
        self.task_dependencies: Dict[str, Set[str]] = {}
        
        # Initialize task timeouts
        self.task_timeouts: Dict[str, asyncio.Task] = {}
        
    async def create_task(
        self,
        task_type: str,
        platform: str,
        target: str,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new task."""
        try:
            # Generate task ID
            task_id = f"{platform}_{task_type}_{datetime.utcnow().timestamp()}"
            
            # Create task
            task = {
                'id': task_id,
                'type': task_type,
                'platform': platform,
                'target': target,
                'dependencies': set(dependencies or []),
                'timeout': timeout or self.config.get('default_timeout', 300),
                'context': context or {},
                'status': 'created',
                'created_at': datetime.utcnow(),
                'progress': 0.0
            }
            
            # Store task
            self.active_tasks[task_id] = task
            
            # Set up dependencies
            self.task_dependencies[task_id] = set(dependencies or [])
            
            # Set up timeout
            if task['timeout']:
                self.task_timeouts[task_id] = asyncio.create_task(
                    self._handle_task_timeout(task_id)
                )
                
            # Record metric
            self.monitoring.record_metric(
                'created_tasks',
                1,
                {
                    'platform': platform,
                    'task_type': task_type
                }
            )
            
            return task_id
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error creating task: {str(e)}",
                error_type="task_creation_error",
                component="task_manager",
                context={
                    'task_type': task_type,
                    'platform': platform,
                    'target': target
                }
            )
            raise
            
    async def start_task(self, task_id: str):
        """Start a task."""
        try:
            # Get task
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
                
            # Check dependencies
            if not await self._check_dependencies(task_id):
                return
                
            # Update task status
            task['status'] = 'running'
            task['started_at'] = datetime.utcnow()
            
            # Record metric
            self.monitoring.record_metric(
                'started_tasks',
                1,
                {
                    'platform': task['platform'],
                    'task_type': task['type']
                }
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error starting task: {str(e)}",
                error_type="task_start_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            raise
            
    async def complete_task(self, task_id: str, result: DataObject):
        """Complete a task with results."""
        try:
            # Get task
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
                
            # Update task status
            task['status'] = 'completed'
            task['completed_at'] = datetime.utcnow()
            task['progress'] = 1.0
            
            # Store result
            self.task_results[task_id] = result
            
            # Move to completed tasks
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            # Cancel timeout
            if task_id in self.task_timeouts:
                self.task_timeouts[task_id].cancel()
                del self.task_timeouts[task_id]
                
            # Record metric
            self.monitoring.record_metric(
                'completed_tasks',
                1,
                {
                    'platform': task['platform'],
                    'task_type': task['type']
                }
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error completing task: {str(e)}",
                error_type="task_completion_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            raise
            
    async def fail_task(self, task_id: str, error: str):
        """Mark a task as failed."""
        try:
            # Get task
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
                
            # Update task status
            task['status'] = 'failed'
            task['failed_at'] = datetime.utcnow()
            task['error'] = error
            
            # Move to failed tasks
            self.failed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            # Cancel timeout
            if task_id in self.task_timeouts:
                self.task_timeouts[task_id].cancel()
                del self.task_timeouts[task_id]
                
            # Record metric
            self.monitoring.record_metric(
                'failed_tasks',
                1,
                {
                    'platform': task['platform'],
                    'task_type': task['type']
                }
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error failing task: {str(e)}",
                error_type="task_failure_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            raise
            
    async def update_task_progress(self, task_id: str, progress: float):
        """Update task progress."""
        try:
            # Get task
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
                
            # Update progress
            task['progress'] = min(max(progress, 0.0), 1.0)
            
            # Record metric
            self.monitoring.record_metric(
                'task_progress',
                task['progress'],
                {
                    'platform': task['platform'],
                    'task_type': task['type']
                }
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating task progress: {str(e)}",
                error_type="progress_update_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            raise
            
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status."""
        try:
            # Check active tasks
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]
                
            # Check completed tasks
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
                
            # Check failed tasks
            if task_id in self.failed_tasks:
                return self.failed_tasks[task_id]
                
            raise ValueError(f"Task not found: {task_id}")
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting task status: {str(e)}",
                error_type="status_check_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            raise
            
    async def get_task_result(self, task_id: str) -> Optional[DataObject]:
        """Get task result."""
        try:
            return self.task_results.get(task_id)
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting task result: {str(e)}",
                error_type="result_retrieval_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            raise
            
    async def _check_dependencies(self, task_id: str) -> bool:
        """Check if task dependencies are satisfied."""
        try:
            # Get dependencies
            dependencies = self.task_dependencies.get(task_id, set())
            
            # Check each dependency
            for dep_id in dependencies:
                # Get dependency status
                dep_status = await self.get_task_status(dep_id)
                
                # Check if dependency is completed
                if dep_status['status'] != 'completed':
                    return False
                    
            return True
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error checking dependencies: {str(e)}",
                error_type="dependency_check_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            return False
            
    async def _handle_task_timeout(self, task_id: str):
        """Handle task timeout."""
        try:
            # Get task
            task = self.active_tasks.get(task_id)
            if not task:
                return
                
            # Wait for timeout
            await asyncio.sleep(task['timeout'])
            
            # Check if task is still active
            if task_id in self.active_tasks:
                # Fail task
                await self.fail_task(
                    task_id,
                    f"Task timed out after {task['timeout']} seconds"
                )
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error handling task timeout: {str(e)}",
                error_type="timeout_handling_error",
                component="task_manager",
                context={'task_id': task_id}
            )
            
    def get_task_summary(self) -> Dict[str, Any]:
        """Get summary of all tasks."""
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'total_tasks': len(self.active_tasks) + len(self.completed_tasks) + len(self.failed_tasks)
        } 