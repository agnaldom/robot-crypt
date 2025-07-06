"""
Logging configuration for Robot-Crypt.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from .config import settings


def setup_logging(log_level=None, log_file=None):
    """
    Configure application logging.
    
    Args:
        log_level (str, optional): Logging level. Defaults to settings.LOG_LEVEL.
        log_file (str, optional): Log file path. Defaults to settings.LOG_FILE.
    
    Returns:
        logging.Logger: Configured logger
    """
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    if log_file is None:
        log_file = settings.LOG_FILE
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logger
    logger = logging.getLogger("robot_crypt")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )
    
    # File handler - rotating file that creates new file when max size is reached
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Capture warnings
    logging.captureWarnings(True)
    
    logger.info("Logging configured with level: %s", log_level)
    return logger


# Create default logger
logger = setup_logging()
