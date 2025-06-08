"""
Proxy Manager

This module manages proxy rotation and validation for web scraping operations.
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
import random
import aiohttp
from datetime import datetime, timedelta

from services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages proxy rotation and validation for web scraping."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.proxies: Dict[str, List[Dict[str, Any]]] = {}
        self.current_proxies: Dict[str, Dict[str, Any]] = {}
        self.proxy_stats: Dict[str, Dict[str, Any]] = {}
        self.last_rotation: Dict[str, datetime] = {}
        
    async def initialize_proxies(self, platform: str):
        """Initialize proxy list for a platform."""
        try:
            # Load proxies from configuration
            proxy_list = self.config.get('proxy_list', [])
            
            # Validate each proxy
            valid_proxies = []
            for proxy in proxy_list:
                if await self._validate_proxy(proxy):
                    valid_proxies.append({
                        'proxy': proxy,
                        'last_used': None,
                        'success_count': 0,
                        'failure_count': 0
                    })
                    
            self.proxies[platform] = valid_proxies
            logger.info(f"Initialized {len(valid_proxies)} proxies for {platform}")
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error initializing proxies: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def get_proxy(self, platform: str) -> Dict[str, str]:
        """Get a proxy for the specified platform."""
        try:
            if platform not in self.proxies:
                await self.initialize_proxies(platform)
                
            if not self.proxies[platform]:
                raise ValueError(f"No valid proxies available for {platform}")
                
            # Select proxy based on success rate and last used time
            proxy = await self._select_best_proxy(platform)
            
            # Update proxy stats
            self.current_proxies[platform] = proxy
            self.last_rotation[platform] = datetime.now()
            
            return proxy['proxy']
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting proxy: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def rotate_proxy(self, platform: str):
        """Rotate to a new proxy for the platform."""
        try:
            if platform in self.current_proxies:
                current_proxy = self.current_proxies[platform]
                current_proxy['last_used'] = datetime.now()
                
            await self.get_proxy(platform)
            logger.info(f"Rotated proxy for {platform}")
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error rotating proxy: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def report_proxy_success(self, platform: str):
        """Report successful proxy usage."""
        try:
            if platform in self.current_proxies:
                proxy = self.current_proxies[platform]
                proxy['success_count'] += 1
                self.monitoring.record_metric(
                    f"proxy_{platform}_success",
                    1
                )
        except Exception as e:
            self.monitoring.log_error(
                f"Error reporting proxy success: {str(e)}",
                context={"platform": platform}
            )
            
    async def report_proxy_failure(self, platform: str):
        """Report failed proxy usage."""
        try:
            if platform in self.current_proxies:
                proxy = self.current_proxies[platform]
                proxy['failure_count'] += 1
                self.monitoring.record_metric(
                    f"proxy_{platform}_failure",
                    1
                )
                
                # Rotate proxy if failure count exceeds threshold
                if proxy['failure_count'] >= self.config.get('max_failures', 3):
                    await self.rotate_proxy(platform)
                    
        except Exception as e:
            self.monitoring.log_error(
                f"Error reporting proxy failure: {str(e)}",
                context={"platform": platform}
            )
            
    def get_current_proxy(self, platform: str) -> Optional[Dict[str, str]]:
        """Get current proxy for the platform."""
        return self.current_proxies.get(platform, {}).get('proxy')
        
    async def _validate_proxy(self, proxy: Dict[str, str]) -> bool:
        """Validate if a proxy is working."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=f"http://{proxy['host']}:{proxy['port']}",
                    timeout=10
                ) as response:
                    return response.status == 200
        except:
            return False
            
    async def _select_best_proxy(self, platform: str) -> Dict[str, Any]:
        """Select the best proxy based on success rate and last used time."""
        try:
            proxies = self.proxies[platform]
            
            # Filter out recently used proxies
            now = datetime.now()
            available_proxies = [
                p for p in proxies
                if not p['last_used'] or
                (now - p['last_used']) > timedelta(minutes=5)
            ]
            
            if not available_proxies:
                available_proxies = proxies
                
            # Sort by success rate
            available_proxies.sort(
                key=lambda x: x['success_count'] / (x['success_count'] + x['failure_count'] + 1),
                reverse=True
            )
            
            return random.choice(available_proxies[:3])
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error selecting best proxy: {str(e)}",
                context={"platform": platform}
            )
            raise 