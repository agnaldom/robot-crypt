"""
Pydantic schemas for Robot-Crypt API.
"""

from .user import UserBase, UserCreate, UserUpdate, UserInDB, User
from .asset import AssetBase, AssetCreate, AssetUpdate, Asset
from .technical_indicator import TechnicalIndicatorBase, TechnicalIndicatorCreate, TechnicalIndicator
from .macro_indicator import MacroIndicatorBase, MacroIndicatorCreate, MacroIndicator
from .bot_performance import BotPerformanceBase, BotPerformanceCreate, BotPerformance
from .risk_management import RiskManagementBase, RiskManagementCreate, RiskManagement
from .alert import AlertBase, AlertCreate, AlertUpdate, Alert
from .trade import TradeBase, TradeCreate, Trade
from .report import ReportBase, ReportCreate, Report
from .token import Token, TokenData

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate", 
    "UserUpdate",
    "UserInDB",
    "User",
    # Asset schemas
    "AssetBase",
    "AssetCreate",
    "AssetUpdate", 
    "Asset",
    # Technical indicator schemas
    "TechnicalIndicatorBase",
    "TechnicalIndicatorCreate",
    "TechnicalIndicator",
    # Macro indicator schemas
    "MacroIndicatorBase",
    "MacroIndicatorCreate",
    "MacroIndicator",
    # Bot performance schemas
    "BotPerformanceBase",
    "BotPerformanceCreate",
    "BotPerformance",
    # Risk management schemas
    "RiskManagementBase",
    "RiskManagementCreate",
    "RiskManagement",
    # Alert schemas
    "AlertBase",
    "AlertCreate",
    "AlertUpdate",
    "Alert",
    # Trade schemas
    "TradeBase",
    "TradeCreate",
    "Trade",
    # Report schemas
    "ReportBase",
    "ReportCreate",
    "Report",
    # Token schemas
    "Token",
    "TokenData",
]
