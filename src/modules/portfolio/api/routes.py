from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

# Import from shared dependencies (assuming they're available in a common location)
from backend_new.core.dependencies import get_current_active_user, get_db
from backend_new.models.user import User

# Import models and schemas from the modular structure
from backend_new.modules.portfolio.models.portfolio_snapshot import PortfolioSnapshot
from backend_new.modules.portfolio.models.portfolio_transaction import PortfolioTransaction
from backend_new.modules.portfolio.models.portfolio_metric import PortfolioMetric
from backend_new.modules.portfolio.models.portfolio_alert import PortfolioAlert
from backend_new.modules.portfolio.models.portfolio_projection import PortfolioProjection
from backend_new.modules.portfolio.models.portfolio_report import PortfolioReport

from backend_new.modules.portfolio.schemas.portfolio import (
    PortfolioSnapshotCreate, PortfolioSnapshotUpdate, PortfolioSnapshotInDB, PortfolioSnapshotWithAssets,
    PortfolioTransactionCreate, PortfolioTransactionUpdate, PortfolioTransactionInDB,
    PortfolioMetricCreate, PortfolioMetricUpdate, PortfolioMetricInDB,
    PortfolioAlertCreate, PortfolioAlertUpdate, PortfolioAlertInDB,
    PortfolioProjectionCreate, PortfolioProjectionUpdate, PortfolioProjectionInDB,
    PortfolioReportCreate, PortfolioReportUpdate, PortfolioReportInDB
)

# Import service functions
from backend_new.modules.portfolio.services.portfolio_service import (
    get_portfolio_snapshot,
    create_portfolio_snapshot,
    update_portfolio_snapshot,
    delete_portfolio_snapshot,
    get_latest_portfolio_snapshot,
    get_portfolio_snapshots,
    
    get_portfolio_transaction,
    create_portfolio_transaction,
    update_portfolio_transaction,
    delete_portfolio_transaction,
    get_portfolio_transactions,
    
    get_portfolio_metric,
    create_portfolio_metric,
    update_portfolio_metric,
    delete_portfolio_metric,
    get_portfolio_metrics,
    
    get_portfolio_alert,
    create_portfolio_alert,
    update_portfolio_alert,
    delete_portfolio_alert,
    get_portfolio_alerts,
    
    get_portfolio_projection,
    create_portfolio_projection,
    update_portfolio_projection,
    delete_portfolio_projection,
    get_portfolio_projections,
    
    get_portfolio_report,
    create_portfolio_report,
    update_portfolio_report,
    delete_portfolio_report,
    get_portfolio_reports,
    
    get_portfolio_summary,
    get_portfolio_assets_distribution,
    get_portfolio_performance,
    get_portfolio_risk_assessment,
    generate_portfolio_projection
)

router = APIRouter()


# Portfolio Snapshots
@router.get("/snapshots", response_model=List[PortfolioSnapshotInDB])
def read_portfolio_snapshots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Any:
    """
    Retrieve portfolio snapshots.
    """
    snapshots = get_portfolio_snapshots(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return snapshots


@router.get("/snapshots/latest", response_model=PortfolioSnapshotWithAssets)
def read_latest_portfolio_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve the latest portfolio snapshot with assets.
    """
    snapshot = get_latest_portfolio_snapshot(db=db, user_id=current_user.id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio snapshot found"
        )
    return snapshot


@router.get("/snapshots/{snapshot_id}", response_model=PortfolioSnapshotWithAssets)
def read_portfolio_snapshot(
    snapshot_id: int = Path(..., title="The ID of the portfolio snapshot to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific portfolio snapshot by ID.
    """
    snapshot = get_portfolio_snapshot(db=db, snapshot_id=snapshot_id, user_id=current_user.id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio snapshot not found"
        )
    return snapshot


@router.post("/snapshots", response_model=PortfolioSnapshotWithAssets, status_code=status.HTTP_201_CREATED)
def create_new_portfolio_snapshot(
    snapshot_in: PortfolioSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new portfolio snapshot.
    """
    # Override user_id with authenticated user's ID
    snapshot_data = snapshot_in.model_dump()
    snapshot_data["user_id"] = current_user.id
    
    snapshot = create_portfolio_snapshot(db=db, snapshot_in=snapshot_data)
    return snapshot


@router.put("/snapshots/{snapshot_id}", response_model=PortfolioSnapshotWithAssets)
def update_existing_portfolio_snapshot(
    snapshot_in: PortfolioSnapshotUpdate,
    snapshot_id: int = Path(..., title="The ID of the portfolio snapshot to update"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update a portfolio snapshot.
    """
    snapshot = get_portfolio_snapshot(db=db, snapshot_id=snapshot_id, user_id=current_user.id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio snapshot not found"
        )
    
    snapshot = update_portfolio_snapshot(
        db=db, 
        snapshot_id=snapshot_id, 
        snapshot_in=snapshot_in.model_dump(exclude_unset=True)
    )
    return snapshot


@router.delete("/snapshots/{snapshot_id}", response_model=PortfolioSnapshotInDB)
def delete_existing_portfolio_snapshot(
    snapshot_id: int = Path(..., title="The ID of the portfolio snapshot to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete a portfolio snapshot.
    """
    snapshot = get_portfolio_snapshot(db=db, snapshot_id=snapshot_id, user_id=current_user.id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio snapshot not found"
        )
    
    snapshot = delete_portfolio_snapshot(db=db, snapshot_id=snapshot_id)
    return snapshot


# Portfolio Transactions
@router.get("/transactions", response_model=List[PortfolioTransactionInDB])
def read_portfolio_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    asset_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Any:
    """
    Retrieve portfolio transactions with filtering options.
    """
    transactions = get_portfolio_transactions(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        asset_id=asset_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    return transactions


@router.get("/transactions/{transaction_id}", response_model=PortfolioTransactionInDB)
def read_portfolio_transaction(
    transaction_id: int = Path(..., title="The ID of the portfolio transaction to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific portfolio transaction by ID.
    """
    transaction = get_portfolio_transaction(db=db, transaction_id=transaction_id, user_id=current_user.id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio transaction not found"
        )
    return transaction


@router.post("/transactions", response_model=PortfolioTransactionInDB, status_code=status.HTTP_201_CREATED)
def create_new_portfolio_transaction(
    transaction_in: PortfolioTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new portfolio transaction.
    """
    # Override user_id with authenticated user's ID
    transaction_data = transaction_in.model_dump()
    transaction_data["user_id"] = current_user.id
    
    transaction = create_portfolio_transaction(db=db, transaction_in=transaction_data)
    return transaction


@router.put("/transactions/{transaction_id}", response_model=PortfolioTransactionInDB)
def update_existing_portfolio_transaction(
    transaction_in: PortfolioTransactionUpdate,
    transaction_id: int = Path(..., title="The ID of the portfolio transaction to update"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update a portfolio transaction.
    """
    transaction = get_portfolio_transaction(db=db, transaction_id=transaction_id, user_id=current_user.id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio transaction not found"
        )
    
    transaction = update_portfolio_transaction(
        db=db, 
        transaction_id=transaction_id, 
        transaction_in=transaction_in.model_dump(exclude_unset=True)
    )
    return transaction


@router.delete("/transactions/{transaction_id}", response_model=PortfolioTransactionInDB)
def delete_existing_portfolio_transaction(
    transaction_id: int = Path(..., title="The ID of the portfolio transaction to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete a portfolio transaction.
    """
    transaction = get_portfolio_transaction(db=db, transaction_id=transaction_id, user_id=current_user.id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio transaction not found"
        )
    
    transaction = delete_portfolio_transaction(db=db, transaction_id=transaction_id)
    return transaction


# Portfolio Metrics
@router.get("/metrics", response_model=List[PortfolioMetricInDB])
def read_portfolio_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    period_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Any:
    """
    Retrieve portfolio metrics with filtering options.
    """
    metrics = get_portfolio_metrics(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )
    return metrics


@router.get("/metrics/{metric_id}", response_model=PortfolioMetricInDB)
def read_portfolio_metric(
    metric_id: int = Path(..., title="The ID of the portfolio metric to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific portfolio metric by ID.
    """
    metric = get_portfolio_metric(db=db, metric_id=metric_id, user_id=current_user.id)
    if metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio metric not found"
        )
    return metric


@router.post("/metrics", response_model=PortfolioMetricInDB, status_code=status.HTTP_201_CREATED)
def create_new_portfolio_metric(
    metric_in: PortfolioMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new portfolio metric.
    """
    # Override user_id with authenticated user's ID
    metric_data = metric_in.model_dump()
    metric_data["user_id"] = current_user.id
    
    metric = create_portfolio_metric(db=db, metric_in=metric_data)
    return metric


# Portfolio Summary and Analysis Endpoints
@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, description="Number of days for historical data")
) -> Any:
    """
    Get portfolio summary including current value, performance, and asset allocation.
    """
    return get_portfolio_summary(db=db, user_id=current_user.id, days=days)


@router.get("/distribution")
def get_assets_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get detailed breakdown of portfolio assets distribution.
    """
    return get_portfolio_assets_distribution(db=db, user_id=current_user.id)


@router.get("/performance")
def get_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    period: str = Query("month", description="Time period: week, month, quarter, year, all"),
    compare_with: Optional[str] = Query(None, description="Asset to compare with (e.g., BTC, ETH)")
) -> Any:
    """
    Get detailed portfolio performance metrics and history.
    """
    return get_portfolio_performance(
        db=db, 
        user_id=current_user.id, 
        period=period, 
        compare_with=compare_with
    )


@router.get("/risk")
def get_risk_assessment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get portfolio risk metrics including VaR, volatility, and concentration risk.
    """
    return get_portfolio_risk_assessment(db=db, user_id=current_user.id)


@router.post("/projections/simulate")
def simulate_projection(
    projection_in: PortfolioProjectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate portfolio projections based on different scenarios.
    """
    # Override user_id with authenticated user's ID
    projection_data = projection_in.model_dump()
    projection_data["user_id"] = current_user.id
    
    return generate_portfolio_projection(db=db, projection_in=projection_data)
