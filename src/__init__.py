#!/usr/bin/env python3
"""
Robot-Crypt Source Package

Estrutura modular do projeto Robot-Crypt para trading de criptomoedas.
"""

__version__ = "3.0.0"
__author__ = "Robot-Crypt Team"

# Principais módulos do projeto
try:
    from src.core.config import Config
except ImportError:
    Config = None

# API modules
try:
    from src.api.binance_api import BinanceAPI
except ImportError:
    BinanceAPI = None

# Strategy modules
try:
    from src.strategies.strategy import ScalpingStrategy, SwingTradingStrategy
except ImportError:
    ScalpingStrategy = None
    SwingTradingStrategy = None

# Database modules
try:
    from src.database.db_manager import DBManager
except ImportError:
    DBManager = None

try:
    from src.database.postgres_manager import PostgresManager
except ImportError:
    PostgresManager = None

# Notification modules
try:
    from src.notifications.telegram_notifier import TelegramNotifier
except ImportError:
    TelegramNotifier = None

# Trading modules
try:
    from src.trading.wallet_manager import WalletManager
except ImportError:
    WalletManager = None

# Risk management modules
try:
    from src.risk_management.adaptive_risk_manager import AdaptiveRiskManager
except ImportError:
    AdaptiveRiskManager = None

# Analysis modules
try:
    from src.analysis.technical_indicators import TechnicalIndicators
except ImportError:
    TechnicalIndicators = None

try:
    from src.analysis.external_data_analyzer import ExternalDataAnalyzer
except ImportError:
    ExternalDataAnalyzer = None

# Utilidades
try:
    from src.utils.utils import (
        setup_logger, 
        save_state, 
        load_state, 
        filtrar_pares_por_liquidez,
        calculate_profit,
        calculate_fees
    )
except ImportError:
    setup_logger = None
    save_state = None
    load_state = None
    filtrar_pares_por_liquidez = None
    calculate_profit = None
    calculate_fees = None

__all__ = [
    # Core
    "Config",
    
    # API
    "BinanceAPI",
    
    # Strategies
    "ScalpingStrategy",
    "SwingTradingStrategy", 
    
    # Database
    "DBManager", 
    "PostgresManager",
    
    # Notifications
    "TelegramNotifier",
    
    # Trading
    "WalletManager",
    
    # Risk Management
    "AdaptiveRiskManager",
    
    # Analysis
    "TechnicalIndicators",
    "ExternalDataAnalyzer",
    
    # Utilities
    "setup_logger",
    "save_state",
    "load_state", 
    "filtrar_pares_por_liquidez",
    "calculate_profit",
    "calculate_fees"
]
