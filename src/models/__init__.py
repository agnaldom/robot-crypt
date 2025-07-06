"""
SQLAlchemy models for Robot-Crypt.
"""

from .user import User
from .asset import Asset
from .technical_indicator import TechnicalIndicator
from .macro_indicator import MacroIndicator
from .bot_performance import BotPerformance
from .risk_management import RiskManagement
from .alert import Alert
from .trade import Trade
from .report import Report

# Portfolio-related models
from .portfolio_orm import Portfolio
from .portfolio_alert import PortfolioAlert
from .portfolio_asset import PortfolioAsset
from .portfolio_metric import PortfolioMetric
from .portfolio_position import PortfolioPosition
from .portfolio_projection import PortfolioProjection
from .portfolio_report import PortfolioReport
from .portfolio_snapshot import PortfolioSnapshot
from .portfolio_transaction import PortfolioTransaction

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
