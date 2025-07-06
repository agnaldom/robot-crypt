"""
Trade service for Robot-Crypt API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

from src.models.trade import Trade
from src.models.asset import Asset
from src.schemas.trade import TradeCreate, TradeUpdate, TradePerformance


class TradeService:
    """Trade service for async database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, trade_id: int) -> Optional[Trade]:
        """Get a trade by ID."""
        result = await self.db.execute(
            select(Trade).where(Trade.id == trade_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        asset_id: Optional[int] = None,
        trade_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Trade]:
        """Get multiple trades with optional filters."""
        query = select(Trade)
        
        conditions = []
        
        if user_id:
            conditions.append(Trade.user_id == user_id)
        
        if asset_id:
            conditions.append(Trade.asset_id == asset_id)
        
        if trade_type:
            conditions.append(Trade.trade_type == trade_type)
        
        if status:
            conditions.append(Trade.status == status)
        
        if date_from:
            conditions.append(Trade.executed_at >= date_from)
        
        if date_to:
            conditions.append(Trade.executed_at <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(Trade.executed_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, trade_in: TradeCreate) -> Trade:
        """Create a new trade."""
        db_trade = Trade(
            user_id=trade_in.user_id,
            asset_id=trade_in.asset_id,
            trade_type=trade_in.trade_type,
            quantity=trade_in.quantity,
            price=trade_in.price,
            total_value=trade_in.total_value,
            fee=trade_in.fee,
            status=trade_in.status,
            notes=trade_in.notes,
            metadata=trade_in.metadata or {}
        )
        self.db.add(db_trade)
        await self.db.commit()
        await self.db.refresh(db_trade)
        return db_trade
    
    async def update(self, trade_id: int, trade_in: TradeUpdate) -> Optional[Trade]:
        """Update a trade."""
        db_trade = await self.get(trade_id)
        if not db_trade:
            return None
        
        update_data = trade_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_trade, field):
                setattr(db_trade, field, value)
        
        self.db.add(db_trade)
        await self.db.commit()
        await self.db.refresh(db_trade)
        return db_trade
    
    async def delete(self, trade_id: int) -> Optional[Trade]:
        """Delete a trade."""
        db_trade = await self.get(trade_id)
        if not db_trade:
            return None
        
        await self.db.delete(db_trade)
        await self.db.commit()
        return db_trade
    
    async def get_performance(
        self,
        user_id: Optional[int] = None,
        period: str = "all_time",
        asset_id: Optional[int] = None
    ) -> TradePerformance:
        """Get trading performance metrics."""
        
        # Calculate date range based on period
        date_from = None
        if period == "daily":
            date_from = datetime.now() - timedelta(days=1)
        elif period == "weekly":
            date_from = datetime.now() - timedelta(weeks=1)
        elif period == "monthly":
            date_from = datetime.now() - timedelta(days=30)
        elif period == "yearly":
            date_from = datetime.now() - timedelta(days=365)
        
        # Build query conditions
        conditions = [Trade.status == "executed"]
        
        if user_id:
            conditions.append(Trade.user_id == user_id)
        
        if asset_id:
            conditions.append(Trade.asset_id == asset_id)
        
        if date_from:
            conditions.append(Trade.executed_at >= date_from)
        
        # Get all trades for the period
        query = select(Trade).where(and_(*conditions))
        result = await self.db.execute(query)
        trades = result.scalars().all()
        
        # Calculate metrics
        total_trades = len(trades)
        if total_trades == 0:
            return TradePerformance(
                period=period,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_profit=0.0,
                total_profit_percentage=0.0,
                avg_profit_per_trade=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                total_fees=0.0
            )
        
        winning_trades = sum(1 for trade in trades if trade.profit_loss and trade.profit_loss > 0)
        losing_trades = sum(1 for trade in trades if trade.profit_loss and trade.profit_loss < 0)
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_profit = sum(trade.profit_loss or 0 for trade in trades)
        total_value = sum(trade.total_value for trade in trades)
        total_profit_percentage = (total_profit / total_value * 100) if total_value > 0 else 0
        
        avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0
        
        profits = [trade.profit_loss or 0 for trade in trades if trade.profit_loss]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        
        total_fees = sum(trade.fee for trade in trades)
        
        # Calculate Sharpe ratio (simplified)
        if profits:
            returns = [p / trade.total_value for trade, p in zip(trades, profits) if trade.total_value > 0]
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown (simplified)
        running_profit = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades, key=lambda x: x.executed_at):
            running_profit += trade.profit_loss or 0
            if running_profit > peak:
                peak = running_profit
            drawdown = peak - running_profit
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return TradePerformance(
            period=period,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            total_profit_percentage=total_profit_percentage,
            avg_profit_per_trade=avg_profit_per_trade,
            best_trade=best_trade,
            worst_trade=worst_trade,
            total_fees=total_fees,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown
        )
    
    async def get_recent_trades(self, user_id: Optional[int] = None, limit: int = 10) -> List[Trade]:
        """Get recent trades."""
        query = select(Trade).where(Trade.status == "executed")
        
        if user_id:
            query = query.where(Trade.user_id == user_id)
        
        query = query.order_by(Trade.executed_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_trades_by_asset(self, asset_id: int, user_id: Optional[int] = None) -> List[Trade]:
        """Get all trades for a specific asset."""
        query = select(Trade).where(Trade.asset_id == asset_id)
        
        if user_id:
            query = query.where(Trade.user_id == user_id)
        
        query = query.order_by(Trade.executed_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
