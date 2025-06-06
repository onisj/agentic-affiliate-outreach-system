import logging
import sys
import os
from pathlib import Path

def setup_logging(name: str = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        name: Optional name for the logger. If not provided, returns the root logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the logger
    logger = logging.getLogger(name)
    
    # Return existing logger if already configured
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # File handler for errors
    error_log = logs_dir / "error.log"
    file_handler = logging.FileHandler(error_log)
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Stream handler for console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_formatter = logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(stream_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

# Create root logger
root_logger = setup_logging()

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module requesting the logger
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logging(name)