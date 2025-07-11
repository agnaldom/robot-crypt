"""
Portfolio router for Robot-Crypt API.
"""

from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_user
from src.database.database import get_database
from src.schemas.portfolio import (
    PortfolioPositionCreate, PortfolioPositionUpdate, PortfolioPositionInDB,
    PortfolioSummary, PortfolioPerformance,
    PortfolioSnapshotWithAssets, PortfolioSnapshotCreate, PortfolioSnapshotUpdate,
    PortfolioTransactionInDB, PortfolioTransactionCreate, PortfolioTransactionUpdate
)
from src.schemas.user import User
from src.services.portfolio_position_service import PortfolioPositionService
from src.services.portfolio_service import PortfolioService

router = APIRouter()


# ==================== Portfolio Snapshots ====================

@router.get("/snapshots", response_model=List[PortfolioSnapshotWithAssets])
async def read_portfolio_snapshots(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve portfolio snapshots with optional date filtering.
    """
    portfolio_service = PortfolioService(db)
    
    # Non-superuser can only see their own snapshots
    user_id = None if current_user.is_superuser else current_user.id
    
    snapshots = await portfolio_service.get_portfolio_snapshots(
        user_id=user_id or current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return snapshots


@router.post("/snapshots", response_model=PortfolioSnapshotWithAssets)
async def create_portfolio_snapshot(
    snapshot_in: PortfolioSnapshotCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new portfolio snapshot.
    """
    portfolio_service = PortfolioService(db)
    
    # Set user_id to current user if not superuser
    if not current_user.is_superuser:
        snapshot_in.user_id = current_user.id
    
    snapshot = await portfolio_service.create_portfolio_snapshot(snapshot_in)
    return snapshot


@router.get("/snapshots/latest", response_model=PortfolioSnapshotWithAssets)
async def get_latest_portfolio_snapshot(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get the latest portfolio snapshot for current user.
    """
    portfolio_service = PortfolioService(db)
    snapshot = await portfolio_service.get_latest_portfolio_snapshot(current_user.id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No portfolio snapshots found")
    
    return snapshot


@router.get("/snapshots/{snapshot_id}", response_model=PortfolioSnapshotWithAssets)
async def read_portfolio_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get portfolio snapshot by ID.
    """
    portfolio_service = PortfolioService(db)
    snapshot = await portfolio_service.get_portfolio_snapshot(snapshot_id, current_user.id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Portfolio snapshot not found")
    
    return snapshot


@router.put("/snapshots/{snapshot_id}", response_model=PortfolioSnapshotWithAssets)
async def update_portfolio_snapshot(
    snapshot_id: int,
    snapshot_in: PortfolioSnapshotUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a portfolio snapshot.
    """
    portfolio_service = PortfolioService(db)
    snapshot = await portfolio_service.update_portfolio_snapshot(
        snapshot_id, snapshot_in, current_user.id
    )
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Portfolio snapshot not found")
    
    return snapshot


@router.delete("/snapshots/{snapshot_id}", response_model=PortfolioSnapshotWithAssets)
async def delete_portfolio_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a portfolio snapshot.
    """
    portfolio_service = PortfolioService(db)
    snapshot = await portfolio_service.delete_portfolio_snapshot(snapshot_id, current_user.id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Portfolio snapshot not found")
    
    return snapshot


# ==================== Portfolio Transactions ====================

@router.get("/transactions", response_model=List[PortfolioTransactionInDB])
async def read_portfolio_transactions(
    skip: int = 0,
    limit: int = 100,
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve portfolio transactions with optional filtering.
    """
    portfolio_service = PortfolioService(db)
    
    # Non-superuser can only see their own transactions
    user_id = None if current_user.is_superuser else current_user.id
    
    transactions = await portfolio_service.get_portfolio_transactions(
        user_id=user_id or current_user.id,
        skip=skip,
        limit=limit,
        asset_id=asset_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    return transactions


@router.post("/transactions", response_model=PortfolioTransactionInDB)
async def create_portfolio_transaction(
    transaction_in: PortfolioTransactionCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new portfolio transaction.
    """
    portfolio_service = PortfolioService(db)
    
    # Set user_id to current user if not superuser
    if not current_user.is_superuser:
        transaction_in.user_id = current_user.id
    
    transaction = await portfolio_service.create_portfolio_transaction(transaction_in)
    return transaction


@router.get("/transactions/{transaction_id}", response_model=PortfolioTransactionInDB)
async def read_portfolio_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get portfolio transaction by ID.
    """
    portfolio_service = PortfolioService(db)
    transaction = await portfolio_service.get_portfolio_transaction(transaction_id, current_user.id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Portfolio transaction not found")
    
    return transaction


@router.put("/transactions/{transaction_id}", response_model=PortfolioTransactionInDB)
async def update_portfolio_transaction(
    transaction_id: int,
    transaction_in: PortfolioTransactionUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a portfolio transaction.
    """
    portfolio_service = PortfolioService(db)
    transaction = await portfolio_service.update_portfolio_transaction(
        transaction_id, transaction_in, current_user.id
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Portfolio transaction not found")
    
    return transaction


@router.delete("/transactions/{transaction_id}", response_model=PortfolioTransactionInDB)
async def delete_portfolio_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a portfolio transaction.
    """
    portfolio_service = PortfolioService(db)
    transaction = await portfolio_service.delete_portfolio_transaction(transaction_id, current_user.id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Portfolio transaction not found")
    
    return transaction


# ==================== Portfolio Analysis ====================

@router.get("/summary")
async def get_portfolio_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days for analysis"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get portfolio summary with key metrics and recent activity.
    """
    portfolio_service = PortfolioService(db)
    summary = await portfolio_service.get_portfolio_summary(current_user.id, days)
    return summary


@router.get("/performance")
async def get_portfolio_performance(
    period: str = Query("month", description="Performance period (week, month, quarter, year, all)"),
    compare_with: Optional[str] = Query(None, description="Asset symbol to compare with (e.g., BTC, ETH)"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get detailed portfolio performance metrics and historical data.
    """
    portfolio_service = PortfolioService(db)
    performance = await portfolio_service.get_portfolio_performance(
        current_user.id, period, compare_with
    )
    return performance


@router.get("/risk-assessment")
async def get_portfolio_risk_assessment(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get comprehensive portfolio risk assessment including VaR, concentration risk, etc.
    """
    portfolio_service = PortfolioService(db)
    risk_assessment = await portfolio_service.get_portfolio_risk_assessment(current_user.id)
    return risk_assessment


@router.get("/assets-distribution")
async def get_portfolio_assets_distribution(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get detailed breakdown of portfolio assets distribution.
    """
    portfolio_service = PortfolioService(db)
    distribution = await portfolio_service.get_assets_distribution(current_user.id)
    return distribution


# ==================== Portfolio Analytics ====================

@router.get("/analytics/correlation")
async def get_portfolio_correlation_analysis(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get correlation analysis between portfolio assets.
    """
    # This would typically calculate correlation matrix between assets
    # For now, return a mock response
    return {
        "status": "success",
        "data": {
            "correlation_matrix": {
                "BTC": {"BTC": 1.0, "ETH": 0.85, "ADA": 0.72},
                "ETH": {"BTC": 0.85, "ETH": 1.0, "ADA": 0.78},
                "ADA": {"BTC": 0.72, "ETH": 0.78, "ADA": 1.0}
            },
            "diversification_score": 75.5,
            "analysis_date": datetime.utcnow().isoformat()
        }
    }


@router.get("/analytics/stress-test")
async def get_portfolio_stress_test(
    scenario: str = Query("market_crash", description="Stress test scenario"),
    severity: float = Query(0.3, ge=0.1, le=1.0, description="Scenario severity (0.1-1.0)"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Perform stress testing on portfolio under various market scenarios.
    """
    portfolio_service = PortfolioService(db)
    
    # Get current portfolio
    summary = await portfolio_service.get_portfolio_summary(current_user.id)
    
    if summary["status"] != "success":
        raise HTTPException(status_code=404, detail="No portfolio data available for stress testing")
    
    current_value = summary["data"]["portfolio_value"]
    
    # Simple stress test calculations
    if scenario == "market_crash":
        projected_loss = current_value * severity * 0.5  # Crypto typically loses 30-90% in crashes
    elif scenario == "bear_market":
        projected_loss = current_value * severity * 0.3  # Extended downtrend
    elif scenario == "regulatory_crackdown":
        projected_loss = current_value * severity * 0.4  # Regulatory impact
    else:
        projected_loss = current_value * severity * 0.2  # Generic scenario
    
    stressed_value = current_value - projected_loss
    
    return {
        "status": "success",
        "data": {
            "scenario": scenario,
            "severity": severity,
            "current_portfolio_value": current_value,
            "projected_loss": projected_loss,
            "stressed_portfolio_value": stressed_value,
            "loss_percentage": (projected_loss / current_value) * 100,
            "time_to_recovery_estimate_days": int(projected_loss / (current_value * 0.001)),  # Rough estimate
            "risk_level": "high" if (projected_loss / current_value) > 0.3 else "medium" if (projected_loss / current_value) > 0.15 else "low",
            "recommendations": [
                "Consider diversifying into less correlated assets",
                "Implement stop-loss orders",
                "Review position sizes",
                "Consider hedging strategies"
            ] if (projected_loss / current_value) > 0.2 else [
                "Portfolio shows good resilience",
                "Continue monitoring market conditions"
            ]
        }
    }


@router.get("/analytics/rebalancing-suggestions")
async def get_portfolio_rebalancing_suggestions(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get portfolio rebalancing suggestions based on target allocation.
    """
    portfolio_service = PortfolioService(db)
    
    # Get current asset distribution
    distribution = await portfolio_service.get_assets_distribution(current_user.id)
    
    if distribution["status"] != "success":
        raise HTTPException(status_code=404, detail="No portfolio data available for rebalancing analysis")
    
    current_assets = distribution["data"]["assets"]
    total_value = distribution["data"]["total_value"]
    
    # Default target allocation
    target_allocation = {
        "BTC": 40,
        "ETH": 25,
        "ADA": 15,
        "SOL": 10,
        "others": 10
    }
    
    rebalancing_actions = []
    
    for asset in current_assets:
        symbol = asset["symbol"]
        current_percentage = asset["allocation_percentage"]
        current_value = asset["current_value"]
        
        target_percentage = target_allocation.get(symbol, target_allocation.get("others", 5))
        target_value = total_value * (target_percentage / 100)
        
        difference_value = target_value - current_value
        difference_percentage = target_percentage - current_percentage
        
        if abs(difference_percentage) > 2:  # Only suggest rebalancing if difference > 2%
            action = "buy" if difference_value > 0 else "sell"
            rebalancing_actions.append({
                "symbol": symbol,
                "action": action,
                "current_percentage": current_percentage,
                "target_percentage": target_percentage,
                "current_value": current_value,
                "target_value": target_value,
                "difference_value": abs(difference_value),
                "difference_percentage": abs(difference_percentage),
                "priority": "high" if abs(difference_percentage) > 10 else "medium" if abs(difference_percentage) > 5 else "low"
            })
    
    return {
        "status": "success",
        "data": {
            "current_total_value": total_value,
            "target_allocation": target_allocation,
            "rebalancing_needed": len(rebalancing_actions) > 0,
            "actions": rebalancing_actions,
            "estimated_cost": sum(action["difference_value"] * 0.001 for action in rebalancing_actions),  # Assume 0.1% trading fee
            "analysis_date": datetime.utcnow().isoformat()
        }
    }
