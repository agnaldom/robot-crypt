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

# Security middlewares
from src.middleware.security_headers import (
    SecurityHeadersMiddleware, 
    RateLimitMiddleware, 
    SecurityMonitoringMiddleware
)

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
            import src.models  # This will import all models from __init__.py
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

# Add security middlewares (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityMonitoringMiddleware)

# Only apply rate limiting in production
if not settings.DEBUG:
    app.add_middleware(RateLimitMiddleware, calls=settings.RATE_LIMIT_PER_MINUTE, period=60)

# Add trusted host middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.herokuapp.com", "*.railway.app"]
    )

# Add CORS middleware with secure configuration
if settings.DEBUG:
    allowed_origins = ["*"]  # Apenas em desenvolvimento
    allowed_methods = ["*"]
    allowed_headers = ["*"]
else:
    allowed_origins = settings.ALLOWED_ORIGINS
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers = ["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
    max_age=600  # Cache preflight por 10 minutos
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
    trades_router, alerts_router, reports_router, portfolio_router
)
from src.api.routers.trading_session import router as trading_session_router
from src.api.routers.market import router as market_router
from src.api.websocket_endpoints import router as websocket_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(assets_router, prefix="/assets", tags=["Assets"])
app.include_router(indicators_router, prefix="/indicators", tags=["Indicators"])
app.include_router(trades_router, prefix="/trades", tags=["Trades"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(trading_session_router, prefix="/trading-sessions", tags=["Trading Sessions"])
app.include_router(market_router, prefix="/market", tags=["Market Data"])
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
    """Get public configuration (limited in production)."""
    # Em produção, retornar apenas informações públicas básicas
    if not settings.DEBUG:
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online"
        }
    
    # Em desenvolvimento, retornar mais informações
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
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
