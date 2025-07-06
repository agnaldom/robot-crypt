"""
API routers for Robot-Crypt.
"""

from .auth import router as auth_router
from .users import router as users_router
from .assets import router as assets_router
from .indicators import router as indicators_router
from .trades import router as trades_router
from .alerts import router as alerts_router
from .reports import router as reports_router
from .portfolio import router as portfolio_router
# from .market import router as market_router  # Temporarily disabled - missing dependencies
# from .trading_session import router as trading_session_router  # Temporarily disabled - missing dependencies

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
