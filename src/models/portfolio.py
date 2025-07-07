"""
Portfolio data models.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Set

from src.models.trade import OrderSide


@dataclass
class Asset:
    """Asset model representing a cryptocurrency."""
    symbol: str
    name: str
    price: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    last_updated: Optional[datetime] = None


@dataclass
class AssetHolding:
    """Asset holding in a portfolio."""
    symbol: str
    quantity: float
    avg_buy_price: float
    current_price: float
    
    @property
    def invested_value(self) -> float:
        """Calculate invested value."""
        return self.quantity * self.avg_buy_price
    
    @property
    def current_value(self) -> float:
        """Calculate current value."""
        return self.quantity * self.current_price
    
    @property
    def profit_loss(self) -> float:
        """Calculate profit/loss in currency."""
        return self.current_value - self.invested_value
    
    @property
    def profit_loss_percentage(self) -> float:
        """Calculate profit/loss as percentage."""
        if self.invested_value == 0:
            return 0.0
        return (self.profit_loss / self.invested_value) * 100


@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a specific point in time."""
    timestamp: datetime
    holdings: List[AssetHolding] = field(default_factory=list)
    
    @property
    def total_invested_value(self) -> float:
        """Calculate total invested value."""
        return sum(holding.invested_value for holding in self.holdings)
    
    @property
    def total_current_value(self) -> float:
        """Calculate total current value."""
        return sum(holding.current_value for holding in self.holdings)
    
    @property
    def total_profit_loss(self) -> float:
        """Calculate total profit/loss in currency."""
        return sum(holding.profit_loss for holding in self.holdings)
    
    @property
    def total_profit_loss_percentage(self) -> float:
        """Calculate total profit/loss as percentage."""
        if self.total_invested_value == 0:
            return 0.0
        return (self.total_profit_loss / self.total_invested_value) * 100
    
    def asset_allocation(self) -> Dict[str, float]:
        """Calculate asset allocation as percentages."""
        if self.total_current_value == 0:
            return {holding.symbol: 0.0 for holding in self.holdings}
        
        return {
            holding.symbol: (holding.current_value / self.total_current_value) * 100
            for holding in self.holdings
        }


@dataclass
class PortfolioTransaction:
    """Portfolio transaction."""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    fee: float = 0.0
    fee_currency: str = "USDT"
    note: Optional[str] = None
    
    @property
    def total_value(self) -> float:
        """Calculate total value of the transaction."""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Calculate net value after fee."""
        return self.total_value + (self.fee if self.side == OrderSide.SELL else -self.fee)


@dataclass
class PortfolioPerformance:
    """Portfolio performance metrics."""
    start_date: datetime
    end_date: datetime
    starting_value: float
    ending_value: float
    deposits: float = 0.0
    withdrawals: float = 0.0
    
    @property
    def absolute_return(self) -> float:
        """Calculate absolute return."""
        return self.ending_value - self.starting_value - self.deposits + self.withdrawals
    
    @property
    def percentage_return(self) -> float:
        """Calculate percentage return."""
        if self.starting_value == 0:
            return 0.0
        adjusted_start = self.starting_value + self.deposits - self.withdrawals
        if adjusted_start == 0:
            return 0.0
        return (self.absolute_return / adjusted_start) * 100
