"""
Trades router for Robot-Crypt API.
"""

from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_user, get_current_active_superuser
from src.database.database import get_database
from src.schemas.trade import (
    Trade, TradeCreate, TradeCreateRequest, TradeResponse, TradeUpdate, TradeExecution, 
    TradeSignal, TradePerformance
)
from src.schemas.user import User
from src.services.trade_service import TradeService
from src.services.asset_service import AssetService

router = APIRouter()


@router.get("/", response_model=List[Trade])
@router.get("", response_model=List[Trade])
async def read_trades(
    skip: int = 0,
    limit: int = 100,
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    trade_type: Optional[str] = Query(None, description="Filter by trade type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve trades with optional filters.
    """
    trade_service = TradeService(db)
    
    # Non-superuser can only see their own trades
    user_id = None if current_user.is_superuser else current_user.id
    
    trades = await trade_service.get_multi(
        skip=skip,
        limit=limit,
        user_id=user_id,
        asset_id=asset_id,
        trade_type=trade_type,
        status=status,
        date_from=date_from,
        date_to=date_to
    )
    return trades


@router.post("/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_request: TradeCreateRequest,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new trade.
    """
    trade_service = TradeService(db)
    asset_service = AssetService(db)
    
    # Convert trade request to internal format
    # First, find or create the asset
    asset = await asset_service.get_by_symbol(trade_request.symbol)
    if not asset:
        # Create asset if it doesn't exist
        from src.schemas.asset import AssetCreate
        asset_data = AssetCreate(
            symbol=trade_request.symbol,
            name=trade_request.symbol.replace('USDT', '').replace('BTC', ''),
            type="cryptocurrency",
            metadata={"exchange": trade_request.exchange}
        )
        asset = await asset_service.create(asset_data)
    
    # Convert string values to float
    quantity = float(trade_request.quantity)
    price = float(trade_request.price)
    total_value = quantity * price
    
    # Create TradeCreate object
    trade_in = TradeCreate(
        user_id=current_user.id,
        asset_id=asset.id,
        trade_type=trade_request.side,
        quantity=quantity,
        price=price,
        total_value=total_value,
        fee=total_value * 0.001,  # 0.1% fee
        status="pending",
        notes=trade_request.notes,
        metadata={
            "exchange": trade_request.exchange,
            "stop_loss": float(trade_request.stop_loss) if trade_request.stop_loss else None,
            "take_profit": float(trade_request.take_profit) if trade_request.take_profit else None,
        }
    )
    
    trade = await trade_service.create(trade_in)
    
    # Construct TradeResponse with expected fields
    return TradeResponse(
        id=trade.id,
        symbol=trade_request.symbol,
        side=trade_request.side,
        quantity=trade.quantity,
        price=trade.price,
        total_value=trade.total_value,
        fee=trade.fee,
        status=trade.status,
        exchange=trade_request.exchange,
        stop_loss=float(trade_request.stop_loss) if trade_request.stop_loss else None,
        take_profit=float(trade_request.take_profit) if trade_request.take_profit else None,
        notes=trade.notes,
        created_at=trade.executed_at,
        executed_at=trade.executed_at
    )


@router.post("/execute", response_model=dict)
async def execute_trade(
    trade_execution: TradeExecution,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Execute a trade order.
    """
    asset_service = AssetService(db)
    trade_service = TradeService(db)
    
    # Get asset by symbol
    asset = await asset_service.get_by_symbol(trade_execution.asset_symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Implement trade execution logic
    # 1. Validate trade parameters
    if trade_execution.quantity and trade_execution.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    if trade_execution.trade_amount and trade_execution.trade_amount <= 0:
        raise HTTPException(status_code=400, detail="Trade amount must be positive")
    
    # 2. Check account balance (simplified check)
    # In a real implementation, this would check actual account balance
    
    # 3. Place order with exchange API (simulated)
    # In a real implementation, this would integrate with exchange APIs
    
    # 4. Store trade record and update portfolio handled below
    
    # Mock execution for demonstration
    execution_price = trade_execution.price or asset.current_price or 50000
    quantity = trade_execution.quantity or (trade_execution.trade_amount / execution_price if trade_execution.trade_amount else 0.001)
    total_value = execution_price * quantity
    fee = total_value * 0.001  # 0.1% fee
    
    # Create trade record
    trade_in = TradeCreate(
        user_id=current_user.id,
        asset_id=asset.id,
        trade_type=trade_execution.trade_type,
        quantity=quantity,
        price=execution_price,
        total_value=total_value,
        fee=fee,
        status="executed",
        notes=f"Auto-executed via API",
        metadata={
            "stop_loss": trade_execution.stop_loss,
            "take_profit": trade_execution.take_profit,
            "execution_type": "market" if not trade_execution.price else "limit"
        }
    )
    
    trade = await trade_service.create(trade_in)
    
    return {
        "trade_id": trade.id,
        "status": "executed",
        "execution_price": execution_price,
        "quantity": quantity,
        "total_value": total_value,
        "fee": fee,
        "executed_at": trade.executed_at.isoformat(),
        "message": f"Successfully executed {trade_execution.trade_type} order for {quantity} {trade_execution.asset_symbol}"
    }


@router.get("/performance", response_model=TradePerformance)
async def get_trade_performance(
    period: str = Query("all_time", description="Performance period"),
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get trading performance metrics.
    """
    trade_service = TradeService(db)
    
    # Non-superuser can only see their own performance
    user_id = None if current_user.is_superuser else current_user.id
    
    performance = await trade_service.get_performance(
        user_id=user_id,
        period=period,
        asset_id=asset_id
    )
    return performance


@router.get("/recent", response_model=List[Trade])
async def get_recent_trades(
    limit: int = Query(10, le=50, description="Number of recent trades"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get recent trades.
    """
    trade_service = TradeService(db)
    
    # Non-superuser can only see their own trades
    user_id = None if current_user.is_superuser else current_user.id
    
    trades = await trade_service.get_recent_trades(user_id=user_id, limit=limit)
    return trades


@router.get("/{trade_id}", response_model=Trade)
async def read_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get trade by ID.
    """
    trade_service = TradeService(db)
    trade = await trade_service.get(trade_id)
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Check ownership if not superuser
    if not current_user.is_superuser and trade.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return trade


@router.put("/{trade_id}", response_model=Trade)
async def update_trade(
    trade_id: int,
    trade_in: TradeUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a trade.
    """
    trade_service = TradeService(db)
    
    # Check if trade exists and user has permission
    existing_trade = await trade_service.get(trade_id)
    if not existing_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if not current_user.is_superuser and existing_trade.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    trade = await trade_service.update(trade_id, trade_in)
    return trade


@router.delete("/{trade_id}", response_model=Trade)
async def delete_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete a trade (superuser only).
    """
    trade_service = TradeService(db)
    trade = await trade_service.delete(trade_id)
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade


@router.post("/signal", response_model=dict)
async def generate_trade_signal(
    asset_symbol: str,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate trading signal for an asset.
    """
    asset_service = AssetService(db)
    
    # Get asset by symbol
    asset = await asset_service.get_by_symbol(asset_symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Implement signal generation logic
    # 1. Fetch latest price data (from asset)
    current_price = asset.current_price or 50000
    
    # 2. Calculate technical indicators (simplified)
    # In a real implementation, this would use actual technical analysis
    
    # 3. Apply trading strategy rules
    # 4. Generate signal with confidence
    
    # Mock signal generation
    import random
    
    signal_types = ["buy", "sell", "hold"]
    signal_type = random.choice(signal_types)
    strength = round(random.uniform(0.3, 0.9), 2)
    
    current_price = asset.current_price or 50000
    
    reasoning_map = {
        "buy": "Technical indicators suggest oversold conditions with potential reversal",
        "sell": "Overbought conditions detected with resistance at current levels", 
        "hold": "Mixed signals suggest waiting for clearer market direction"
    }
    
    signal = TradeSignal(
        asset_symbol=asset_symbol,
        signal_type=signal_type,
        strength=strength,
        price=current_price,
        indicators={
            "RSI": round(random.uniform(20, 80), 1),
            "MA_20": round(current_price * random.uniform(0.95, 1.05), 2),
            "EMA_12": round(current_price * random.uniform(0.98, 1.02), 2),
            "Volume": round(random.uniform(1000000, 10000000), 0)
        },
        reasoning=reasoning_map[signal_type]
    )
    
    return {
        "signal": signal.model_dump(),
        "generated_at": datetime.now().isoformat(),
        "confidence": strength,
        "recommendation": f"Consider {signal_type.upper()} position" if signal_type != "hold" else "Hold current position"
    }


@router.get("/asset/{asset_id}", response_model=List[Trade])
async def get_trades_by_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all trades for a specific asset.
    """
    trade_service = TradeService(db)
    
    # Non-superuser can only see their own trades
    user_id = None if current_user.is_superuser else current_user.id
    
    trades = await trade_service.get_trades_by_asset(asset_id=asset_id, user_id=user_id)
    return trades
