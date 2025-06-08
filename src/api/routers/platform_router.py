"""
Platform Router

This module implements the PlatformRouter class for routing tasks to appropriate
platform adapters in the Agentic Affiliate Outreach System.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from services.monitoring import MonitoringService
from services.discovery.adapters.linkedin_scraper import LinkedInScraper
from services.discovery.adapters.twitter_scraper import TwitterScraper
from services.discovery.adapters.youtube_scraper import YouTubeScraper
from services.discovery.adapters.tiktok_scraper import TikTokScraper
from services.discovery.adapters.instagram_scraper import InstagramScraper
from services.discovery.adapters.reddit_scraper import RedditScraper
from services.discovery.adapters.generic_scraper import GenericWebScraper
from services.discovery.models.data_models import DataObject, PlatformType

class PlatformRouter:
    """Routes tasks to appropriate platform adapters."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize platform router."""
        self.config = config or {}
        self.monitoring = MonitoringService()
        
        # Initialize platform adapters
        self.adapters = {
            PlatformType.LINKEDIN: LinkedInScraper(self.config),
            PlatformType.TWITTER: TwitterScraper(self.config),
            PlatformType.YOUTUBE: YouTubeScraper(self.config),
            PlatformType.TIKTOK: TikTokScraper(self.config),
            PlatformType.INSTAGRAM: InstagramScraper(self.config),
            PlatformType.REDDIT: RedditScraper(self.config),
            PlatformType.GENERIC: GenericWebScraper(self.config)
        }
        
        # Initialize task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
    async def route_task(
        self,
        task_type: str,
        platform: str,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DataObject:
        """Route a task to the appropriate platform adapter."""
        try:
            # Get platform type
            platform_type = self._get_platform_type(platform)
            
            # Get adapter
            adapter = self.adapters.get(platform_type)
            if not adapter:
                raise ValueError(f"No adapter found for platform: {platform}")
                
            # Generate task ID
            task_id = f"{platform}_{task_type}_{datetime.utcnow().timestamp()}"
            
            # Create task
            task = {
                'id': task_id,
                'type': task_type,
                'platform': platform,
                'target': target,
                'context': context or {},
                'status': 'routing',
                'created_at': datetime.utcnow()
            }
            
            # Track task
            self.active_tasks[task_id] = task
            
            # Record metric
            self.monitoring.record_metric(
                'routed_tasks',
                1,
                {
                    'platform': platform,
                    'task_type': task_type
                }
            )
            
            # Execute task
            result = await self._execute_task(adapter, task)
            
            # Update task status
            task['status'] = 'completed'
            task['completed_at'] = datetime.utcnow()
            
            return result
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error routing task: {str(e)}",
                error_type="task_routing_error",
                component="platform_router",
                context={
                    'task_type': task_type,
                    'platform': platform,
                    'target': target
                }
            )
            raise
            
    async def _execute_task(
        self,
        adapter: Any,
        task: Dict[str, Any]
    ) -> DataObject:
        """Execute task using the appropriate adapter method."""
        try:
            # Update task status
            task['status'] = 'executing'
            
            # Execute based on task type
            if task['type'] == 'profile_scrape':
                result = await adapter.scrape_profile(task['target'])
            elif task['type'] == 'content_scrape':
                result = await adapter.scrape_content(task['target'])
            elif task['type'] == 'network_scrape':
                result = await adapter.scrape_network(task['target'])
            else:
                raise ValueError(f"Unknown task type: {task['type']}")
                
            return result
            
        except Exception as e:
            # Update task status
            task['status'] = 'failed'
            task['error'] = str(e)
            
            self.monitoring.log_error(
                f"Error executing task: {str(e)}",
                error_type="task_execution_error",
                component="platform_router",
                context=task
            )
            raise
            
    def _get_platform_type(self, platform: str) -> PlatformType:
        """Get platform type from string."""
        try:
            return PlatformType(platform.lower())
        except ValueError:
            return PlatformType.GENERIC
            
    def get_adapter_status(self) -> Dict[str, Any]:
        """Get status of all platform adapters."""
        return {
            platform: {
                'active_tasks': len([
                    task for task in self.active_tasks.values()
                    if task['platform'] == platform
                ]),
                'adapter_type': type(adapter).__name__
            }
            for platform, adapter in self.adapters.items()
        }
        
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        return self.active_tasks.get(task_id)
        
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks."""
        return list(self.active_tasks.values())