"""
Main FastAPI application entry point for Robot-Crypt backend.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.database.database import Base, get_database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    logger.info("Starting Robot-Crypt API...")
    
    # Initialize database tables
    try:
        from src.database.database import async_engine
        async with async_engine.begin() as conn:
            # Import all models to ensure they are registered
            from src.models import (
                user, asset, technical_indicator, macro_indicator,
                bot_performance, risk_management, alert, trade, report
            )
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Robot-Crypt API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Cryptocurrency trading bot API with advanced analytics and risk management",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add security middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.herokuapp.com", "*.railway.app"]
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
from src.api.routers import (
    auth_router, users_router, assets_router, indicators_router,
    trades_router, alerts_router, reports_router, trading_session_router
)
from src.api.websocket_endpoints import router as websocket_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(assets_router, prefix="/assets", tags=["Assets"])
app.include_router(indicators_router, prefix="/indicators", tags=["Indicators"])
app.include_router(trades_router, prefix="/trades", tags=["Trades"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(trading_session_router, prefix="/trading-sessions", tags=["Trading Sessions"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "robot-crypt-api",
        "version": settings.APP_VERSION
    }


@app.get("/config")
async def get_config():
    """Get public configuration."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "trading_pairs": settings.TRADING_PAIRS,
        "simulation_mode": settings.SIMULATION_MODE,
        "notifications_enabled": settings.notifications_enabled
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
