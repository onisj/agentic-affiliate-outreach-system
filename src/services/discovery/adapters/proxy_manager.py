"""
Proxy Manager

This module implements the ProxyManager class for managing proxy connections in the Agentic Affiliate Outreach System.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
from services.monitoring import MonitoringService

class ProxyManager:
    """Manages proxy connections for scraping tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize proxy manager."""
        self.config = config or {}
        self.monitoring = MonitoringService()
        
        # Initialize proxy configuration
        self.proxy_list = self.config.get('proxy_list', [])
        self.proxy_timeout = self.config.get('proxy_timeout', 30)
        self.proxy_retry_attempts = self.config.get('proxy_retry_attempts', 3)
        self.proxy_retry_delay = self.config.get('proxy_retry_delay', 5)
        
        # Initialize proxy status
        self.proxy_status: Dict[str, Dict[str, Any]] = {}
        
        # Initialize proxy rotation
        self.current_proxy_index = 0
        
    async def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next available proxy."""
        try:
            if not self.proxy_list:
                return None
                
            # Get next proxy
            proxy = self.proxy_list[self.current_proxy_index]
            
            # Update index
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            
            # Check proxy status
            if not await self._check_proxy(proxy):
                # Try next proxy
                return await self.get_proxy()
                
            return proxy
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting proxy: {str(e)}",
                error_type="proxy_retrieval_error",
                component="proxy_manager"
            )
            return None
            
    async def _check_proxy(self, proxy: Dict[str, str]) -> bool:
        """Check if proxy is working."""
        try:
            # Get proxy URL
            proxy_url = self._format_proxy_url(proxy)
            
            # Check proxy status
            status = self.proxy_status.get(proxy_url, {})
            if status.get('status') == 'active':
                return True
                
            # Test proxy
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=proxy_url,
                    timeout=self.proxy_timeout
                ) as response:
                    if response.status == 200:
                        # Update status
                        await self.update_proxy_status(
                            proxy_url,
                            {'status': 'active'}
                        )
                        return True
                        
            # Update status
            await self.update_proxy_status(
                proxy_url,
                {'status': 'inactive'}
            )
            return False
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error checking proxy: {str(e)}",
                error_type="proxy_check_error",
                component="proxy_manager",
                context={'proxy': proxy}
            )
            return False
            
    async def update_proxy_status(self, proxy_url: str, status: Dict[str, Any]):
        """Update status of a specific proxy."""
        try:
            self.proxy_status[proxy_url] = {
                **status,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Record metric
            self.monitoring.record_metric(
                'proxy_status',
                1,
                {
                    'proxy': proxy_url,
                    'status': status.get('status', 'unknown')
                }
            )
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error updating proxy status: {str(e)}",
                error_type="status_update_error",
                component="proxy_manager",
                context={'proxy': proxy_url}
            )
            raise
            
    def _format_proxy_url(self, proxy: Dict[str, str]) -> str:
        """Format proxy URL."""
        return f"{proxy['protocol']}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        
    def get_proxy_status(self, proxy_url: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific proxy."""
        return self.proxy_status.get(proxy_url)
        
    def get_all_proxy_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all proxies."""
        return self.proxy_status
        
    async def cleanup(self):
        """Cleanup resources."""
        try:
            # Update all proxies to inactive
            for proxy_url in self.proxy_status.keys():
                await self.update_proxy_status(
                    proxy_url,
                    {'status': 'inactive'}
                )
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error in cleanup: {str(e)}",
                error_type="cleanup_error",
                component="proxy_manager"
            )
            raise 