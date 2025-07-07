"""
API routers for Robot-Crypt.
"""

from src.api.routers.auth import router as auth_router
from src.api.routers.users import router as users_router
from src.api.routers.assets import router as assets_router
from src.api.routers.indicators import router as indicators_router
from src.api.routers.trades import router as trades_router
from src.api.routers.alerts import router as alerts_router
from src.api.routers.reports import router as reports_router
from src.api.routers.portfolio import router as portfolio_router
# from src.market import router as market_router  # Temporarily disabled - missing dependencies
# from src.trading_session import router as trading_session_router  # Temporarily disabled - missing dependencies

__all__ = [
    "auth_router",
    "users_router",
    "assets_router",
    "indicators_router",
    "trades_router",
    "alerts_router",
    "reports_router",
    "portfolio_router",
    # "market_router",  # Temporarily disabled
    # "trading_session_router",  # Temporarily disabled
]
