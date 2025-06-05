import pytest
import logging
import json
from pathlib import Path
from services.logging_service import LoggingService, log_execution_time
import asyncio
from datetime import datetime

@pytest.fixture
def logger(tmp_path):
    """Create a logger instance with a temporary log file."""
    log_file = tmp_path / "test.log"
    return LoggingService(
        log_level="DEBUG",
        log_file=str(log_file),
        enable_console=False
    )

def test_log_info(logger, tmp_path):
    """Test info level logging."""
    logger.info("Test info message", extra={"test": "data"})
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test info message"
    assert log_entry["test"] == "data"

def test_log_error(logger, tmp_path):
    """Test error level logging with exception."""
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Test error message", exc_info=e)
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert log_entry["level"] == "ERROR"
    assert log_entry["message"] == "Test error message"
    assert "exception" in log_entry
    assert log_entry["exception"]["type"] == "ValueError"
    assert log_entry["exception"]["message"] == "Test error"

def test_log_metric(logger, tmp_path):
    """Test metric logging."""
    logger.log_metric("test_metric", 42.0, tags={"test": "tag"})
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert log_entry["level"] == "INFO"
    assert log_entry["metric_name"] == "test_metric"
    assert log_entry["metric_value"] == 42.0
    assert log_entry["tags"] == {"test": "tag"}

def test_log_api_request(logger, tmp_path):
    """Test API request logging."""
    logger.log_api_request(
        method="GET",
        path="/test",
        status_code=200,
        duration_ms=100.0,
        client_ip="127.0.0.1"
    )
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert log_entry["level"] == "INFO"
    assert log_entry["request_method"] == "GET"
    assert log_entry["request_path"] == "/test"
    assert log_entry["status_code"] == 200
    assert log_entry["duration_ms"] == 100.0
    assert log_entry["client_ip"] == "127.0.0.1"

def test_log_execution_time_sync(logger, tmp_path):
    """Test execution time logging for sync functions."""
    @log_execution_time(logger)
    def test_function():
        return "test"
    
    result = test_function()
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert result == "test"
    assert log_entry["level"] == "INFO"
    assert log_entry["function_name"] == "test_function"
    assert "duration_ms" in log_entry

@pytest.mark.asyncio
async def test_log_execution_time_async(logger, tmp_path):
    """Test execution time logging for async functions."""
    @log_execution_time(logger)
    async def test_async_function():
        await asyncio.sleep(0.1)
        return "test"
    
    result = await test_async_function()
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert result == "test"
    assert log_entry["level"] == "INFO"
    assert log_entry["function_name"] == "test_async_function"
    assert "duration_ms" in log_entry
    assert log_entry["duration_ms"] >= 100  # Should be at least 100ms due to sleep

def test_log_execution_time_error(logger, tmp_path):
    """Test execution time logging with error."""
    @log_execution_time(logger)
    def test_error_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        test_error_function()
    
    log_file = tmp_path / "test.log"
    with open(log_file) as f:
        log_entry = json.loads(f.readline())
    
    assert log_entry["level"] == "ERROR"
    assert log_entry["function_name"] == "test_error_function"
    assert "duration_ms" in log_entry
    assert "exception" in log_entry
    assert log_entry["exception"]["type"] == "ValueError"
    assert log_entry["exception"]["message"] == "Test error" 