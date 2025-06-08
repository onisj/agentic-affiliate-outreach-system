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
from abc import ABC, abstractmethod
from dataclasses import dataclass

from services.monitoring import MonitoringService
from services.discovery.adapters.base_scraper import BaseScraper
from .proxy_manager import ProxyManager
from .rate_limiter import RateLimiter

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
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.logger = logging.getLogger(__name__)
        
    async def execute_task(self, task: Any, scraper: Any) -> TaskResult:
        """Execute a scraping task using the appropriate scraper."""
        start_time = datetime.utcnow()
        task_id = task.target_url
        
        try:
            if task.task_type == 'profile':
                data = await scraper.scrape_profile(task.target_url)
            elif task.task_type == 'content':
                data = await scraper.scrape_content(task.target_url)
            elif task.task_type == 'network':
                data = await scraper.scrape_network(task.target_url)
            elif task.task_type == 'engagement':
                data = await scraper.scrape_engagement(task.target_url)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result = TaskResult(
                task_id=task_id,
                status='completed',
                data=data,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            result = TaskResult(
                task_id=task_id,
                status='failed',
                error=str(e),
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
        self.task_results[task_id] = result
        return result
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get the status of a specific task."""
        return self.task_results.get(task_id)
    
    def get_active_tasks(self) -> List[str]:
        """Get list of currently active task IDs."""
        return list(self.active_tasks.keys())
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
            return True
        return False
    
    async def cleanup(self) -> None:
        """Clean up completed tasks and their results."""
        current_time = datetime.utcnow()
        retention_period = self.config.get('result_retention_hours', 24)
        
        tasks_to_remove = [
            task_id for task_id, result in self.task_results.items()
            if (current_time - datetime.fromtimestamp(result.execution_time)).total_seconds() > retention_period * 3600
        ]
        
        for task_id in tasks_to_remove:
            del self.task_results[task_id] 