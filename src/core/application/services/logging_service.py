import logging
import time
import json
from functools import wraps
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LoggingService:
    def __init__(self, log_level='INFO', log_file=None, enable_console=True):
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.enable_console = enable_console
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(str(id(self)))
        self.logger.setLevel(self.log_level)
        formatter = logging.Formatter('%(message)s')
        # Remove existing handlers
        self.logger.handlers = []
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def info(self, message, extra=None):
        log_entry = {"level": "INFO", "message": message}
        if extra:
            log_entry.update(extra)
        self.logger.info(json.dumps(log_entry))

    def error(self, message, exc_info=None, extra=None):
        log_entry = {"level": "ERROR", "message": message}
        if exc_info:
            log_entry["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info)
            }
        if extra:
            log_entry.update(extra)
        self.logger.error(json.dumps(log_entry))

    def log_metric(self, metric_name, metric_value, tags=None):
        log_entry = {
            "level": "INFO",
            "metric_name": metric_name,
            "metric_value": metric_value,
            "tags": tags or {}
        }
        self.logger.info(json.dumps(log_entry))

    def log_api_request(self, request_data: Dict[str, Any]) -> None:
        """Log API request data."""
        logger.info(f"API Request: {request_data}")
        
    def log_request(self, request_data: Dict[str, Any]) -> None:
        """Alias for log_api_request for backward compatibility."""
        self.log_api_request(request_data)

    def log_execution_time(self, logger_instance):
        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        duration_ms = int((time.time() - start_time) * 1000)
                        logger_instance.info(
                            f"{func.__name__} executed",
                            extra={"function_name": func.__name__, "duration_ms": duration_ms}
                        )
                        return result
                    except Exception as e:
                        duration_ms = int((time.time() - start_time) * 1000)
                        logger_instance.error(
                            f"{func.__name__} failed",
                            exc_info=e,
                            extra={"function_name": func.__name__, "duration_ms": duration_ms}
                        )
                        raise
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = int((time.time() - start_time) * 1000)
                        logger_instance.info(
                            f"{func.__name__} executed",
                            extra={"function_name": func.__name__, "duration_ms": duration_ms}
                        )
                        return result
                    except Exception as e:
                        duration_ms = int((time.time() - start_time) * 1000)
                        logger_instance.error(
                            f"{func.__name__} failed",
                            exc_info=e,
                            extra={"function_name": func.__name__, "duration_ms": duration_ms}
                        )
                        raise
                return sync_wrapper
        return decorator

# Export the log_execution_time decorator factory
log_execution_time = LoggingService().log_execution_time 