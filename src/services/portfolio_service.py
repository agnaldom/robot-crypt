from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
import json
import math
import numpy as np

from src.models.portfolio_snapshot import PortfolioSnapshot
from src.models.portfolio_asset import PortfolioAsset
from src.models.portfolio_transaction import PortfolioTransaction
from src.models.portfolio_metric import PortfolioMetric
from src.models.portfolio_alert import PortfolioAlert
from src.models.portfolio_projection import PortfolioProjection
from src.models.portfolio_report import PortfolioReport
from src.models.asset import Asset

from src.schemas.portfolio import (
    PortfolioSnapshotCreate, PortfolioSnapshotUpdate,
    PortfolioTransactionCreate, PortfolioTransactionUpdate,
    PortfolioMetricCreate, PortfolioMetricUpdate,
    PortfolioAlertCreate, PortfolioAlertUpdate,
    PortfolioProjectionCreate, PortfolioProjectionUpdate,
    PortfolioReportCreate, PortfolioReportUpdate
)


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Portfolio Snapshot Services ====================

    async def get_portfolio_snapshot(self, snapshot_id: int, user_id: int) -> Optional[PortfolioSnapshot]:
        """Get a specific portfolio snapshot by ID and user ID."""
        result = await self.db.execute(
            select(PortfolioSnapshot).where(
                and_(PortfolioSnapshot.id == snapshot_id, PortfolioSnapshot.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_portfolio_snapshot(self, user_id: int) -> Optional[PortfolioSnapshot]:
        """Get the latest portfolio snapshot for a user."""
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == user_id)
            .order_by(desc(PortfolioSnapshot.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_portfolio_snapshots(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots for a user with optional date filtering."""
        conditions = [PortfolioSnapshot.user_id == user_id]
        
        if start_date:
            conditions.append(PortfolioSnapshot.created_at >= start_date)
        if end_date:
            conditions.append(PortfolioSnapshot.created_at <= end_date)

        query = (
            select(PortfolioSnapshot)
            .where(and_(*conditions))
            .order_by(desc(PortfolioSnapshot.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_portfolio_snapshot(self, snapshot_in: PortfolioSnapshotCreate) -> PortfolioSnapshot:
        """Create a new portfolio snapshot with assets."""
        # Create snapshot
        db_snapshot = PortfolioSnapshot(
            user_id=snapshot_in.user_id,
            total_invested_value=snapshot_in.total_invested_value,
            current_market_value=snapshot_in.current_market_value,
            total_profit_loss=snapshot_in.total_profit_loss,
            profit_loss_percentage=snapshot_in.profit_loss_percentage,
            risk_level=snapshot_in.risk_level,
            value_at_risk=snapshot_in.value_at_risk,
            max_drawdown=snapshot_in.max_drawdown,
            volatility=snapshot_in.volatility,
            sharpe_ratio=snapshot_in.sharpe_ratio,
            btc_comparison=snapshot_in.btc_comparison,
            eth_comparison=snapshot_in.eth_comparison,
            metrics=snapshot_in.metrics
        )
        
        self.db.add(db_snapshot)
        await self.db.flush()  # Flush to get the ID

        # Create assets for the snapshot
        for asset_data in snapshot_in.assets:
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
            self.db.add(db_asset)

        await self.db.commit()
        await self.db.refresh(db_snapshot)
        return db_snapshot

    async def update_portfolio_snapshot(
        self, 
        snapshot_id: int, 
        snapshot_in: PortfolioSnapshotUpdate,
        user_id: int
    ) -> Optional[PortfolioSnapshot]:
        """Update a portfolio snapshot."""
        result = await self.db.execute(
            select(PortfolioSnapshot).where(
                and_(PortfolioSnapshot.id == snapshot_id, PortfolioSnapshot.user_id == user_id)
            )
        )
        db_snapshot = result.scalar_one_or_none()
        
        if not db_snapshot:
            return None

        update_data = snapshot_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_snapshot, field, value)

        await self.db.commit()
        await self.db.refresh(db_snapshot)
        return db_snapshot

    async def delete_portfolio_snapshot(self, snapshot_id: int, user_id: int) -> Optional[PortfolioSnapshot]:
        """Delete a portfolio snapshot and its related assets."""
        result = await self.db.execute(
            select(PortfolioSnapshot).where(
                and_(PortfolioSnapshot.id == snapshot_id, PortfolioSnapshot.user_id == user_id)
            )
        )
        db_snapshot = result.scalar_one_or_none()

        if db_snapshot:
            await self.db.delete(db_snapshot)
            await self.db.commit()

        return db_snapshot

    # ==================== Portfolio Transaction Services ====================

    async def get_portfolio_transaction(self, transaction_id: int, user_id: int) -> Optional[PortfolioTransaction]:
        """Get a specific portfolio transaction by ID and user ID."""
        result = await self.db.execute(
            select(PortfolioTransaction).where(
                and_(PortfolioTransaction.id == transaction_id, PortfolioTransaction.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_portfolio_transactions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PortfolioTransaction]:
        """Get portfolio transactions for a user with filtering options."""
        conditions = [PortfolioTransaction.user_id == user_id]

        if asset_id:
            conditions.append(PortfolioTransaction.asset_id == asset_id)
        if transaction_type:
            conditions.append(PortfolioTransaction.transaction_type == transaction_type)
        if start_date:
            conditions.append(PortfolioTransaction.executed_at >= start_date)
        if end_date:
            conditions.append(PortfolioTransaction.executed_at <= end_date)

        query = (
            select(PortfolioTransaction)
            .where(and_(*conditions))
            .order_by(desc(PortfolioTransaction.executed_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_portfolio_transaction(self, transaction_in: PortfolioTransactionCreate) -> PortfolioTransaction:
        """Create a new portfolio transaction."""
        db_transaction = PortfolioTransaction(
            user_id=transaction_in.user_id,
            asset_id=transaction_in.asset_id,
            transaction_type=transaction_in.transaction_type,
            quantity=transaction_in.quantity,
            price=transaction_in.price,
            total_value=transaction_in.total_value,
            fee=transaction_in.fee,
            realized_profit_loss=transaction_in.realized_profit_loss,
            profit_loss_percentage=transaction_in.profit_loss_percentage,
            notes=transaction_in.notes,
            metadata=transaction_in.metadata,
            external_id=transaction_in.external_id,
            external_source=transaction_in.external_source,
            executed_at=transaction_in.executed_at
        )
        
        self.db.add(db_transaction)
        await self.db.commit()
        await self.db.refresh(db_transaction)
        return db_transaction

    async def update_portfolio_transaction(
        self,
        transaction_id: int,
        transaction_in: PortfolioTransactionUpdate,
        user_id: int
    ) -> Optional[PortfolioTransaction]:
        """Update a portfolio transaction."""
        result = await self.db.execute(
            select(PortfolioTransaction).where(
                and_(PortfolioTransaction.id == transaction_id, PortfolioTransaction.user_id == user_id)
            )
        )
        db_transaction = result.scalar_one_or_none()
        
        if not db_transaction:
            return None

        update_data = transaction_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)

        await self.db.commit()
        await self.db.refresh(db_transaction)
        return db_transaction

    async def delete_portfolio_transaction(self, transaction_id: int, user_id: int) -> Optional[PortfolioTransaction]:
        """Delete a portfolio transaction."""
        result = await self.db.execute(
            select(PortfolioTransaction).where(
                and_(PortfolioTransaction.id == transaction_id, PortfolioTransaction.user_id == user_id)
            )
        )
        db_transaction = result.scalar_one_or_none()

        if db_transaction:
            await self.db.delete(db_transaction)
            await self.db.commit()

        return db_transaction

    # ==================== Portfolio Analysis Services ====================

    async def get_portfolio_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get a summary of the user's portfolio."""
        # Get the latest snapshot
        latest_snapshot = await self.get_latest_portfolio_snapshot(user_id)

        if not latest_snapshot:
            return {
                "status": "empty",
                "message": "No portfolio data available",
                "data": {}
            }

        # Get historical snapshots for the time period
        start_date = datetime.utcnow() - timedelta(days=days)
        historical_snapshots = await self.get_portfolio_snapshots(user_id, 0, 100, start_date)

        # Calculate period change
        period_start_value = historical_snapshots[-1].current_market_value if historical_snapshots else latest_snapshot.current_market_value
        period_change_value = latest_snapshot.current_market_value - period_start_value
        period_change_percentage = (period_change_value / period_start_value) * 100 if period_start_value > 0 else 0

        # Get recent transactions
        recent_transactions = await self.get_portfolio_transactions(
            user_id,
            0,
            5,
            start_date=datetime.utcnow() - timedelta(days=7)
        )

        # Get assets for this snapshot
        assets_result = await self.db.execute(
            select(PortfolioAsset).where(PortfolioAsset.snapshot_id == latest_snapshot.id)
        )
        assets = assets_result.scalars().all()

        # Calculate asset distribution
        assets_distribution = {}
        for asset in assets:
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
                "assets_count": len(assets),
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

    async def get_portfolio_performance(
        self,
        user_id: int,
        period: str = "month",
        compare_with: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed portfolio performance metrics and history."""
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

        # Get snapshots for historical data
        snapshots = await self.get_portfolio_snapshots(user_id, 0, 100, start_date=start_date)

        # Process performance data
        performance_history = []
        for snapshot in snapshots:
            performance_history.append({
                "date": snapshot.created_at,
                "value": snapshot.current_market_value,
                "profit_loss": snapshot.total_profit_loss,
                "profit_loss_percentage": snapshot.profit_loss_percentage
            })

        # Calculate basic metrics
        latest_snapshot = snapshots[0] if snapshots else None
        oldest_snapshot = snapshots[-1] if snapshots else None

        starting_value = oldest_snapshot.current_market_value if oldest_snapshot else 0
        ending_value = latest_snapshot.current_market_value if latest_snapshot else 0
        absolute_return = ending_value - starting_value
        percentage_return = (absolute_return / starting_value) * 100 if starting_value > 0 else 0

        return {
            "status": "success",
            "data": {
                "period": period,
                "performance_history": performance_history,
                "metrics": {
                    "starting_value": starting_value,
                    "ending_value": ending_value,
                    "absolute_return": absolute_return,
                    "percentage_return": percentage_return,
                    "volatility": latest_snapshot.volatility if latest_snapshot else 0,
                    "sharpe_ratio": latest_snapshot.sharpe_ratio if latest_snapshot else 0,
                    "max_drawdown": latest_snapshot.max_drawdown if latest_snapshot else 0,
                },
                "comparison": {
                    "symbol": compare_with,
                    "performance_percentage": 0.0  # Placeholder
                } if compare_with else None
            }
        }

    async def get_portfolio_risk_assessment(self, user_id: int) -> Dict[str, Any]:
        """Get portfolio risk metrics including VaR, volatility, and concentration risk."""
        # Get the latest snapshot
        latest_snapshot = await self.get_latest_portfolio_snapshot(user_id)

        if not latest_snapshot:
            return {
                "status": "empty",
                "message": "No portfolio data available",
                "data": {}
            }

        # Get assets for concentration risk calculation
        assets_result = await self.db.execute(
            select(PortfolioAsset).where(PortfolioAsset.snapshot_id == latest_snapshot.id)
        )
        assets = assets_result.scalars().all()

        # Calculate concentration risk
        concentration_risk = 0
        high_concentration_assets = []

        if assets:
            # Herfindahl-Hirschman Index (HHI) for concentration
            hhi = sum(asset.allocation_percentage ** 2 for asset in assets) / 100
            concentration_risk = hhi * 100  # Scale to 0-100

            # Identify assets with high concentration
            for asset in assets:
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
                "volatility": latest_snapshot.volatility or 0,
                "concentration_risk": concentration_risk,
                "high_concentration_assets": high_concentration_assets,
                "risk_metrics": {
                    "diversification_score": 100 - concentration_risk,
                    "risk_reward_ratio": latest_snapshot.sharpe_ratio if latest_snapshot.sharpe_ratio else 0
                }
            }
        }

    async def get_assets_distribution(self, user_id: int) -> Dict[str, Any]:
        """Get detailed breakdown of portfolio assets distribution."""
        # Get the latest snapshot with assets
        latest_snapshot = await self.get_latest_portfolio_snapshot(user_id)

        if not latest_snapshot:
            return {
                "status": "empty",
                "message": "No portfolio data available",
                "data": {}
            }

        # Get assets for this snapshot
        assets_result = await self.db.execute(
            select(PortfolioAsset).where(PortfolioAsset.snapshot_id == latest_snapshot.id)
        )
        assets = assets_result.scalars().all()

        # Process assets
        assets_data = []
        for asset in assets:
            # Get the full asset info
            asset_info_result = await self.db.execute(
                select(Asset).where(Asset.id == asset.asset_id)
            )
            asset_info = asset_info_result.scalar_one_or_none()

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
