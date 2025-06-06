"""
Unified monitoring and logging service for the application.
Handles:
- System metrics and monitoring
- Structured logging
- Alert management
- Performance tracking
- Error tracking and reporting
"""

from typing import Dict, Any, List, Optional
import time
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client.exposition import start_http_server
import logging
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import requests
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database.models import Webhook, WebhookDelivery, MessageLog, Alert, AlertType, AlertSeverity, WebhookMetric, SystemMetric
import asyncio
import aiohttp
from pydantic import BaseModel, Field, ConfigDict
import statistics
import traceback
import structlog
from pythonjsonlogger import json
from contextvars import ContextVar
import uuid
import sys
from app.services.monitoring import MonitoringService, AlertType, AlertSeverity, AlertConfig

# Context variables for request tracking
request_id = ContextVar('request_id', default=None)
user_id = ContextVar('user_id', default=None)

# Prometheus metrics
WEBHOOK_DELIVERY_TOTAL = Counter(
    'webhook_delivery_total',
    'Total number of webhook deliveries',
    ['webhook_id', 'event_type', 'status']
)

WEBHOOK_DELIVERY_DURATION = Histogram(
    'webhook_delivery_duration_seconds',
    'Webhook delivery duration in seconds',
    ['webhook_id', 'event_type']
)

WEBHOOK_ERROR_TOTAL = Counter(
    'webhook_error_total',
    'Total number of webhook errors',
    ['webhook_id', 'error_type']
)

MESSAGE_PROCESSING_DURATION = Histogram(
    'message_processing_duration_seconds',
    'Message processing duration in seconds',
    ['message_type']
)

ACTIVE_ALERTS = Gauge(
    'active_alerts',
    'Number of active alerts',
    ['severity']
)

class CustomJsonFormatter(json.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add request context
        if request_id.get():
            log_record['request_id'] = request_id.get()
        if user_id.get():
            log_record['user_id'] = user_id.get()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add module and function information
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Include extra fields from record
        if hasattr(record, 'extra'):
            log_record.update(record.extra)

class AlertConfig(BaseModel):
    """Configuration for alerting."""
    webhook_url: Optional[str] = None
    email_recipients: List[str] = Field(default_factory=list)
    slack_webhook_url: Optional[str] = None
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    notification_cooldown: int = Field(300, ge=60)  # 5 minutes minimum
    model_config = ConfigDict(from_attributes=True)

class MonitoringService:
    """Unified service for monitoring and logging."""
    
    def __init__(
        self,
        db: Session,
        prometheus_port: int = 8000,
        alert_config: Optional[AlertConfig] = None,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_console: bool = True
    ):
        # Initialize logging
        self.logger = self._setup_logger(log_level, log_file, enable_console)
        self.error_logger = self._setup_error_logger(log_file)
        
        # Initialize structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Initialize Prometheus metrics
        self.prospect_processing_time = Histogram(
            'prospect_processing_seconds',
            'Time spent processing prospects',
            ['operation']
        )
        
        self.prospect_scores = Gauge(
            'prospect_scores',
            'Current prospect scores',
            ['prospect_id']
        )
        
        self.message_send_attempts = Counter(
            'message_send_attempts_total',
            'Total number of message send attempts',
            ['platform', 'status']
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'Duration of API requests',
            ['endpoint', 'method']
        )
        
        self.error_count = Counter(
            'error_count_total',
            'Total number of errors',
            ['service', 'error_type']
        )
        
        self.active_campaigns = Gauge(
            'active_campaigns',
            'Number of active campaigns'
        )
        
        self.prospects_processed = Counter(
            'prospects_processed_total',
            'Total number of prospects processed',
            ['status']
        )
        
        self.social_api_calls = Counter(
            'social_api_calls_total',
            'Total number of social media API calls',
            ['platform', 'endpoint']
        )
        
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Number of rate limit hits',
            ['platform']
        )
        
        # Start Prometheus metrics server
        start_http_server(prometheus_port)
        self.logger.info(f"Prometheus metrics server started on port {prometheus_port}")
        
        self.db = db
        self.prometheus_port = prometheus_port
        self.alert_config = alert_config or AlertConfig()
        self._alert_cooldowns = {}  # Track last notification time per alert type
    
    def _setup_logger(
        self,
        log_level: str,
        log_file: Optional[str],
        enable_console: bool
    ) -> logging.Logger:
        """Set up the main logger with JSON formatting."""
        logger = logging.getLogger('app')
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatters
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        
        # Add console handler if enabled
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(json_formatter)
            logger.addHandler(console_handler)
        
        # Add file handler if log file specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(json_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _setup_error_logger(self, log_file: Optional[str]) -> logging.Logger:
        """Set up a separate logger for errors with full stack traces."""
        error_logger = logging.getLogger('error')
        error_logger.setLevel(logging.ERROR)
        
        if log_file:
            error_file = str(Path(log_file).parent / 'error.log')
            error_handler = logging.FileHandler(error_file)
            error_handler.setFormatter(CustomJsonFormatter())
            error_logger.addHandler(error_handler)
        
        return error_logger
    
    # Logging methods
    def log_request(self, request_id: str, user_id: Optional[str] = None):
        """Set request context for logging."""
        self.request_id.set(request_id)
        if user_id:
            self.user_id.set(user_id)
    
    def clear_request_context(self):
        """Clear request context."""
        request_id.set(None)
        user_id.set(None)
    
    def info(self, message: str, **kwargs):
        """Log info level message with additional context."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message with additional context."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log error level message with exception info and additional context."""
        if exc_info:
            kwargs['exception'] = {
                'type': type(exc_info).__name__,
                'message': str(exc_info),
                'traceback': traceback.format_exc()
            }
        self.logger.error(message, extra=kwargs)
        self.error_logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log critical level message with exception info and additional context."""
        if exc_info:
            kwargs['exception'] = {
                'type': type(exc_info).__name__,
                'message': str(exc_info),
                'traceback': traceback.format_exc()
            }
        self.logger.critical(message, extra=kwargs)
        self.error_logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def log_metric(self, metric_name: str, value: float, **kwargs):
        """Log a metric with additional context."""
        self.info(
            f"Metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            **kwargs
        )
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log API request details."""
        self.info(
            f"API Request: {method} {path}",
            request_method=method,
            request_path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_database_query(
        self,
        query: str,
        duration_ms: float,
        **kwargs
    ):
        """Log database query details."""
        self.info(
            "Database Query",
            query=query,
            duration_ms=duration_ms,
            **kwargs
        )
    
    # Monitoring methods
    def track_prospect_processing(self, operation: str):
        """Decorator to track prospect processing time."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.prospect_processing_time.labels(operation=operation).time():
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def track_api_request(self, endpoint: str, method: str):
        """Decorator to track API request duration."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.api_request_duration.labels(endpoint=endpoint, method=method).time():
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def record_prospect_score(self, prospect_id: str, score: float):
        """Record a prospect's score."""
        self.prospect_scores.labels(prospect_id=prospect_id).set(score)
    
    def record_message_send(self, platform: str, status: str):
        """Record a message send attempt."""
        self.message_send_attempts.labels(platform=platform, status=status).inc()
    
    def record_error(self, service: str, error_type: str):
        """Record an error occurrence."""
        self.error_count.labels(service=service, error_type=error_type).inc()
    
    def update_active_campaigns(self, count: int):
        """Update the number of active campaigns."""
        self.active_campaigns.set(count)
    
    def record_prospect_processed(self, status: str):
        """Record a processed prospect."""
        self.prospects_processed.labels(status=status).inc()
    
    def record_social_api_call(self, platform: str, endpoint: str):
        """Record a social media API call."""
        self.social_api_calls.labels(platform=platform, endpoint=endpoint).inc()
    
    def record_rate_limit_hit(self, platform: str):
        """Record a rate limit hit."""
        self.rate_limit_hits.labels(platform=platform).inc()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            'active_campaigns': self.active_campaigns._value.get(),
            'total_errors': sum(self.error_count._metrics.values()),
            'total_prospects_processed': sum(self.prospects_processed._metrics.values()),
            'total_message_sends': sum(self.message_send_attempts._metrics.values()),
            'total_api_calls': sum(self.social_api_calls._metrics.values())
        }
    
    def export_metrics_to_file(self, output_dir: str = "reports/metrics"):
        """Export current metrics to a JSON file."""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f'metrics_{timestamp}.json')
            
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_metrics_summary(),
                'prospect_scores': {
                    label: value.get()
                    for label, value in self.prospect_scores._metrics.items()
                },
                'error_counts': {
                    label: value.get()
                    for label, value in self.error_count._metrics.items()
                },
                'message_send_stats': {
                    label: value.get()
                    for label, value in self.message_send_attempts._metrics.items()
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            self.logger.info(f"Metrics exported to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}")
            return None
    
    async def track_webhook_delivery(
        self,
        webhook_id: str,
        event_type: str,
        duration: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Track webhook delivery metrics and create alerts if necessary."""
        try:
            # Update Prometheus metrics
            WEBHOOK_DELIVERY_TOTAL.labels(
                webhook_id=webhook_id,
                event_type=event_type,
                status='success' if success else 'failure'
            ).inc()
            
            WEBHOOK_DELIVERY_DURATION.labels(
                webhook_id=webhook_id,
                event_type=event_type
            ).observe(duration)
            
            if not success and error:
                WEBHOOK_ERROR_TOTAL.labels(
                    webhook_id=webhook_id,
                    error_type=error.split(':')[0]
                ).inc()
            
            # Create webhook metric record
            metric = WebhookMetric(
                webhook_id=webhook_id,
                event_type=event_type,
                duration=duration,
                success=success,
                error=error,
                timestamp=datetime.now(timezone.utc)
            )
            self.db.add(metric)
            self.db.commit()
            
            # Check alert conditions
            await self.check_alert_conditions(webhook_id)
            
        except Exception as e:
            self.logger.error(f"Error tracking webhook delivery: {e}")
            self.db.rollback()
    
    async def track_message_processing(
        self,
        message_type: str,
        duration: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Track message processing metrics."""
        try:
            MESSAGE_PROCESSING_DURATION.labels(
                message_type=message_type
            ).observe(duration)
            
            # Log message processing
            self.info(
                f"Message processing completed",
                message_type=message_type,
                duration=duration,
                success=success,
                error=error
            )
            
            # Create message log record
            log = MessageLog(
                message_type=message_type,
                duration=duration,
                success=success,
                error=error,
                timestamp=datetime.now(timezone.utc)
            )
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Error tracking message processing: {e}")
            self.db.rollback()
    
    async def check_alert_conditions(self, webhook_id: str) -> None:
        """Check conditions for creating alerts."""
        try:
            # Calculate failure rate
            failure_rate = await self.calculate_failure_rate(webhook_id)
            
            # Check against thresholds
            if failure_rate > self.alert_config.alert_thresholds.get('webhook_failure_rate', 0.1):
                await self._create_alert(
                    alert_type=AlertType.WEBHOOK_FAILURE,
                    severity=AlertSeverity.HIGH,
                    message=f"High webhook failure rate: {failure_rate:.2%}",
                    alert_metadata={'webhook_id': webhook_id, 'failure_rate': failure_rate}
                )
            
            # Check response time
            avg_duration = await self._get_average_webhook_duration(webhook_id)
            if avg_duration > self.alert_config.alert_thresholds.get('webhook_response_time', 5.0):
                await self._create_alert(
                    alert_type=AlertType.WEBHOOK_SLOW,
                    severity=AlertSeverity.MEDIUM,
                    message=f"Slow webhook response time: {avg_duration:.2f}s",
                    alert_metadata={'webhook_id': webhook_id, 'avg_duration': avg_duration}
                )
            
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
    
    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        alert_metadata: Dict[str, Any],
        skip_notifications: bool = False
    ) -> Optional[Alert]:
        """Create a new alert and send notifications."""
        try:
            # Check cooldown
            last_notification = self._alert_cooldowns.get(alert_type)
            if last_notification and (datetime.now(timezone.utc) - last_notification).total_seconds() < self.alert_config.notification_cooldown:
                return None
            
            # Create alert
            alert = Alert(
                type=alert_type,
                severity=severity,
                message=message,
                metadata=alert_metadata,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(alert)
            self.db.commit()
            
            # Update active alerts metric
            ACTIVE_ALERTS.labels(severity=severity.value).inc()
            
            # Send notifications
            if not skip_notifications:
                await self._send_notifications(alert)
                self._alert_cooldowns[alert_type] = datetime.now(timezone.utc)
            
            return alert
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            self.db.rollback()
            return None
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        try:
            # Send webhook notification
            if self.alert_config.webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        self.alert_config.webhook_url,
                        json={
                            'type': alert.type.value,
                            'severity': alert.severity.value,
                            'message': alert.message,
                            'metadata': alert.metadata,
                            'timestamp': alert.created_at.isoformat()
                        }
                    )
            
            # Send Slack notification
            if self.alert_config.slack_webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        self.alert_config.slack_webhook_url,
                        json={
                            'text': f"*{alert.severity.value.upper()} Alert*\n{alert.message}",
                            'attachments': [{
                                'color': 'danger' if alert.severity == AlertSeverity.HIGH else 'warning',
                                'fields': [
                                    {'title': k, 'value': str(v), 'short': True}
                                    for k, v in alert.metadata.items()
                                ]
                            }]
                        }
                    )
            
            # Send email notifications
            if self.alert_config.email_recipients:
                # TODO: Implement email notification
                pass
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
    
    async def calculate_failure_rate(self, webhook_id: str) -> float:
        """Calculate the failure rate for a webhook."""
        try:
            # Get recent deliveries
            recent_deliveries = self.db.query(WebhookDelivery).filter(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.timestamp >= datetime.now(timezone.utc) - timedelta(hours=1)
            ).all()
            
            if not recent_deliveries:
                return 0.0
            
            # Calculate failure rate
            failures = sum(1 for d in recent_deliveries if not d.success)
            return failures / len(recent_deliveries)
            
        except Exception as e:
            self.logger.error(f"Error calculating failure rate: {e}")
            return 0.0
    
    async def _get_average_webhook_duration(self, webhook_id: str) -> float:
        """Calculate average webhook delivery duration."""
        try:
            # Get recent deliveries
            recent_deliveries = self.db.query(WebhookDelivery).filter(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.timestamp >= datetime.now(timezone.utc) - timedelta(hours=1)
            ).all()
            
            if not recent_deliveries:
                return 0.0
            
            # Calculate average duration
            return statistics.mean(d.duration for d in recent_deliveries)
            
        except Exception as e:
            self.logger.error(f"Error calculating average duration: {e}")
            return 0.0
    
    async def get_system_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get system-wide metrics."""
        try:
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(hours=1)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            
            # Get message processing metrics
            message_metrics = self.db.query(
                MessageLog.message_type,
                func.count().label('total'),
                func.avg(MessageLog.duration).label('avg_duration'),
                func.sum(case((MessageLog.success == True, 1), else_=0)).label('successes'),
                func.sum(case((MessageLog.success == False, 1), else_=0)).label('failures')
            ).filter(
                MessageLog.timestamp.between(start_time, end_time)
            ).group_by(MessageLog.message_type).all()
            
            # Get webhook metrics
            webhook_metrics = self.db.query(
                WebhookDelivery.webhook_id,
                func.count().label('total'),
                func.avg(WebhookDelivery.duration).label('avg_duration'),
                func.sum(case((WebhookDelivery.success == True, 1), else_=0)).label('successes'),
                func.sum(case((WebhookDelivery.success == False, 1), else_=0)).label('failures')
            ).filter(
                WebhookDelivery.timestamp.between(start_time, end_time)
            ).group_by(WebhookDelivery.webhook_id).all()
            
            # Get alert metrics
            alert_metrics = self.db.query(
                Alert.severity,
                func.count().label('count')
            ).filter(
                Alert.created_at.between(start_time, end_time)
            ).group_by(Alert.severity).all()
            
            return {
                'message_metrics': [
                    {
                        'type': m.message_type,
                        'total': m.total,
                        'avg_duration': float(m.avg_duration) if m.avg_duration else 0.0,
                        'success_rate': float(m.successes) / m.total if m.total > 0 else 0.0,
                        'failure_rate': float(m.failures) / m.total if m.total > 0 else 0.0
                    }
                    for m in message_metrics
                ],
                'webhook_metrics': [
                    {
                        'webhook_id': w.webhook_id,
                        'total': w.total,
                        'avg_duration': float(w.avg_duration) if w.avg_duration else 0.0,
                        'success_rate': float(w.successes) / w.total if w.total > 0 else 0.0,
                        'failure_rate': float(w.failures) / w.total if w.total > 0 else 0.0
                    }
                    for w in webhook_metrics
                ],
                'alert_metrics': [
                    {
                        'severity': a.severity.value,
                        'count': a.count
                    }
                    for a in alert_metrics
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def get_webhook_metrics(
        self,
        webhook_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Any]:
        """Get metrics for a specific webhook."""
        try:
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(hours=1)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            
            # Get delivery metrics
            deliveries = self.db.query(WebhookDelivery).filter(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.timestamp.between(start_time, end_time)
            ).order_by(WebhookDelivery.timestamp.desc()).all()
            
            return [
                {
                    'timestamp': d.timestamp.isoformat(),
                    'event_type': d.event_type,
                    'duration': d.duration,
                    'success': d.success,
                    'error': d.error
                }
                for d in deliveries
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting webhook metrics: {e}")
            return []
    
    def update_alert_status(self, alert: Alert, is_resolved: bool) -> None:
        """Update the status of an alert."""
        try:
            alert.resolved_at = datetime.now(timezone.utc) if is_resolved else None
            self.db.commit()
            
            # Update active alerts metric
            if is_resolved:
                ACTIVE_ALERTS.labels(severity=alert.severity.value).dec()
            
        except Exception as e:
            self.logger.error(f"Error updating alert status: {e}")
            self.db.rollback()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        try:
            return self.db.query(Alert).filter(
                Alert.resolved_at.is_(None)
            ).order_by(Alert.created_at.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []
    
    def get_alert_history(self) -> List[Alert]:
        """Get alert history."""
        try:
            return self.db.query(Alert).order_by(
                Alert.created_at.desc()
            ).all()
            
        except Exception as e:
            self.logger.error(f"Error getting alert history: {e}")
            return []

    def send_alert(self, alert_config: AlertConfig):
        print(f"Alert: {alert_config.alert_type.value} - {alert_config.severity.value} - {alert_config.message}")

def log_execution_time(monitoring_service: MonitoringService):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                monitoring_service.info(
                    f"Function {func.__name__} executed successfully",
                    function_name=func.__name__,
                    duration_ms=duration
                )
                return result
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                monitoring_service.error(
                    f"Function {func.__name__} failed",
                    function_name=func.__name__,
                    duration_ms=duration,
                    exc_info=e
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                monitoring_service.info(
                    f"Function {func.__name__} executed successfully",
                    function_name=func.__name__,
                    duration_ms=duration
                )
                return result
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                monitoring_service.error(
                    f"Function {func.__name__} failed",
                    function_name=func.__name__,
                    duration_ms=duration,
                    exc_info=e
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 