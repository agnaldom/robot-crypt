from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import json
import math
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.portfolio_asset import PortfolioAsset
from app.models.portfolio_transaction import PortfolioTransaction
from app.models.portfolio_metric import PortfolioMetric
from app.models.portfolio_alert import PortfolioAlert
from app.models.portfolio_projection import PortfolioProjection
from app.models.portfolio_report import PortfolioReport
from app.models.asset import Asset


# ==================== Portfolio Snapshot Services ====================

def get_portfolio_snapshot(db: Session, snapshot_id: int, user_id: int) -> Optional[PortfolioSnapshot]:
    """
    Get a specific portfolio snapshot by ID and user ID.
    """
    return db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.id == snapshot_id,
        PortfolioSnapshot.user_id == user_id
    ).first()


def get_latest_portfolio_snapshot(db: Session, user_id: int) -> Optional[PortfolioSnapshot]:
    """
    Get the latest portfolio snapshot for a user.
    """
    return db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id
    ).order_by(desc(PortfolioSnapshot.created_at)).first()


def get_portfolio_snapshots(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[PortfolioSnapshot]:
    """
    Get portfolio snapshots for a user with optional date filtering.
    """
    query = db.query(PortfolioSnapshot).filter(PortfolioSnapshot.user_id == user_id)
    
    if start_date:
        query = query.filter(PortfolioSnapshot.created_at >= start_date)
    
    if end_date:
        query = query.filter(PortfolioSnapshot.created_at <= end_date)
    
    return query.order_by(desc(PortfolioSnapshot.created_at)).offset(skip).limit(limit).all()


def create_portfolio_snapshot(db: Session, snapshot_in: Dict[str, Any]) -> PortfolioSnapshot:
    """
    Create a new portfolio snapshot with assets.
    """
    # Extract assets data
    assets_data = snapshot_in.pop("assets", [])
    
    # Create snapshot
    db_snapshot = PortfolioSnapshot(**snapshot_in)
    db.add(db_snapshot)
    db.flush()  # Flush to get the ID
    
    # Create assets for the snapshot
    for asset_data in assets_data:
        asset_data["snapshot_id"] = db_snapshot.id
        db_asset = PortfolioAsset(**asset_data)
        db.add(db_asset)
    
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def update_portfolio_snapshot(
    db: Session, 
    snapshot_id: int, 
    snapshot_in: Dict[str, Any]
) -> PortfolioSnapshot:
    """
    Update a portfolio snapshot.
    """
    db_snapshot = db.query(PortfolioSnapshot).filter(PortfolioSnapshot.id == snapshot_id).first()
    
    for field, value in snapshot_in.items():
        setattr(db_snapshot, field, value)
    
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def delete_portfolio_snapshot(db: Session, snapshot_id: int) -> PortfolioSnapshot:
    """
    Delete a portfolio snapshot and its related assets.
    """
    db_snapshot = db.query(PortfolioSnapshot).filter(PortfolioSnapshot.id == snapshot_id).first()
    
    if db_snapshot:
        db.delete(db_snapshot)
        db.commit()
    
    return db_snapshot


# ==================== Portfolio Transaction Services ====================

def get_portfolio_transaction(db: Session, transaction_id: int, user_id: int) -> Optional[PortfolioTransaction]:
    """
    Get a specific portfolio transaction by ID and user ID.
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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[PortfolioTransaction]:
    """
    Get portfolio transactions for a user with filtering options.
    """
    query = db.query(PortfolioTransaction).filter(PortfolioTransaction.user_id == user_id)
    
    if asset_id:
        query = query.filter(PortfolioTransaction.asset_id == asset_id)
    
    if transaction_type:
        query = query.filter(PortfolioTransaction.transaction_type == transaction_type)
    
    if start_date:
        query = query.filter(PortfolioTransaction.executed_at >= start_date)
    
    if end_date:
        query = query.filter(PortfolioTransaction.executed_at <= end_date)
    
    return query.order_by(desc(PortfolioTransaction.executed_at)).offset(skip).limit(limit).all()


def create_portfolio_transaction(db: Session, transaction_in: Dict[str, Any]) -> PortfolioTransaction:
    """
    Create a new portfolio transaction and update portfolio data.
    """
    # Create transaction
    db_transaction = PortfolioTransaction(**transaction_in)
    db.add(db_transaction)
    
    # Get the asset
    asset = db.query(Asset).filter(Asset.id == transaction_in["asset_id"]).first()
    
    # Calculate profit/loss for sell transactions
    if transaction_in["transaction_type"] == "sell" and asset:
        # Logic to calculate profit/loss based on previous buy transactions
        # For simplicity, we're not implementing the full FIFO/LIFO logic here
        pass
    
    db.commit()
    db.refresh(db_transaction)
    
    # After creating a transaction, we should update the portfolio snapshot
    # but for simplicity, we're not implementing that here
    
    return db_transaction


def update_portfolio_transaction(
    db: Session, 
    transaction_id: int, 
    transaction_in: Dict[str, Any]
) -> PortfolioTransaction:
    """
    Update a portfolio transaction.
    """
    db_transaction = db.query(PortfolioTransaction).filter(PortfolioTransaction.id == transaction_id).first()
    
    for field, value in transaction_in.items():
        setattr(db_transaction, field, value)
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_portfolio_transaction(db: Session, transaction_id: int) -> PortfolioTransaction:
    """
    Delete a portfolio transaction.
    """
    db_transaction = db.query(PortfolioTransaction).filter(PortfolioTransaction.id == transaction_id).first()
    
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
    
    return db_transaction


# ==================== Portfolio Metric Services ====================

def get_portfolio_metric(db: Session, metric_id: int, user_id: int) -> Optional[PortfolioMetric]:
    """
    Get a specific portfolio metric by ID and user ID.
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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[PortfolioMetric]:
    """
    Get portfolio metrics for a user with filtering options.
    """
    query = db.query(PortfolioMetric).filter(PortfolioMetric.user_id == user_id)
    
    if period_type:
        query = query.filter(PortfolioMetric.period_type == period_type)
    
    if start_date:
        query = query.filter(PortfolioMetric.period_end >= start_date)
    
    if end_date:
        query = query.filter(PortfolioMetric.period_start <= end_date)
    
    return query.order_by(desc(PortfolioMetric.period_end)).offset(skip).limit(limit).all()


def create_portfolio_metric(db: Session, metric_in: Dict[str, Any]) -> PortfolioMetric:
    """
    Create a new portfolio metric.
    """
    db_metric = PortfolioMetric(**metric_in)
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def update_portfolio_metric(
    db: Session, 
    metric_id: int, 
    metric_in: Dict[str, Any]
) -> PortfolioMetric:
    """
    Update a portfolio metric.
    """
    db_metric = db.query(PortfolioMetric).filter(PortfolioMetric.id == metric_id).first()
    
    for field, value in metric_in.items():
        setattr(db_metric, field, value)
    
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def delete_portfolio_metric(db: Session, metric_id: int) -> PortfolioMetric:
    """
    Delete a portfolio metric.
    """
    db_metric = db.query(PortfolioMetric).filter(PortfolioMetric.id == metric_id).first()
    
    if db_metric:
        db.delete(db_metric)
        db.commit()
    
    return db_metric


# ==================== Portfolio Alert Services ====================

def get_portfolio_alert(db: Session, alert_id: int, user_id: int) -> Optional[PortfolioAlert]:
    """
    Get a specific portfolio alert by ID and user ID.
    """
    return db.query(PortfolioAlert).filter(
        PortfolioAlert.id == alert_id,
        PortfolioAlert.user_id == user_id
    ).first()


def get_portfolio_alerts(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_triggered: Optional[bool] = None,
    asset_id: Optional[int] = None
) -> List[PortfolioAlert]:
    """
    Get portfolio alerts for a user with filtering options.
    """
    query = db.query(PortfolioAlert).filter(PortfolioAlert.user_id == user_id)
    
    if is_active is not None:
        query = query.filter(PortfolioAlert.is_active == is_active)
    
    if is_triggered is not None:
        query = query.filter(PortfolioAlert.is_triggered == is_triggered)
    
    if asset_id:
        query = query.filter(PortfolioAlert.asset_id == asset_id)
    
    return query.order_by(desc(PortfolioAlert.created_at)).offset(skip).limit(limit).all()


def create_portfolio_alert(db: Session, alert_in: Dict[str, Any]) -> PortfolioAlert:
    """
    Create a new portfolio alert.
    """
    db_alert = PortfolioAlert(**alert_in)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def update_portfolio_alert(
    db: Session, 
    alert_id: int, 
    alert_in: Dict[str, Any]
) -> PortfolioAlert:
    """
    Update a portfolio alert.
    """
    db_alert = db.query(PortfolioAlert).filter(PortfolioAlert.id == alert_id).first()
    
    for field, value in alert_in.items():
        setattr(db_alert, field, value)
    
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def delete_portfolio_alert(db: Session, alert_id: int) -> PortfolioAlert:
    """
    Delete a portfolio alert.
    """
    db_alert = db.query(PortfolioAlert).filter(PortfolioAlert.id == alert_id).first()
    
    if db_alert:
        db.delete(db_alert)
        db.commit()
    
    return db_alert


# ==================== Portfolio Projection Services ====================

def get_portfolio_projection(db: Session, projection_id: int, user_id: int) -> Optional[PortfolioProjection]:
    """
    Get a specific portfolio projection by ID and user ID.
    """
    return db.query(PortfolioProjection).filter(
        PortfolioProjection.id == projection_id,
        PortfolioProjection.user_id == user_id
    ).first()


def get_portfolio_projections(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    scenario_type: Optional[str] = None
) -> List[PortfolioProjection]:
    """
    Get portfolio projections for a user with filtering options.
    """
    query = db.query(PortfolioProjection).filter(PortfolioProjection.user_id == user_id)
    
    if scenario_type:
        query = query.filter(PortfolioProjection.scenario_type == scenario_type)
    
    return query.order_by(desc(PortfolioProjection.created_at)).offset(skip).limit(limit).all()


def create_portfolio_projection(db: Session, projection_in: Dict[str, Any]) -> PortfolioProjection:
    """
    Create a new portfolio projection.
    """
    db_projection = PortfolioProjection(**projection_in)
    db.add(db_projection)
    db.commit()
    db.refresh(db_projection)
    return db_projection


def update_portfolio_projection(
    db: Session, 
    projection_id: int, 
    projection_in: Dict[str, Any]
) -> PortfolioProjection:
    """
    Update a portfolio projection.
    """
    db_projection = db.query(PortfolioProjection).filter(PortfolioProjection.id == projection_id).first()
    
    for field, value in projection_in.items():
        setattr(db_projection, field, value)
    
    db.add(db_projection)
    db.commit()
    db.refresh(db_projection)
    return db_projection


def delete_portfolio_projection(db: Session, projection_id: int) -> PortfolioProjection:
    """
    Delete a portfolio projection.
    """
    db_projection = db.query(PortfolioProjection).filter(PortfolioProjection.id == projection_id).first()
    
    if db_projection:
        db.delete(db_projection)
        db.commit()
    
    return db_projection


# ==================== Portfolio Report Services ====================

def get_portfolio_report(db: Session, report_id: int, user_id: int) -> Optional[PortfolioReport]:
    """
    Get a specific portfolio report by ID and user ID.
    """
    return db.query(PortfolioReport).filter(
        PortfolioReport.id == report_id,
        PortfolioReport.user_id == user_id
    ).first()


def get_portfolio_reports(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    report_type: Optional[str] = None,
    format: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[PortfolioReport]:
    """
    Get portfolio reports for a user with filtering options.
    """
    query = db.query(PortfolioReport).filter(PortfolioReport.user_id == user_id)
    
    if report_type:
        query = query.filter(PortfolioReport.report_type == report_type)
    
    if format:
        query = query.filter(PortfolioReport.format == format)
    
    if start_date:
        query = query.filter(PortfolioReport.created_at >= start_date)
    
    if end_date:
        query = query.filter(PortfolioReport.created_at <= end_date)
    
    return query.order_by(desc(PortfolioReport.created_at)).offset(skip).limit(limit).all()


def create_portfolio_report(db: Session, report_in: Dict[str, Any]) -> PortfolioReport:
    """
    Create a new portfolio report.
    """
    db_report = PortfolioReport(**report_in)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def update_portfolio_report(
    db: Session, 
    report_id: int, 
    report_in: Dict[str, Any]
) -> PortfolioReport:
    """
    Update a portfolio report.
    """
    db_report = db.query(PortfolioReport).filter(PortfolioReport.id == report_id).first()
    
    for field, value in report_in.items():
        setattr(db_report, field, value)
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def delete_portfolio_report(db: Session, report_id: int) -> PortfolioReport:
    """
    Delete a portfolio report.
    """
    db_report = db.query(PortfolioReport).filter(PortfolioReport.id == report_id).first()
    
    if db_report:
        db.delete(db_report)
        db.commit()
    
    return db_report


# ==================== Portfolio Analysis Services ====================

def get_portfolio_summary(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Get a summary of the user's portfolio.
    """
    # Get the latest snapshot
    latest_snapshot = get_latest_portfolio_snapshot(db, user_id)
    
    if not latest_snapshot:
        return {
            "status": "empty",
            "message": "No portfolio data available",
            "data": {}
        }
    
    # Get historical snapshots for the time period
    start_date = datetime.utcnow() - timedelta(days=days)
    historical_snapshots = get_portfolio_snapshots(db, user_id, 0, 100, start_date)
    
    # Calculate period change
    period_start_value = historical_snapshots[-1].current_market_value if historical_snapshots else latest_snapshot.current_market_value
    period_change_value = latest_snapshot.current_market_value - period_start_value
    period_change_percentage = (period_change_value / period_start_value) * 100 if period_start_value > 0 else 0
    
    # Get recent transactions
    recent_transactions = get_portfolio_transactions(
        db, 
        user_id, 
        0, 
        5, 
        start_date=datetime.utcnow() - timedelta(days=7)
    )
    
    # Calculate asset distribution
    assets_distribution = {}
    for asset in latest_snapshot.assets:
        assets_distribution[asset.symbol] = {
            "allocation_percentage": asset.allocation_percentage,
            "current_value": asset.current_value,
            "profit_loss_percentage": asset.profit_loss_percentage
        }
    
    return {
        "status": "success",
        "data": {
            "portfolio_value": latest_snapshot.current_market_value,
            "total_invested": latest_snapshot.total_invested_value,
            "total_profit_loss": latest_snapshot.total_profit_loss,
            "profit_loss_percentage": latest_snapshot.profit_loss_percentage,
            "period_change_value": period_change_value,
            "period_change_percentage": period_change_percentage,
            "risk_level": latest_snapshot.risk_level,
            "value_at_risk": latest_snapshot.value_at_risk,
            "assets_count": len(latest_snapshot.assets),
            "assets_distribution": assets_distribution,
            "recent_transactions": [
                {
                    "id": tx.id,
                    "date": tx.executed_at,
                    "type": tx.transaction_type,
                    "asset_id": tx.asset_id,
                    "quantity": tx.quantity,
                    "price": tx.price,
                    "total_value": tx.total_value
                }
                for tx in recent_transactions
            ]
        }
    }


def get_portfolio_assets_distribution(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get detailed breakdown of portfolio assets distribution.
    """
    # Get the latest snapshot with assets
    latest_snapshot = get_latest_portfolio_snapshot(db, user_id)
    
    if not latest_snapshot:
        return {
            "status": "empty",
            "message": "No portfolio data available",
            "data": {}
        }
    
    # Process assets
    assets_data = []
    for asset in latest_snapshot.assets:
        # Get the full asset info
        asset_info = db.query(Asset).filter(Asset.id == asset.asset_id).first()
        
        assets_data.append({
            "id": asset.id,
            "asset_id": asset.asset_id,
            "symbol": asset.symbol,
            "name": asset_info.name if asset_info else asset.symbol,
            "type": asset_info.type if asset_info else "unknown",
            "quantity": asset.quantity,
            "avg_buy_price": asset.avg_buy_price,
            "current_price": asset.current_price,
            "invested_value": asset.invested_value,
            "current_value": asset.current_value,
            "profit_loss": asset.profit_loss,
            "profit_loss_percentage": asset.profit_loss_percentage,
            "allocation_percentage": asset.allocation_percentage
        })
    
    # Sort by allocation percentage (descending)
    assets_data = sorted(assets_data, key=lambda x: x["allocation_percentage"], reverse=True)
    
    # Calculate asset type distribution
    type_distribution = {}
    for asset in assets_data:
        asset_type = asset["type"]
        if asset_type not in type_distribution:
            type_distribution[asset_type] = 0
        type_distribution[asset_type] += asset["allocation_percentage"]
    
    return {
        "status": "success",
        "data": {
            "total_value": latest_snapshot.current_market_value,
            "assets": assets_data,
            "type_distribution": type_distribution
        }
    }


def get_portfolio_performance(
    db: Session, 
    user_id: int, 
    period: str = "month",
    compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed portfolio performance metrics and history.
    """
    # Get time period
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = None
    
    # Get portfolio metrics for the period
    metrics = get_portfolio_metrics(
        db, 
        user_id, 
        0, 
        100, 
        start_date=start_date
    )
    
    # Get snapshots for historical data
    snapshots = get_portfolio_snapshots(
        db, 
        user_id, 
        0, 
        100, 
        start_date=start_date
    )
    
    # Get comparison data if requested
    comparison_data = None
    if compare_with and snapshots:
        # This would require historical price data for the comparison asset
        # For simplicity, we're not implementing the full comparison logic
        comparison_data = {
            "symbol": compare_with,
            "performance_percentage": 0.0  # Placeholder
        }
    
    # Process performance data
    performance_history = []
    for snapshot in snapshots:
        performance_history.append({
            "date": snapshot.created_at,
            "value": snapshot.current_market_value,
            "profit_loss": snapshot.total_profit_loss,
            "profit_loss_percentage": snapshot.profit_loss_percentage
        })
    
    # Calculate metrics
    latest_metric = metrics[0] if metrics else None
    
    return {
        "status": "success",
        "data": {
            "period": period,
            "performance_history": performance_history,
            "metrics": {
                "starting_value": latest_metric.starting_value if latest_metric else 0,
                "ending_value": latest_metric.ending_value if latest_metric else 0,
                "absolute_return": latest_metric.absolute_return if latest_metric else 0,
                "percentage_return": latest_metric.percentage_return if latest_metric else 0,
                "volatility": latest_metric.volatility if latest_metric else 0,
                "sharpe_ratio": latest_metric.sharpe_ratio if latest_metric else 0,
                "max_drawdown": latest_metric.max_drawdown if latest_metric else 0,
                "average_win": latest_metric.average_win if latest_metric else 0,
                "average_loss": latest_metric.average_loss if latest_metric else 0,
                "win_rate": latest_metric.win_rate if latest_metric else 0
            },
            "comparison": comparison_data
        }
    }


def get_portfolio_risk_assessment(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get portfolio risk metrics including VaR, volatility, and concentration risk.
    """
    # Get the latest snapshot
    latest_snapshot = get_latest_portfolio_snapshot(db, user_id)
    
    if not latest_snapshot:
        return {
            "status": "empty",
            "message": "No portfolio data available",
            "data": {}
        }
    
    # Get historical snapshots for volatility calculation
    historical_snapshots = get_portfolio_snapshots(
        db, 
        user_id, 
        0, 
        100, 
        start_date=datetime.utcnow() - timedelta(days=90)
    )
    
    # Calculate volatility if we have enough data
    volatility = latest_snapshot.volatility or 0
    if not volatility and len(historical_snapshots) > 2:
        values = [snapshot.current_market_value for snapshot in historical_snapshots]
        returns = [values[i] / values[i-1] - 1 for i in range(1, len(values))]
        volatility = np.std(returns) * 100 if returns else 0
    
    # Calculate concentration risk
    concentration_risk = 0
    high_concentration_assets = []
    
    if latest_snapshot.assets:
        # Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(asset.allocation_percentage ** 2 for asset in latest_snapshot.assets) / 100
        concentration_risk = hhi * 100  # Scale to 0-100
        
        # Identify assets with high concentration
        for asset in latest_snapshot.assets:
            if asset.allocation_percentage > 20:  # Arbitrary threshold
                high_concentration_assets.append({
                    "symbol": asset.symbol,
                    "allocation_percentage": asset.allocation_percentage
                })
    
    return {
        "status": "success",
        "data": {
            "portfolio_value": latest_snapshot.current_market_value,
            "risk_level": latest_snapshot.risk_level or "unknown",
            "value_at_risk": latest_snapshot.value_at_risk or 0,
            "max_drawdown": latest_snapshot.max_drawdown or 0,
            "volatility": volatility,
            "concentration_risk": concentration_risk,
            "high_concentration_assets": high_concentration_assets,
            "risk_metrics": {
                "diversification_score": 100 - concentration_risk,
                "risk_reward_ratio": latest_snapshot.sharpe_ratio if latest_snapshot.sharpe_ratio else 0
            }
        }
    }


def generate_portfolio_projection(db: Session, projection_in: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a portfolio projection based on specified parameters.
    """
    # For Monte Carlo simulation, we'd normally run many iterations
    # This is a simplified version
    
    # Extract parameters
    initial_value = projection_in["initial_value"]
    expected_return_rate = projection_in["expected_return_rate"]
    volatility = projection_in["volatility"]
    time_horizon = projection_in["time_horizon"]
    time_unit = projection_in["time_unit"]
    scenario_type = projection_in["scenario_type"]
    
    # Convert time horizon to days
    days_multiplier = 1 if time_unit == "days" else 30 if time_unit == "months" else 365
    days = time_horizon * days_multiplier
    
    # Number of data points (one per day)
    n_points = days
    
    # Annualized to daily rate
    daily_return = (1 + expected_return_rate) ** (1/365) - 1
    daily_volatility = volatility / math.sqrt(365)
    
    # Adjust return based on scenario
    if scenario_type == "optimistic":
        daily_return *= 1.5
    elif scenario_type == "pessimistic":
        daily_return *= 0.5
    
    # Generate time points
    today = datetime.utcnow()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n_points)]
    
    # Generate base projection
    values = [initial_value]
    for i in range(1, n_points):
        values.append(values[-1] * (1 + daily_return))
    
    # Generate best and worst case (simple approach)
    best_case = [initial_value]
    worst_case = [initial_value]
    
    for i in range(1, n_points):
        best_case.append(best_case[-1] * (1 + daily_return + 2 * daily_volatility))
        worst_case.append(worst_case[-1] * (1 + daily_return - 2 * daily_volatility))
    
    # Final projected values
    projected_value = values[-1]
    best_case_value = best_case[-1]
    worst_case_value = worst_case[-1]
    
    # Create projection data
    projection_data = {
        "dates": dates,
        "values": values,
        "best_case": best_case,
        "worst_case": worst_case
    }
    
    # Store projection if requested
    if projection_in.get("save_projection", False):
        projection_obj = {
            "user_id": projection_in["user_id"],
            "scenario_type": scenario_type,
            "time_horizon": time_horizon,
            "time_unit": time_unit,
            "initial_value": initial_value,
            "expected_return_rate": expected_return_rate,
            "volatility": volatility,
            "projected_value": projected_value,
            "best_case_value": best_case_value,
            "worst_case_value": worst_case_value,
            "projection_data": projection_data,
            "title": projection_in.get("title", f"{scenario_type.capitalize()} {time_horizon} {time_unit} Projection"),
            "description": projection_in.get("description", "")
        }
        
        if "recurring_investment" in projection_in:
            projection_obj["recurring_investment"] = projection_in["recurring_investment"]
        
        if "recurring_frequency" in projection_in:
            projection_obj["recurring_frequency"] = projection_in["recurring_frequency"]
        
        if "withdrawal_rate" in projection_in:
            projection_obj["withdrawal_rate"] = projection_in["withdrawal_rate"]
        
        if "inflation_rate" in projection_in:
            projection_obj["inflation_rate"] = projection_in["inflation_rate"]
        
        create_portfolio_projection(db, projection_obj)
    
    return {
        "status": "success",
        "data": {
            "initial_value": initial_value,
            "projected_value": projected_value,
            "best_case_value": best_case_value,
            "worst_case_value": worst_case_value,
            "absolute_return": projected_value - initial_value,
            "percentage_return": ((projected_value / initial_value) - 1) * 100,
            "scenario_type": scenario_type,
            "time_horizon": time_horizon,
            "time_unit": time_unit,
            "projection_data": projection_data
        }
    }
