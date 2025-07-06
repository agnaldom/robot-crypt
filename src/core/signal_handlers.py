"""
Signal handling for graceful shutdown and other signal-based operations.
"""
import signal
import sys
import threading
from typing import Callable, Dict, Optional

from .logging_setup import logger


class SignalHandler:
    """
    Signal handler for managing graceful shutdowns and other signal-based operations.
    """
    
    def __init__(self):
        """Initialize the signal handler."""
        self.shutdown_event = threading.Event()
        self.handlers: Dict[int, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default signal handlers."""
        # Register SIGINT (Ctrl+C) and SIGTERM
        self.register_handler(signal.SIGINT, self._handle_shutdown)
        self.register_handler(signal.SIGTERM, self._handle_shutdown)
    
    def register_handler(self, sig: int, handler: Callable):
        """
        Register a signal handler.
        
        Args:
            sig (int): Signal number to handle
            handler (Callable): Handler function
        """
        self.handlers[sig] = handler
        signal.signal(sig, self._signal_receiver)
        logger.debug(f"Registered handler for signal {sig}")
    
    def _signal_receiver(self, signum, frame):
        """
        Signal receiver that delegates to the appropriate handler.
        
        Args:
            signum (int): Signal number
            frame: Current stack frame
        """
        if signum in self.handlers:
            logger.debug(f"Received signal {signum}")
            self.handlers[signum](signum, frame)
    
    def _handle_shutdown(self, signum, frame):
        """
        Default handler for shutdown signals.
        
        Args:
            signum (int): Signal number
            frame: Current stack frame
        """
        logger.info(f"Received shutdown signal {signum}, initiating graceful shutdown")
        self.shutdown_event.set()
    
    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for shutdown signal.
        
        Args:
            timeout (float, optional): Timeout in seconds. Defaults to None (wait indefinitely).
        
        Returns:
            bool: True if shutdown was signaled, False if timeout occurred
        """
        return self.shutdown_event.wait(timeout)
    
    def is_shutdown_requested(self) -> bool:
        """
        Check if shutdown has been requested.
        
        Returns:
            bool: True if shutdown has been requested
        """
        return self.shutdown_event.is_set()
    
    def request_shutdown(self):
        """Request a shutdown manually."""
        logger.info("Manual shutdown requested")
        self.shutdown_event.set()


# Create default signal handler
signal_handler = SignalHandler()
