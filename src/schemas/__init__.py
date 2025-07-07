"""
Pydantic schemas for Robot-Crypt API.
"""

from src.schemas.user import UserBase, UserCreate, UserUpdate, UserInDB, User
from src.schemas.asset import AssetBase, AssetCreate, AssetUpdate, Asset
from src.schemas.technical_indicator import TechnicalIndicatorBase, TechnicalIndicatorCreate, TechnicalIndicator
from src.schemas.macro_indicator import MacroIndicatorBase, MacroIndicatorCreate, MacroIndicator
from src.schemas.bot_performance import BotPerformanceBase, BotPerformanceCreate, BotPerformance
from src.schemas.risk_management import RiskManagementBase, RiskManagementCreate, RiskManagement
from src.schemas.alert import AlertBase, AlertCreate, AlertUpdate, Alert
from src.schemas.trade import TradeBase, TradeCreate, Trade
from src.schemas.report import ReportBase, ReportCreate, Report
from src.schemas.token import Token, TokenData

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
