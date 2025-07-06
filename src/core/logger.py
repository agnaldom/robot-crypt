"""
Logger utility for Robot-Crypt API.

Provides standardized logging configuration and formatters for the application.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from src.core.config import settings


class CustomFormatter(logging.Formatter):
    """Custom log formatter with colors and structured output."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True, use_json: bool = False):
        """
        Initialize the custom formatter.
        
        Args:
            use_colors: Whether to use colored output
            use_json: Whether to output in JSON format
        """
        self.use_colors = use_colors
        self.use_json = use_json
        
        if use_json:
            super().__init__()
        else:
            format_string = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
            super().__init__(format_string, datefmt='%Y-%m-%d %H:%M:%S')
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record."""
        if self.use_json:
            return self._format_json(record)
        else:
            return self._format_text(record)
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Format record as colored text."""
        # Apply color if enabled
        if self.use_colors and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the basic message
        formatted = super().format(record)
        
        # Add extra context if available
        if hasattr(record, 'user_id'):
            formatted = f"[User:{record.user_id}] {formatted}"
        
        if hasattr(record, 'request_id'):
            formatted = f"[Req:{record.request_id}] {formatted}"
        
        return formatted
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add extra fields if available
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class RobotCryptLogger:
    """Main logger class for Robot-Crypt."""
    
    def __init__(self, name: str = "robot-crypt"):
        """Initialize the logger."""
        self.name = name
        self.logger = logging.getLogger(name)
        self._configured = False
    
    def configure(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        use_colors: bool = True,
        use_json: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Configure the logger with handlers and formatters.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            use_colors: Whether to use colored console output
            use_json: Whether to use JSON format
            max_file_size: Maximum file size before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            Configured logger instance
        """
        if self._configured:
            return self.logger
        
        # Set log level
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = CustomFormatter(use_colors=use_colors, use_json=use_json)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(numeric_level)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            self._setup_file_handler(log_file, use_json, max_file_size, backup_count, numeric_level)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        self._configured = True
        return self.logger
    
    def _setup_file_handler(
        self,
        log_file: str,
        use_json: bool,
        max_file_size: int,
        backup_count: int,
        level: int
    ):
        """Setup rotating file handler."""
        from logging.handlers import RotatingFileHandler
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Use JSON format for files for better parsing
        file_formatter = CustomFormatter(use_colors=False, use_json=True)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        if not self._configured:
            self.configure()
        return self.logger


# Global logger instance
_robot_crypt_logger = RobotCryptLogger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (if None, uses module name from caller)
        
    Returns:
        Logger instance
    """
    if name is None:
        # Get the caller's module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'robot-crypt')
    
    return logging.getLogger(name)


def configure_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    use_colors: bool = True,
    use_json: bool = False
) -> logging.Logger:
    """
    Configure the main application logger.
    
    Args:
        level: Log level from settings or parameter
        log_file: Log file path from settings or parameter
        use_colors: Whether to use colored console output
        use_json: Whether to use JSON format for logs
        
    Returns:
        Configured main logger
    """
    # Use settings defaults if not provided
    level = level or getattr(settings, 'LOG_LEVEL', 'INFO')
    log_file = log_file or getattr(settings, 'LOG_FILE', None)
    
    # Configure in production to use JSON and file logging
    if not getattr(settings, 'DEBUG', True):
        use_json = True
        if not log_file:
            log_file = "logs/robot-crypt.log"
    
    return _robot_crypt_logger.configure(
        level=level,
        log_file=log_file,
        use_colors=use_colors,
        use_json=use_json
    )


def add_context(logger: logging.Logger, **kwargs):
    """
    Add context to logger (e.g., user_id, request_id).
    
    Args:
        logger: Logger instance
        **kwargs: Context data to add
    """
    # Store context in logger for use by formatters
    for key, value in kwargs.items():
        setattr(logger, f'_context_{key}', value)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log records."""
    
    def process(self, msg, kwargs):
        """Add context to log record."""
        # Add extra context from adapter
        for key, value in self.extra.items():
            kwargs.setdefault('extra', {})[key] = value
        
        return msg, kwargs


def get_contextual_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with context that will be added to all log messages.
    
    Args:
        name: Logger name
        **context: Context data (e.g., user_id=123, request_id="abc")
        
    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)


# Export the main logger for easy access
logger = _robot_crypt_logger.get_logger()


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    test_logger = configure_logging(level="DEBUG", use_colors=True)
    
    # Test different log levels
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    # Test contextual logging
    contextual_logger = get_contextual_logger("test", user_id=123, request_id="abc-123")
    contextual_logger.info("This message has context")
    
    # Test exception logging
    try:
        1 / 0
    except Exception:
        test_logger.exception("Exception occurred")
