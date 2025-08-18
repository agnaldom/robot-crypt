"""
Configuration for BingX trading bot.
"""
import os
from typing import List, Dict, Any

class BingXConfig:
    """Configuration class for BingX trading bot."""
    
    # API Configuration
    API_KEY = os.getenv('BINGX_API_KEY', '')
    API_SECRET = os.getenv('BINGX_API_SECRET', '')
    USE_TESTNET = os.getenv('BINGX_USE_TESTNET', 'true').lower() == 'true'
    
    # Trading Configuration
    MAX_POSITIONS = int(os.getenv('BINGX_MAX_POSITIONS', '3'))
    RISK_PER_TRADE = float(os.getenv('BINGX_RISK_PER_TRADE', '0.02'))  # 2%
    LEVERAGE = int(os.getenv('BINGX_LEVERAGE', '10'))
    
    # Strategy Configuration
    TIMEFRAME = os.getenv('BINGX_TIMEFRAME', '15m')
    SYMBOLS = os.getenv('BINGX_SYMBOLS', 'BTC-USDT,ETH-USDT,BNB-USDT,ADA-USDT,DOT-USDT').split(',')
    
    # Risk Management
    STOP_LOSS_RATIO = float(os.getenv('BINGX_STOP_LOSS_RATIO', '0.02'))  # 2%
    TAKE_PROFIT_RATIO = float(os.getenv('BINGX_TAKE_PROFIT_RATIO', '0.04'))  # 4%
    MIN_PROFIT_RATIO = float(os.getenv('BINGX_MIN_PROFIT_RATIO', '1.5'))  # 1.5:1
    
    # Pattern Detection
    PATTERN_TOLERANCE = float(os.getenv('BINGX_PATTERN_TOLERANCE', '0.005'))  # 0.5%
    MIN_PATTERN_POINTS = int(os.getenv('BINGX_MIN_PATTERN_POINTS', '5'))
    
    # Monitoring
    CHECK_INTERVAL = int(os.getenv('BINGX_CHECK_INTERVAL', '60'))  # seconds
    
    # Telegram Notifications (if enabled)
    TELEGRAM_ENABLED = os.getenv('BINGX_TELEGRAM_ENABLED', 'false').lower() == 'true'
    TELEGRAM_BOT_TOKEN = os.getenv('BINGX_TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('BINGX_TELEGRAM_CHAT_ID', '')
    
    @classmethod
    def get_strategy_config(cls) -> Dict[str, Any]:
        """Get strategy configuration as dictionary."""
        return {
            'max_positions': cls.MAX_POSITIONS,
            'risk_per_trade': cls.RISK_PER_TRADE,
            'leverage': cls.LEVERAGE,
            'timeframe': cls.TIMEFRAME,
            'symbols': cls.SYMBOLS,
            'stop_loss_ratio': cls.STOP_LOSS_RATIO,
            'take_profit_ratio': cls.TAKE_PROFIT_RATIO,
            'min_profit_ratio': cls.MIN_PROFIT_RATIO,
            'pattern_tolerance': cls.PATTERN_TOLERANCE,
            'min_pattern_points': cls.MIN_PATTERN_POINTS,
            'check_interval': cls.CHECK_INTERVAL
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not cls.API_KEY:
            errors.append("BINGX_API_KEY is required")
        
        if not cls.API_SECRET:
            errors.append("BINGX_API_SECRET is required")
        
        if cls.LEVERAGE < 1 or cls.LEVERAGE > 125:
            errors.append("BINGX_LEVERAGE must be between 1 and 125")
        
        if cls.RISK_PER_TRADE <= 0 or cls.RISK_PER_TRADE > 1:
            errors.append("BINGX_RISK_PER_TRADE must be between 0 and 1")
        
        if cls.MAX_POSITIONS < 1:
            errors.append("BINGX_MAX_POSITIONS must be at least 1")
        
        if not cls.SYMBOLS:
            errors.append("BINGX_SYMBOLS cannot be empty")
        
        if cls.TELEGRAM_ENABLED and not cls.TELEGRAM_BOT_TOKEN:
            errors.append("BINGX_TELEGRAM_BOT_TOKEN is required when Telegram is enabled")
        
        if cls.TELEGRAM_ENABLED and not cls.TELEGRAM_CHAT_ID:
            errors.append("BINGX_TELEGRAM_CHAT_ID is required when Telegram is enabled")
        
        return errors
