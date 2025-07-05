from typing import List, Dict, Optional, Any, Tuple
import datetime
import numpy as np
from sqlalchemy.orm import Session

from backend_new.core.db.database import get_db
from backend_new.modules.portfolio.models.portfolio_snapshot import PortfolioSnapshot
from backend_new.modules.portfolio.models.portfolio_asset import PortfolioAsset
from backend_new.modules.portfolio.models.portfolio_transaction import PortfolioTransaction
from backend_new.modules.portfolio.models.portfolio_metric import PortfolioMetric
from backend_new.modules.portfolio.models.portfolio_alert import PortfolioAlert
from backend_new.modules.portfolio.models.portfolio_projection import PortfolioProjection
from backend_new.modules.portfolio.models.portfolio_report import PortfolioReport
from backend_new.modules.portfolio.schemas import portfolio as schemas


# Snapshot Services
def create_portfolio_snapshot(db: Session, user_id: int, snapshot_data: schemas.PortfolioSnapshotCreate) -> PortfolioSnapshot:
    """
    Create a new portfolio snapshot with its associated assets
    """
    # Create the snapshot
    db_snapshot = PortfolioSnapshot(
        user_id=user_id,
        total_invested_value=snapshot_data.total_invested_value,
        current_market_value=snapshot_data.current_market_value,
        total_profit_loss=snapshot_data.total_profit_loss,
        profit_loss_percentage=snapshot_data.profit_loss_percentage,
        risk_level=snapshot_data.risk_level,
        value_at_risk=snapshot_data.value_at_risk,
        max_drawdown=snapshot_data.max_drawdown,
        volatility=snapshot_data.volatility,
        sharpe_ratio=snapshot_data.sharpe_ratio,
        btc_comparison=snapshot_data.btc_comparison,
        eth_comparison=snapshot_data.eth_comparison,
        metrics=snapshot_data.metrics or {}
    )
    db.add(db_snapshot)
    db.flush()  # Flush to get the snapshot ID
    
    # Create the associated assets
    for asset_data in snapshot_data.assets:
        db_asset = PortfolioAsset(
            snapshot_id=db_snapshot.id,
            asset_id=asset_data.asset_id,
            symbol=asset_data.symbol,
            quantity=asset_data.quantity,
            avg_buy_price=asset_data.avg_buy_price,
            current_price=asset_data.current_price,
            invested_value=asset_data.invested_value,
            current_value=asset_data.current_value,
            profit_loss=asset_data.profit_loss,
            profit_loss_percentage=asset_data.profit_loss_percentage,
            allocation_percentage=asset_data.allocation_percentage,
            is_active=asset_data.is_active
        )
        db.add(db_asset)
    
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def get_portfolio_snapshot(db: Session, snapshot_id: int, user_id: int) -> Optional[PortfolioSnapshot]:
    """
    Get a portfolio snapshot by ID for a specific user
    """
    return db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.id == snapshot_id,
        PortfolioSnapshot.user_id == user_id
    ).first()


def get_latest_portfolio_snapshot(db: Session, user_id: int) -> Optional[PortfolioSnapshot]:
    """
    Get the most recent portfolio snapshot for a user
    """
    return db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id
    ).order_by(PortfolioSnapshot.created_at.desc()).first()


def get_portfolio_snapshots(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None
) -> List[PortfolioSnapshot]:
    """
    Get all portfolio snapshots for a user with optional date filtering
    """
    query = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id
    )
    
    if start_date:
        query = query.filter(PortfolioSnapshot.created_at >= start_date)
    
    if end_date:
        query = query.filter(PortfolioSnapshot.created_at <= end_date)
    
    return query.order_by(PortfolioSnapshot.created_at.desc()).offset(skip).limit(limit).all()


def update_portfolio_snapshot(
    db: Session, 
    snapshot_id: int, 
    user_id: int, 
    snapshot_data: schemas.PortfolioSnapshotUpdate
) -> Optional[PortfolioSnapshot]:
    """
    Update an existing portfolio snapshot
    """
    db_snapshot = get_portfolio_snapshot(db, snapshot_id, user_id)
    if not db_snapshot:
        return None
    
    # Update snapshot fields
    update_data = snapshot_data.dict(exclude_unset=True)
    
    # Handle assets separately
    assets_data = update_data.pop("assets", None)
    
    # Update snapshot attributes
    for key, value in update_data.items():
        setattr(db_snapshot, key, value)
    
    # Update assets if provided
    if assets_data:
        # Remove existing assets
        db.query(PortfolioAsset).filter(
            PortfolioAsset.snapshot_id == snapshot_id
        ).delete()
        
        # Add new assets
        for asset_data in assets_data:
            db_asset = PortfolioAsset(
                snapshot_id=db_snapshot.id,
                **asset_data.dict()
            )
            db.add(db_asset)
    
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def delete_portfolio_snapshot(db: Session, snapshot_id: int, user_id: int) -> bool:
    """
    Delete a portfolio snapshot by ID
    """
    db_snapshot = get_portfolio_snapshot(db, snapshot_id, user_id)
    if not db_snapshot:
        return False
    
    db.delete(db_snapshot)
    db.commit()
    return True


# Transaction Services
def create_portfolio_transaction(
    db: Session, 
    user_id: int, 
    transaction_data: schemas.PortfolioTransactionCreate
) -> PortfolioTransaction:
    """
    Create a new portfolio transaction
    """
    db_transaction = PortfolioTransaction(
        user_id=user_id,
        **transaction_data.dict()
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_portfolio_transaction(
    db: Session, 
    transaction_id: int, 
    user_id: int
) -> Optional[PortfolioTransaction]:
    """
    Get a portfolio transaction by ID
    """
    return db.query(PortfolioTransaction).filter(
        PortfolioTransaction.id == transaction_id,
        PortfolioTransaction.user_id == user_id
    ).first()


def get_portfolio_transactions(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    asset_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None
) -> List[PortfolioTransaction]:
    """
    Get all portfolio transactions for a user with optional filtering
    """
    query = db.query(PortfolioTransaction).filter(
        PortfolioTransaction.user_id == user_id
    )
    
    if asset_id:
        query = query.filter(PortfolioTransaction.asset_id == asset_id)
    
    if transaction_type:
        query = query.filter(PortfolioTransaction.transaction_type == transaction_type)
    
    if start_date:
        query = query.filter(PortfolioTransaction.executed_at >= start_date)
    
    if end_date:
        query = query.filter(PortfolioTransaction.executed_at <= end_date)
    
    return query.order_by(PortfolioTransaction.executed_at.desc()).offset(skip).limit(limit).all()


def update_portfolio_transaction(
    db: Session, 
    transaction_id: int, 
    user_id: int, 
    transaction_data: schemas.PortfolioTransactionUpdate
) -> Optional[PortfolioTransaction]:
    """
    Update a portfolio transaction
    """
    db_transaction = get_portfolio_transaction(db, transaction_id, user_id)
    if not db_transaction:
        return None
    
    update_data = transaction_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_portfolio_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    """
    Delete a portfolio transaction
    """
    db_transaction = get_portfolio_transaction(db, transaction_id, user_id)
    if not db_transaction:
        return False
    
    db.delete(db_transaction)
    db.commit()
    return True


# Portfolio Metrics Services
def create_portfolio_metric(
    db: Session, 
    user_id: int, 
    metric_data: schemas.PortfolioMetricCreate
) -> PortfolioMetric:
    """
    Create a new portfolio metric
    """
    db_metric = PortfolioMetric(
        user_id=user_id,
        **metric_data.dict()
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def get_portfolio_metric(db: Session, metric_id: int, user_id: int) -> Optional[PortfolioMetric]:
    """
    Get a portfolio metric by ID
    """
    return db.query(PortfolioMetric).filter(
        PortfolioMetric.id == metric_id,
        PortfolioMetric.user_id == user_id
    ).first()


def get_portfolio_metrics(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    period_type: Optional[str] = None,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None
) -> List[PortfolioMetric]:
    """
    Get portfolio metrics for a user with optional filtering
    """
    query = db.query(PortfolioMetric).filter(
        PortfolioMetric.user_id == user_id
    )
    
    if period_type:
        query = query.filter(PortfolioMetric.period_type == period_type)
    
    if start_date:
        query = query.filter(PortfolioMetric.period_end >= start_date)
    
    if end_date:
        query = query.filter(PortfolioMetric.period_start <= end_date)
    
    return query.order_by(PortfolioMetric.period_end.desc()).offset(skip).limit(limit).all()


# Portfolio Analysis Functions
def calculate_portfolio_summary(
    db: Session, 
    user_id: int,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None
) -> Dict[str, Any]:
    """
    Calculate a summary of the user's portfolio
    """
    # Get the latest snapshot for current data
    latest_snapshot = get_latest_portfolio_snapshot(db, user_id)
    if not latest_snapshot:
        return {
            "total_invested": 0.0,
            "current_value": 0.0,
            "profit_loss": 0.0,
            "profit_loss_percentage": 0.0,
            "assets_count": 0,
            "risk_level": "unknown",
            "last_updated": None
        }
    
    # Get asset distribution
    assets = latest_snapshot.assets
    asset_distribution = [
        {
            "symbol": asset.symbol,
            "allocation": asset.allocation_percentage,
            "current_value": asset.current_value,
            "profit_loss": asset.profit_loss,
            "profit_loss_percentage": asset.profit_loss_percentage
        }
        for asset in assets
    ]
    
    # Get historical performance
    query = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id
    )
    
    if start_date:
        query = query.filter(PortfolioSnapshot.created_at >= start_date)
    
    if end_date:
        query = query.filter(PortfolioSnapshot.created_at <= end_date)
    
    historical_snapshots = query.order_by(PortfolioSnapshot.created_at.asc()).all()
    
    historical_values = [
        {
            "date": snapshot.created_at,
            "value": snapshot.current_market_value,
            "profit_loss": snapshot.total_profit_loss,
            "profit_loss_percentage": snapshot.profit_loss_percentage
        }
        for snapshot in historical_snapshots
    ]
    
    return {
        "total_invested": latest_snapshot.total_invested_value,
        "current_value": latest_snapshot.current_market_value,
        "profit_loss": latest_snapshot.total_profit_loss,
        "profit_loss_percentage": latest_snapshot.profit_loss_percentage,
        "assets_count": len(assets),
        "risk_level": latest_snapshot.risk_level,
        "volatility": latest_snapshot.volatility,
        "sharpe_ratio": latest_snapshot.sharpe_ratio,
        "max_drawdown": latest_snapshot.max_drawdown,
        "value_at_risk": latest_snapshot.value_at_risk,
        "btc_comparison": latest_snapshot.btc_comparison,
        "eth_comparison": latest_snapshot.eth_comparison,
        "asset_distribution": asset_distribution,
        "historical_performance": historical_values,
        "last_updated": latest_snapshot.created_at
    }


def calculate_portfolio_risk_assessment(
    db: Session, 
    user_id: int
) -> Dict[str, Any]:
    """
    Calculate portfolio risk assessment metrics
    """
    # Get the latest snapshot and historical data
    latest_snapshot = get_latest_portfolio_snapshot(db, user_id)
    if not latest_snapshot:
        return {
            "risk_level": "unknown",
            "risk_score": 0,
            "diversification_score": 0,
            "volatility": 0,
            "value_at_risk": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "asset_correlations": []
        }
    
    # Get historical snapshots for the last 90 days
    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=90)
    
    historical_snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id,
        PortfolioSnapshot.created_at >= start_date,
        PortfolioSnapshot.created_at <= end_date
    ).order_by(PortfolioSnapshot.created_at.asc()).all()
    
    # Calculate diversification score based on current asset distribution
    assets = latest_snapshot.assets
    allocations = [asset.allocation_percentage for asset in assets]
    
    # Higher when more evenly distributed (1/sum of squared allocations)
    diversification_score = 0
    if allocations:
        diversification_score = min(1.0, 1.0 / sum(a**2 for a in allocations))
    
    # Calculate correlation between assets (placeholder - in a real system this would use price data)
    # For this example, we'll just return a placeholder
    asset_correlations = []
    
    # Return the comprehensive risk assessment
    return {
        "risk_level": latest_snapshot.risk_level or "medium",
        "risk_score": latest_snapshot.value_at_risk or 0,
        "diversification_score": diversification_score,
        "volatility": latest_snapshot.volatility or 0,
        "value_at_risk": latest_snapshot.value_at_risk or 0,
        "max_drawdown": latest_snapshot.max_drawdown or 0,
        "sharpe_ratio": latest_snapshot.sharpe_ratio or 0,
        "asset_correlations": asset_correlations,
        "historical_snapshots_count": len(historical_snapshots)
    }


def generate_portfolio_projection(
    db: Session,
    user_id: int,
    projection_data: schemas.PortfolioProjectionCreate
) -> PortfolioProjection:
    """
    Generate a new portfolio projection
    """
    # Create the projection record
    db_projection = PortfolioProjection(
        user_id=user_id,
        **projection_data.dict(exclude={"projection_data"})
    )
    
    # Generate time series projection data
    initial_value = projection_data.initial_value
    expected_return_rate = projection_data.expected_return_rate
    volatility = projection_data.volatility
    time_horizon = projection_data.time_horizon
    time_unit = projection_data.time_unit
    
    # Convert time unit to days for calculation
    days_multiplier = {
        "days": 1,
        "months": 30,
        "years": 365
    }
    total_days = time_horizon * days_multiplier.get(time_unit, 1)
    
    # Calculate daily return rate and volatility
    daily_return = (1 + expected_return_rate) ** (1/365) - 1
    daily_volatility = volatility / (365 ** 0.5)
    
    # Generate projection paths
    np.random.seed(42)  # For reproducibility
    
    # Generate main projection (expected path)
    expected_path = []
    current_value = initial_value
    
    for day in range(total_days + 1):
        expected_path.append({
            "day": day,
            "value": current_value
        })
        current_value *= (1 + daily_return)
    
    # Generate optimistic and pessimistic paths
    optimistic_value = initial_value
    pessimistic_value = initial_value
    
    for day in range(total_days + 1):
        # Optimistic: 95th percentile
        optimistic_factor = daily_return + 1.645 * daily_volatility
        optimistic_value *= (1 + optimistic_factor)
        
        # Pessimistic: 5th percentile
        pessimistic_factor = daily_return - 1.645 * daily_volatility
        pessimistic_value *= (1 + max(-0.99, pessimistic_factor))  # Prevent negative values
    
    # Compile projection data
    projection_data = {
        "expected_path": expected_path,
        "final_expected_value": expected_path[-1]["value"],
        "optimistic_value": optimistic_value,
        "pessimistic_value": pessimistic_value
    }
    
    db_projection.projection_data = projection_data
    db_projection.projected_value = expected_path[-1]["value"]
    db_projection.best_case_value = optimistic_value
    db_projection.worst_case_value = pessimistic_value
    
    db.add(db_projection)
    db.commit()
    db.refresh(db_projection)
    return db_projection
