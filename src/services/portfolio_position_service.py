"""
Portfolio Position Service for CRUD operations.
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.models.portfolio_position import PortfolioPosition
from src.schemas.portfolio import PortfolioPositionCreate, PortfolioPositionUpdate


class PortfolioPositionService:
    """Service for portfolio position operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_position(self, position_id: int, user_id: int) -> Optional[PortfolioPosition]:
        """Get a specific portfolio position."""
        stmt = select(PortfolioPosition).where(
            PortfolioPosition.id == position_id,
            PortfolioPosition.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_positions(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PortfolioPosition]:
        """Get all portfolio positions for a user."""
        stmt = select(PortfolioPosition).where(
            PortfolioPosition.user_id == user_id
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_position(self, position_data: PortfolioPositionCreate, user_id: int) -> PortfolioPosition:
        """Create a new portfolio position."""
        position = PortfolioPosition(
            user_id=user_id,
            symbol=position_data.symbol,
            quantity=position_data.quantity,
            average_price=position_data.average_price,
            current_price=position_data.current_price
        )
        self.db.add(position)
        await self.db.commit()
        await self.db.refresh(position)
        return position
    
    async def update_position(
        self, position_id: int, position_data: PortfolioPositionUpdate, user_id: int
    ) -> Optional[PortfolioPosition]:
        """Update a portfolio position."""
        position = await self.get_position(position_id, user_id)
        if not position:
            return None
        
        update_data = position_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(position, field, value)
        
        await self.db.commit()
        await self.db.refresh(position)
        return position
    
    async def delete_position(self, position_id: int, user_id: int) -> bool:
        """Delete a portfolio position."""
        position = await self.get_position(position_id, user_id)
        if not position:
            return False
        
        await self.db.delete(position)
        await self.db.commit()
        return True
    
    async def get_portfolio_summary(self, user_id: int) -> dict:
        """Get portfolio summary with all positions."""
        positions = await self.get_positions(user_id)
        
        if not positions:
            return {
                "total_value": 0.0,
                "total_profit_loss": 0.0,
                "total_profit_loss_percentage": 0.0,
                "positions": []
            }
        
        total_value = sum(pos.current_value for pos in positions)
        total_invested = sum(pos.invested_value for pos in positions)
        total_profit_loss = total_value - total_invested
        total_profit_loss_percentage = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        return {
            "total_value": total_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percentage": round(total_profit_loss_percentage, 2),
            "positions": positions
        }
    
    async def get_portfolio_performance(self, user_id: int) -> dict:
        """Get portfolio performance metrics."""
        positions = await self.get_positions(user_id)
        
        if not positions:
            return {
                "total_invested": 0.0,
                "current_value": 0.0,
                "total_profit_loss": 0.0,
                "total_profit_loss_percentage": 0.0,
                "best_performing_asset": None,
                "worst_performing_asset": None
            }
        
        total_invested = sum(pos.invested_value for pos in positions)
        current_value = sum(pos.current_value for pos in positions)
        total_profit_loss = current_value - total_invested
        total_profit_loss_percentage = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        # Find best and worst performing assets
        best_performing = max(positions, key=lambda x: x.profit_loss_percentage)
        worst_performing = min(positions, key=lambda x: x.profit_loss_percentage)
        
        return {
            "total_invested": total_invested,
            "current_value": current_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percentage": round(total_profit_loss_percentage, 2),
            "best_performing_asset": best_performing.symbol,
            "worst_performing_asset": worst_performing.symbol
        }
    
    def calculate_position_value(self, quantity: Decimal, current_price: Decimal) -> Decimal:
        """Calculate position value (quantity * current_price)."""
        return quantity * current_price
    
    def calculate_profit_loss(self, quantity: Decimal, current_price: Decimal, average_price: Decimal) -> Decimal:
        """Calculate profit/loss (quantity * (current_price - average_price))."""
        return quantity * (current_price - average_price)
    
    def calculate_profit_loss_percentage(self, quantity: Decimal, current_price: Decimal, average_price: Decimal) -> Decimal:
        """Calculate profit/loss percentage ((current_price - average_price) / average_price * 100)."""
        if average_price == 0:
            return Decimal("0.00")
        return ((current_price - average_price) / average_price) * Decimal("100")
    
    def calculate_allocation_percentage(self, position_value: Decimal, total_portfolio_value: Decimal) -> Decimal:
        """Calculate allocation percentage (position_value / total_portfolio_value * 100)."""
        if total_portfolio_value == 0:
            return Decimal("0.00")
        return (position_value / total_portfolio_value) * Decimal("100")
