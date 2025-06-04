import logging
import sys

def setup_logging():
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all logs for tests

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler for errors
    file_handler = logging.FileHandler("error.log")
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Stream handler for console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)  # Support --log-cli-level=DEBUG
    stream_formatter = logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(stream_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

# Instantiate logger
logger = setup_logging()