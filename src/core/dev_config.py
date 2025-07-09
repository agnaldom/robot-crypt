"""
Development configuration utilities for Robot-Crypt API.
"""

import logging
from typing import Dict, Any
from src.core.config import settings

logger = logging.getLogger(__name__)


class DevConfig:
    """Development configuration helper."""
    
    @staticmethod
    def get_dev_rate_limits() -> Dict[str, Any]:
        """Get development-friendly rate limits."""
        return {
            "enabled": not settings.DEBUG,
            "burst_multiplier": 10 if settings.DEBUG else 1,
            "regular_multiplier": 5 if settings.DEBUG else 1,
            "whitelisted_ips": [
                "127.0.0.1",
                "localhost",
                "::1",
                "0.0.0.0",
                "unknown"
            ]
        }
    
    @staticmethod
    def get_auth_config() -> Dict[str, Any]:
        """Get authentication configuration."""
        return {
            "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "debug_mode": settings.DEBUG,
            "enhanced_logging": settings.DEBUG,
            "allow_test_tokens": settings.DEBUG
        }
    
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """Get CORS configuration."""
        if settings.DEBUG:
            return {
                "allow_origins": ["*"],
                "allow_methods": ["*"],
                "allow_headers": ["*"],
                "allow_credentials": True
            }
        else:
            return {
                "allow_origins": settings.ALLOWED_ORIGINS,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
                "allow_credentials": True
            }
    
    @staticmethod
    def log_startup_config():
        """Log startup configuration."""
        logger.info("🔧 Development Configuration:")
        logger.info(f"   Debug Mode: {settings.DEBUG}")
        logger.info(f"   Rate Limiting: {'Disabled' if settings.DEBUG else 'Enabled'}")
        logger.info(f"   Enhanced Logging: {'Enabled' if settings.DEBUG else 'Disabled'}")
        logger.info(f"   CORS: {'Permissive' if settings.DEBUG else 'Restrictive'}")
        logger.info(f"   Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        
        if settings.DEBUG:
            logger.info("⚠️  Development mode - use only for development!")
        else:
            logger.info("🔒 Production mode - security features enabled")


def setup_dev_environment():
    """Setup development environment configurations."""
    if settings.DEBUG:
        # Enable more verbose logging for development
        logging.getLogger("src.middleware").setLevel(logging.DEBUG)
        logging.getLogger("src.core.security").setLevel(logging.DEBUG)
        logging.getLogger("src.api").setLevel(logging.DEBUG)
        
        logger.info("🛠️  Development environment configured")
    else:
        logger.info("🏭 Production environment configured")
