"""
Portfolio module for managing portfolio snapshots, transactions, metrics, projections and reports.
"""
from fastapi import APIRouter

from backend_new.modules.portfolio.api.routes import router as portfolio_router

# Create a router to be included in the main app
router = APIRouter()
router.include_router(portfolio_router)

__all__ = ["router"]
