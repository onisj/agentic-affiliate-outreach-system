"""
Monitoring Service

This module provides centralized monitoring, logging, and metrics tracking
for the Agentic Affiliate Outreach System, with integration for Prometheus and Grafana.
"""

from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime, timedelta
import traceback
from collections import defaultdict
import asyncio
import aiohttp
import prometheus_client as prom
from prometheus_client import Counter, Gauge, Histogram, Summary
import requests
from requests.auth import HTTPBasicAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MonitoringService:
    """Centralized monitoring service for the system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize monitoring service."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize Prometheus metrics
        self._init_metrics()
        
        # Initialize error tracking
        self.error_counts = defaultdict(int)
        self.error_history = []
        
        # Initialize performance tracking
        self.performance_metrics = defaultdict(list)
        
        # Initialize rate limit tracking
        self.rate_limit_metrics = defaultdict(dict)
        
        # Initialize Grafana client
        self._init_grafana()
        
    def _init_grafana(self):
        """Initialize Grafana client."""
        self.grafana_url = self.config.get('grafana_url')
        self.grafana_api_key = self.config.get('grafana_api_key')
        self.grafana_username = self.config.get('grafana_username')
        self.grafana_password = self.config.get('grafana_password')
        
        if self.grafana_url:
            self.grafana_headers = {
                'Authorization': f'Bearer {self.grafana_api_key}',
                'Content-Type': 'application/json'
            } if self.grafana_api_key else None
            
            self.grafana_auth = HTTPBasicAuth(
                self.grafana_username,
                self.grafana_password
            ) if self.grafana_username and self.grafana_password else None
            
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Error metrics
        self.error_counter = Counter(
            'system_errors_total',
            'Total number of system errors',
            ['error_type', 'component']
        )
        
        # Performance metrics
        self.request_duration = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'method']
        )
        
        self.processing_time = Histogram(
            'processing_time_seconds',
            'Processing time in seconds',
            ['operation', 'component']
        )
        
        # Rate limit metrics
        self.rate_limit_counter = Counter(
            'rate_limit_hits_total',
            'Total number of rate limit hits',
            ['platform', 'limit_type']
        )
        
        # Resource usage metrics
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['component']
        )
        
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            ['component']
        )
        
        # Business metrics
        self.prospect_score = Gauge(
            'prospect_score',
            'Prospect scoring metrics',
            ['platform', 'score_type']
        )
        
        self.engagement_metrics = Counter(
            'engagement_total',
            'Engagement metrics',
            ['platform', 'metric_type']
        )
        
    async def create_grafana_dashboard(self, dashboard_data: Dict[str, Any]) -> Optional[str]:
        """Create a new Grafana dashboard."""
        try:
            if not self.grafana_url:
                self.logger.warning("Grafana URL not configured")
                return None
                
            url = f"{self.grafana_url}/api/dashboards/db"
            
            payload = {
                "dashboard": dashboard_data,
                "overwrite": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=self.grafana_headers,
                    auth=self.grafana_auth
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('uid')
                    else:
                        self.logger.error(
                            f"Failed to create Grafana dashboard: {await response.text()}"
                        )
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error creating Grafana dashboard: {str(e)}")
            return None
            
    async def update_grafana_dashboard(self, dashboard_uid: str, dashboard_data: Dict[str, Any]) -> bool:
        """Update an existing Grafana dashboard."""
        try:
            if not self.grafana_url:
                self.logger.warning("Grafana URL not configured")
                return False
                
            url = f"{self.grafana_url}/api/dashboards/db"
            
            payload = {
                "dashboard": {
                    **dashboard_data,
                    "uid": dashboard_uid
                },
                "overwrite": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=self.grafana_headers,
                    auth=self.grafana_auth
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Error updating Grafana dashboard: {str(e)}")
            return False
            
    async def get_grafana_dashboard(self, dashboard_uid: str) -> Optional[Dict[str, Any]]:
        """Get a Grafana dashboard by UID."""
        try:
            if not self.grafana_url:
                self.logger.warning("Grafana URL not configured")
                return None
                
            url = f"{self.grafana_url}/api/dashboards/uid/{dashboard_uid}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.grafana_headers,
                    auth=self.grafana_auth
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(
                            f"Failed to get Grafana dashboard: {await response.text()}"
                        )
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error getting Grafana dashboard: {str(e)}")
            return None
            
    async def create_grafana_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """Create a new Grafana alert rule."""
        try:
            if not self.grafana_url:
                self.logger.warning("Grafana URL not configured")
                return None
                
            url = f"{self.grafana_url}/api/v1/provisioning/alert-rules"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=alert_data,
                    headers=self.grafana_headers,
                    auth=self.grafana_auth
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('uid')
                    else:
                        self.logger.error(
                            f"Failed to create Grafana alert: {await response.text()}"
                        )
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error creating Grafana alert: {str(e)}")
            return None
            
    async def get_grafana_alerts(self) -> List[Dict[str, Any]]:
        """Get all Grafana alert rules."""
        try:
            if not self.grafana_url:
                self.logger.warning("Grafana URL not configured")
                return []
                
            url = f"{self.grafana_url}/api/v1/provisioning/alert-rules"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.grafana_headers,
                    auth=self.grafana_auth
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(
                            f"Failed to get Grafana alerts: {await response.text()}"
                        )
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error getting Grafana alerts: {str(e)}")
            return []
            
    def log_error(
        self,
        error_message: str,
        error_type: str = "general",
        component: str = "unknown",
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Log an error with context."""
        try:
            # Increment error counter
            self.error_counter.labels(
                error_type=error_type,
                component=component
            ).inc()
            
            # Update error tracking
            self.error_counts[error_type] += 1
            error_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': error_type,
                'component': component,
                'message': error_message,
                'context': context or {},
                'traceback': traceback.format_exc() if exception else None
            }
            self.error_history.append(error_entry)
            
            # Log error
            self.logger.error(
                f"Error in {component}: {error_message}",
                extra={
                    'error_type': error_type,
                    'context': context,
                    'exception': str(exception) if exception else None
                }
            )
            
            # Store error in persistent storage if configured
            if self.config.get('store_errors', False):
                self._store_error(error_entry)
                
        except Exception as e:
            self.logger.error(f"Error in error logging: {str(e)}")
            
    def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric value."""
        try:
            # Get the appropriate metric
            metric = getattr(self, metric_name, None)
            if metric:
                if labels:
                    metric.labels(**labels).set(value)
                else:
                    metric.set(value)
                    
            # Store in performance metrics
            self.performance_metrics[metric_name].append({
                'timestamp': datetime.utcnow().isoformat(),
                'value': value,
                'labels': labels or {}
            })
            
        except Exception as e:
            self.logger.error(f"Error recording metric: {str(e)}")
            
    def record_rate_limit(
        self,
        platform: str,
        limit_type: str,
        remaining: int,
        reset_time: datetime
    ):
        """Record rate limit information."""
        try:
            # Update rate limit counter
            self.rate_limit_counter.labels(
                platform=platform,
                limit_type=limit_type
            ).inc()
            
            # Store rate limit metrics
            self.rate_limit_metrics[platform][limit_type] = {
                'remaining': remaining,
                'reset_time': reset_time.isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error recording rate limit: {str(e)}")
            
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of system errors."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': dict(self.error_counts),
            'recent_errors': self.error_history[-10:] if self.error_history else []
        }
        
    def get_performance_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance metrics."""
        return dict(self.performance_metrics)
        
    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status."""
        return dict(self.rate_limit_metrics)
        
    def _store_error(self, error_entry: Dict[str, Any]):
        """Store error in persistent storage."""
        # Implementation depends on storage backend
        # This could be a database, file system, or external service
        pass
        
    async def send_metrics_to_prometheus(self):
        """Send metrics to Prometheus push gateway."""
        try:
            if not self.config.get('prometheus_push_gateway'):
                return
                
            async with aiohttp.ClientSession() as session:
                await prom.push_to_gateway(
                    self.config['prometheus_push_gateway'],
                    job='affiliate_outreach_system',
                    registry=prom.REGISTRY
                )
                
        except Exception as e:
            self.logger.error(f"Error sending metrics to Prometheus: {str(e)}")
            
    def cleanup(self):
        """Cleanup resources."""
        try:
            # Clear old metrics
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            for metric_name, values in self.performance_metrics.items():
                self.performance_metrics[metric_name] = [
                    v for v in values
                    if datetime.fromisoformat(v['timestamp']) > cutoff_time
                ]
                
            # Clear old error history
            self.error_history = [
                e for e in self.error_history
                if datetime.fromisoformat(e['timestamp']) > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}") 