"""
Trading session API router for Robot-Crypt application.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.security import get_current_user
from src.models.user import User
from src.models.trading_session import TradingSessionStatus, TradingStrategy, OrderStatus
from src.schemas.trading_session import (
    TradingSessionCreate, TradingSessionUpdate, TradingSessionResponse,
    TradingSessionLogResponse, OpenOrderCreate, OpenOrderUpdate, OpenOrderResponse,
    SessionControlRequest, SessionPerformanceMetrics, SessionRiskMetrics
)
from src.schemas.common import SuccessResponse, ErrorResponse
from src.services.trading_session import TradingSessionService, OpenOrderService
from src.core.exceptions import NotFoundError, BadRequestError, UnauthorizedError


router = APIRouter()


@router.post("/sessions", response_model=TradingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_trading_session(
    session_data: TradingSessionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trading session.
    
    - **name**: Session name
    - **strategy**: Trading strategy type
    - **trading_pairs**: List of trading pairs to trade
    - **initial_capital**: Starting capital amount
    - **risk_per_trade**: Risk percentage per trade
    - **strategy_parameters**: Strategy-specific parameters
    """
    try:
        service = TradingSessionService(db)
        session = await service.create_session(current_user.id, session_data)
        return TradingSessionResponse.from_orm(session)
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create session")


@router.get("/sessions/{session_id}", response_model=TradingSessionResponse)
async def get_trading_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a trading session by ID.
    """
    try:
        service = TradingSessionService(db)
        session = await service.get_session(session_id, current_user.id)
        return TradingSessionResponse.from_orm(session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve session")


@router.get("/sessions", response_model=List[TradingSessionResponse])
async def get_user_trading_sessions(
    status: Optional[TradingSessionStatus] = Query(None, description="Filter by session status"),
    strategy: Optional[TradingStrategy] = Query(None, description="Filter by trading strategy"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get trading sessions for the current user.
    
    - **status**: Filter by session status
    - **strategy**: Filter by trading strategy
    - **limit**: Maximum number of sessions (1-100)
    - **offset**: Number of sessions to skip
    """
    try:
        service = TradingSessionService(db)
        sessions = await service.get_user_sessions(
            current_user.id, status, strategy, limit, offset
        )
        return [TradingSessionResponse.from_orm(session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve sessions")


@router.put("/sessions/{session_id}", response_model=TradingSessionResponse)
async def update_trading_session(
    session_id: int,
    update_data: TradingSessionUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a trading session.
    
    Only inactive sessions can be updated.
    """
    try:
        service = TradingSessionService(db)
        session = await service.update_session(session_id, current_user.id, update_data)
        return TradingSessionResponse.from_orm(session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update session")


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def delete_trading_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a trading session.
    
    Only inactive sessions can be deleted.
    """
    try:
        service = TradingSessionService(db)
        await service.delete_session(session_id, current_user.id)
        return SuccessResponse(message="Trading session deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete session")


@router.post("/sessions/{session_id}/control", response_model=TradingSessionResponse)
async def control_trading_session(
    session_id: int,
    control_request: SessionControlRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Control a trading session (start, pause, resume, stop).
    
    - **action**: Action to perform (start, pause, resume, stop)
    - **reason**: Optional reason for the action
    """
    try:
        service = TradingSessionService(db)
        session = await service.control_session(session_id, current_user.id, control_request)
        return TradingSessionResponse.from_orm(session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to control session")


@router.get("/sessions/{session_id}/performance", response_model=SessionPerformanceMetrics)
async def get_session_performance(
    session_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance metrics for a trading session.
    """
    try:
        service = TradingSessionService(db)
        metrics = await service.get_session_performance(session_id, current_user.id)
        return metrics
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve performance metrics")


@router.get("/sessions/{session_id}/risk", response_model=SessionRiskMetrics)
async def get_session_risk_metrics(
    session_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get risk metrics for a trading session.
    """
    try:
        service = TradingSessionService(db)
        metrics = await service.get_session_risk_metrics(session_id, current_user.id)
        return metrics
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve risk metrics")


@router.get("/sessions/{session_id}/logs", response_model=List[TradingSessionLogResponse])
async def get_session_logs(
    session_id: int,
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs to return"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get logs for a trading session.
    
    - **level**: Filter by log level (DEBUG, INFO, WARNING, ERROR)
    - **limit**: Maximum number of logs (1-500)
    """
    try:
        service = TradingSessionService(db)
        logs = await service.get_session_logs(session_id, current_user.id, level, limit)
        return [TradingSessionLogResponse.from_orm(log) for log in logs]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve logs")


# Open Orders endpoints
@router.post("/orders", response_model=OpenOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_open_order(
    order_data: OpenOrderCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new open order.
    
    - **session_id**: Associated trading session (optional)
    - **order_type**: Order type (market, limit, stop, stop_limit)
    - **side**: Order side (buy, sell)
    - **symbol**: Trading pair symbol
    - **quantity**: Order quantity
    - **price**: Order price (for limit orders)
    - **stop_price**: Stop price (for stop orders)
    """
    try:
        service = OpenOrderService(db)
        order = await service.create_order(current_user.id, order_data)
        return OpenOrderResponse.from_orm(order)
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create order")


@router.get("/orders/{order_id}", response_model=OpenOrderResponse)
async def get_open_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get an open order by ID.
    """
    try:
        service = OpenOrderService(db)
        order = await service.get_order(order_id, current_user.id)
        return OpenOrderResponse.from_orm(order)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve order")


@router.get("/orders", response_model=List[OpenOrderResponse])
async def get_user_open_orders(
    session_id: Optional[int] = Query(None, description="Filter by session ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of orders to return"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get open orders for the current user.
    
    - **session_id**: Filter by session ID
    - **status**: Filter by order status
    - **limit**: Maximum number of orders (1-100)
    """
    try:
        service = OpenOrderService(db)
        orders = await service.get_user_orders(current_user.id, session_id, status, limit)
        return [OpenOrderResponse.from_orm(order) for order in orders]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve orders")


@router.put("/orders/{order_id}", response_model=OpenOrderResponse)
async def update_open_order(
    order_id: int,
    update_data: OpenOrderUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update an open order.
    
    Only pending orders can be updated.
    """
    try:
        service = OpenOrderService(db)
        order = await service.update_order(order_id, current_user.id, update_data)
        return OpenOrderResponse.from_orm(order)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order")


@router.delete("/orders/{order_id}", response_model=OpenOrderResponse)
async def cancel_open_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an open order.
    
    Only pending orders can be cancelled.
    """
    try:
        service = OpenOrderService(db)
        order = await service.cancel_order(order_id, current_user.id)
        return OpenOrderResponse.from_orm(order)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel order")


@router.post("/orders/bulk", response_model=dict)
async def bulk_create_orders(
    orders_data: List[OpenOrderCreate],
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple orders in bulk.
    
    Returns both successfully created orders and failed orders with error details.
    """
    try:
        service = OpenOrderService(db)
        created_orders, failed_orders = await service.bulk_create_orders(current_user.id, orders_data)
        
        return {
            "created_orders": [OpenOrderResponse.from_orm(order) for order in created_orders],
            "failed_orders": failed_orders,
            "summary": {
                "total_requested": len(orders_data),
                "successful": len(created_orders),
                "failed": len(failed_orders)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create orders")


# Health check endpoint
@router.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint for trading session service.
    """
    return {
        "status": "healthy",
        "service": "trading_session",
        "version": "1.0.0"
    }
