"""
SQLAlchemy models for Robot-Crypt.
"""

from src.models.user import User
from src.models.asset import Asset
from src.models.technical_indicator import TechnicalIndicator
from src.models.macro_indicator import MacroIndicator
from src.models.bot_performance import BotPerformance
from src.models.risk_management import RiskManagement
from src.models.alert import Alert
from src.models.trade import Trade
from src.models.report import Report
from src.models.trading_session import TradingSession, TradingSessionLog, OpenOrder
from src.models.price_history import PriceHistory
from src.models.market_analysis import MarketAnalysis
from src.models.trading_signals import TradingSignal

# Portfolio-related models
from src.models.portfolio_orm import Portfolio
from src.models.portfolio_alert import PortfolioAlert
from src.models.portfolio_asset import PortfolioAsset
from src.models.portfolio_metric import PortfolioMetric
from src.models.portfolio_position import PortfolioPosition
from src.models.portfolio_projection import PortfolioProjection
from src.models.portfolio_report import PortfolioReport
from src.models.portfolio_snapshot import PortfolioSnapshot
from src.models.portfolio_transaction import PortfolioTransaction

__all__ = [
    "User",
    "Asset",
    "TechnicalIndicator",
    "MacroIndicator",
    "BotPerformance",
    "RiskManagement",
    "Alert",
    "Trade",
    "Report",
    "TradingSession",
    "TradingSessionLog",
    "OpenOrder",
    "PriceHistory",
    "MarketAnalysis",
    "TradingSignal",
    # Portfolio models
    "Portfolio",
    "PortfolioAlert",
    "PortfolioAsset",
    "PortfolioMetric",
    "PortfolioPosition",
    "PortfolioProjection",
    "PortfolioReport",
    "PortfolioSnapshot",
    "PortfolioTransaction",
]
