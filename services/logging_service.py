import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path
import structlog
from pythonjsonlogger import json
from functools import wraps
import traceback
from contextvars import ContextVar
import uuid
import asyncio

# Context variables for request tracking
request_id = ContextVar('request_id', default=None)
user_id = ContextVar('user_id', default=None)

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

class LoggingService:
    """Service for handling structured logging and error tracking."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_console: bool = True
    ):
        self.logger = self._setup_logger(log_level, log_file, enable_console)
        self.error_logger = self._setup_error_logger(log_file)
        self.request_id = ContextVar('request_id', default=None)
        self.user_id = ContextVar('user_id', default=None)
        
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

def log_execution_time(logger: LoggingService):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                logger.info(
                    f"Function {func.__name__} executed successfully",
                    function_name=func.__name__,
                    duration_ms=duration
                )
                return result
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                logger.error(
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
                logger.info(
                    f"Function {func.__name__} executed successfully",
                    function_name=func.__name__,
                    duration_ms=duration
                )
                return result
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                logger.error(
                    f"Function {func.__name__} failed",
                    function_name=func.__name__,
                    duration_ms=duration,
                    exc_info=e
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 