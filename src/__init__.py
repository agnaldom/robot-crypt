#!/usr/bin/env python3
"""
Robot-Crypt Source Package

Estrutura modular do projeto Robot-Crypt para trading de criptomoedas.
"""

__version__ = "3.0.0"
__author__ = "Robot-Crypt Team"

# Principais módulos do projeto
from .core.config import Config
from .api.binance_api import BinanceAPI
from .strategies.strategy import ScalpingStrategy, SwingTradingStrategy
from .database.db_manager import DBManager
from .database.postgres_manager import PostgresManager
from .notifications.telegram_notifier import TelegramNotifier
from .trading.wallet_manager import WalletManager
from .risk_management.adaptive_risk_manager import AdaptiveRiskManager
from .analysis.technical_indicators import TechnicalIndicators
from .analysis.external_data_analyzer import ExternalDataAnalyzer

# Utilitários
from .utils.utils import (
    setup_logger, 
    save_state, 
    load_state, 
    filtrar_pares_por_liquidez,
    calculate_profit,
    calculate_fees
)

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
    
    # Utils
    "setup_logger",
    "save_state",
    "load_state", 
    "filtrar_pares_por_liquidez",
    "calculate_profit",
    "calculate_fees"
]
