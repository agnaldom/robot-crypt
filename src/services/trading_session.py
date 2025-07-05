"""
Trading session service for Robot-Crypt application.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError

from src.models.trading_session import (
    TradingSession, TradingSessionLog, OpenOrder, 
    TradingSessionStatus, TradingStrategy, OrderStatus
)
from src.models.trade import Trade
from src.schemas.trading_session import (
    TradingSessionCreate, TradingSessionUpdate, TradingSessionLogCreate,
    OpenOrderCreate, OpenOrderUpdate, SessionControlRequest,
    SessionPerformanceMetrics, SessionRiskMetrics
)
from src.core.exceptions import NotFoundError, BadRequestError, UnauthorizedError
from src.core.websocket_manager import websocket_manager, MessageType, WebSocketMessage


logger = logging.getLogger(__name__)


class TradingSessionService:
    """Service for managing trading sessions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(self, user_id: int, session_data: TradingSessionCreate) -> TradingSession:
        """Create a new trading session."""
        # Validate strategy parameters
        if session_data.strategy_parameters:
            await self._validate_strategy_parameters(session_data.strategy, session_data.strategy_parameters)
        
        # Create session
        session = TradingSession(
            user_id=user_id,
            current_capital=session_data.initial_capital,
            **session_data.dict()
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Log session creation
        await self._log_session_event(
            session.id, 
            "INFO", 
            f"Trading session '{session.name}' created with strategy {session.strategy.value}",
            "session_created"
        )
        
        logger.info(f"Created trading session {session.id} for user {user_id}")
        
        # Broadcast session creation event
        await self._broadcast_session_event(
            session.id,
            user_id, 
            MessageType.TRADING_SESSION_UPDATE,
            {
                "action": "created",
                "session_id": session.id,
                "name": session.name,
                "strategy": session.strategy.value,
                "status": session.status.value,
                "initial_capital": float(session.initial_capital)
            }
        )
        
        return session
    
    async def get_session(self, session_id: int, user_id: int) -> TradingSession:
        """Get a trading session by ID."""
        query = select(TradingSession).where(
            and_(TradingSession.id == session_id, TradingSession.user_id == user_id)
        ).options(selectinload(TradingSession.trades))
        
        result = await self.db.execute(query)
        session = result.scalars().first()
        
        if not session:
            raise NotFoundError(f"Trading session {session_id} not found")
        
        return session
    
    async def get_user_sessions(
        self, 
        user_id: int, 
        status: Optional[TradingSessionStatus] = None,
        strategy: Optional[TradingStrategy] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TradingSession]:
        """Get trading sessions for a user."""
        query = select(TradingSession).where(TradingSession.user_id == user_id)
        
        if status:
            query = query.where(TradingSession.status == status)
        
        if strategy:
            query = query.where(TradingSession.strategy == strategy)
        
        query = query.order_by(TradingSession.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_session(
        self, 
        session_id: int, 
        user_id: int, 
        update_data: TradingSessionUpdate
    ) -> TradingSession:
        """Update a trading session."""
        session = await self.get_session(session_id, user_id)
        
        # Validate that session can be updated
        if session.status in [TradingSessionStatus.COMPLETED, TradingSessionStatus.TERMINATED]:
            raise BadRequestError("Cannot update completed or terminated session")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        # Validate strategy parameters if provided
        if 'strategy_parameters' in update_dict:
            await self._validate_strategy_parameters(session.strategy, update_dict['strategy_parameters'])
        
        for field, value in update_dict.items():
            setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        
        # Log update
        await self._log_session_event(
            session.id,
            "INFO",
            f"Trading session updated: {', '.join(update_dict.keys())}",
            "session_updated"
        )
        
        return session
    
    async def delete_session(self, session_id: int, user_id: int) -> bool:
        """Delete a trading session."""
        session = await self.get_session(session_id, user_id)
        
        # Only allow deletion of inactive sessions
        if session.status == TradingSessionStatus.ACTIVE:
            raise BadRequestError("Cannot delete active trading session")
        
        await self.db.delete(session)
        await self.db.commit()
        
        logger.info(f"Deleted trading session {session_id} for user {user_id}")
        return True
    
    async def control_session(
        self, 
        session_id: int, 
        user_id: int, 
        control_request: SessionControlRequest
    ) -> TradingSession:
        """Control trading session (start, pause, stop, resume)."""
        session = await self.get_session(session_id, user_id)
        
        action = control_request.action
        current_status = session.status
        
        # Validate state transitions
        valid_transitions = {
            TradingSessionStatus.CREATED: ['start'],
            TradingSessionStatus.ACTIVE: ['pause', 'stop'],
            TradingSessionStatus.PAUSED: ['resume', 'stop'],
            TradingSessionStatus.STOPPED: ['start'],
            TradingSessionStatus.COMPLETED: [],
            TradingSessionStatus.TERMINATED: []
        }
        
        if action not in valid_transitions.get(current_status, []):
            raise BadRequestError(f"Cannot {action} session in {current_status.value} state")
        
        # Apply action
        now = datetime.utcnow()
        
        if action == 'start':
            session.status = TradingSessionStatus.ACTIVE
            session.started_at = now
            await self._log_session_event(session.id, "INFO", "Trading session started", "session_started")
            
            # Broadcast session start event
            await self._broadcast_session_event(
                session.id,
                user_id,
                MessageType.TRADING_SESSION_START,
                {
                    "session_id": session.id,
                    "name": session.name,
                    "strategy": session.strategy.value,
                    "started_at": now.isoformat(),
                    "current_capital": float(session.current_capital)
                }
            )
        
        elif action == 'pause':
            session.status = TradingSessionStatus.PAUSED
            await self._log_session_event(session.id, "INFO", f"Trading session paused: {control_request.reason}", "session_paused")
            
            # Broadcast session pause event
            await self._broadcast_session_event(
                session.id,
                user_id,
                MessageType.TRADING_SESSION_PAUSE,
                {
                    "session_id": session.id,
                    "name": session.name,
                    "reason": control_request.reason,
                    "paused_at": now.isoformat(),
                    "current_capital": float(session.current_capital)
                }
            )
        
        elif action == 'resume':
            session.status = TradingSessionStatus.ACTIVE
            await self._log_session_event(session.id, "INFO", "Trading session resumed", "session_resumed")
            
            # Broadcast session resume event
            await self._broadcast_session_event(
                session.id,
                user_id,
                MessageType.TRADING_SESSION_RESUME,
                {
                    "session_id": session.id,
                    "name": session.name,
                    "resumed_at": now.isoformat(),
                    "current_capital": float(session.current_capital)
                }
            )
        
        elif action == 'stop':
            session.status = TradingSessionStatus.STOPPED
            session.ended_at = now
            cancelled_orders = await self._cancel_open_orders(session_id)
            await self._log_session_event(session.id, "INFO", f"Trading session stopped: {control_request.reason}", "session_stopped")
            
            # Broadcast session stop event
            await self._broadcast_session_event(
                session.id,
                user_id,
                MessageType.TRADING_SESSION_STOP,
                {
                    "session_id": session.id,
                    "name": session.name,
                    "reason": control_request.reason,
                    "stopped_at": now.isoformat(),
                    "ended_at": now.isoformat(),
                    "current_capital": float(session.current_capital),
                    "cancelled_orders": cancelled_orders
                }
            )
        
        session.updated_at = now
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_session_performance(self, session_id: int, user_id: int) -> SessionPerformanceMetrics:
        """Get performance metrics for a trading session."""
        session = await self.get_session(session_id, user_id)
        
        # Calculate additional metrics
        trades = await self._get_session_trades(session_id)
        
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for trade in trades:
            if trade.profit_loss > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        average_win = sum(t.profit_loss for t in trades if t.profit_loss > 0) / max(1, session.winning_trades)
        average_loss = sum(t.profit_loss for t in trades if t.profit_loss < 0) / max(1, session.losing_trades)
        
        return SessionPerformanceMetrics(
            session_id=session.id,
            total_trades=session.total_trades,
            winning_trades=session.winning_trades,
            losing_trades=session.losing_trades,
            win_rate=session.win_rate,
            profit_factor=session.profit_factor,
            roi=session.roi,
            total_profit_loss=session.total_profit_loss,
            total_fees=session.total_fees,
            max_profit=session.max_profit,
            max_loss=session.max_loss,
            current_drawdown=session.current_drawdown,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            average_win=average_win,
            average_loss=average_loss
        )
    
    async def get_session_risk_metrics(self, session_id: int, user_id: int) -> SessionRiskMetrics:
        """Get risk metrics for a trading session."""
        session = await self.get_session(session_id, user_id)
        
        # Calculate daily loss
        today = datetime.utcnow().date()
        daily_trades = await self._get_session_trades_by_date(session_id, today)
        daily_loss = sum(t.profit_loss for t in daily_trades if t.profit_loss < 0)
        
        return SessionRiskMetrics(
            session_id=session.id,
            current_capital=session.current_capital,
            max_drawdown=session.max_drawdown,
            current_drawdown=session.current_drawdown,
            risk_per_trade=session.risk_per_trade,
            max_position_size=session.max_position_size,
            max_daily_loss=session.max_daily_loss,
            daily_loss=abs(daily_loss)
        )
    
    async def get_session_logs(
        self, 
        session_id: int, 
        user_id: int, 
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[TradingSessionLog]:
        """Get logs for a trading session."""
        # Verify session ownership
        await self.get_session(session_id, user_id)
        
        query = select(TradingSessionLog).where(TradingSessionLog.session_id == session_id)
        
        if level:
            query = query.where(TradingSessionLog.level == level)
        
        query = query.order_by(TradingSessionLog.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _log_session_event(
        self, 
        session_id: int, 
        level: str, 
        message: str, 
        event_type: str = None,
        metadata: Dict[str, Any] = None
    ) -> TradingSessionLog:
        """Log a session event."""
        log = TradingSessionLog(
            session_id=session_id,
            level=level,
            message=message,
            event_type=event_type,
            metadata=metadata or {}
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    async def _validate_strategy_parameters(self, strategy: TradingStrategy, parameters: Dict[str, Any]) -> bool:
        """Validate strategy parameters."""
        # Define required parameters for each strategy
        required_params = {
            TradingStrategy.SCALPING: ['timeframe', 'profit_target', 'stop_loss'],
            TradingStrategy.SWING: ['timeframe', 'risk_reward_ratio'],
            TradingStrategy.MOMENTUM: ['momentum_period', 'volume_threshold'],
            TradingStrategy.MEAN_REVERSION: ['lookback_period', 'deviation_threshold'],
            TradingStrategy.ARBITRAGE: ['exchanges', 'min_spread'],
            TradingStrategy.CUSTOM: []  # Custom strategies have flexible parameters
        }
        
        if strategy in required_params:
            required = required_params[strategy]
            missing = [param for param in required if param not in parameters]
            
            if missing:
                raise BadRequestError(f"Missing required parameters for {strategy.value}: {missing}")
        
        return True
    
    async def _get_session_trades(self, session_id: int) -> List[Trade]:
        """Get all trades for a session."""
        query = select(Trade).where(Trade.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _get_session_trades_by_date(self, session_id: int, date: datetime.date) -> List[Trade]:
        """Get trades for a session on a specific date."""
        query = select(Trade).where(
            and_(
                Trade.session_id == session_id,
                func.date(Trade.created_at) == date
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _cancel_open_orders(self, session_id: int) -> int:
        """Cancel all open orders for a session."""
        query = update(OpenOrder).where(
            and_(
                OpenOrder.session_id == session_id,
                OpenOrder.status.in_([OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED])
            )
        ).values(
            status=OrderStatus.CANCELLED,
            updated_at=datetime.utcnow()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount
    
    async def _broadcast_session_event(
        self,
        session_id: int,
        user_id: int,
        message_type: MessageType,
        data: Dict[str, Any]
    ):
        """Broadcast session events via WebSocket."""
        try:
            # Broadcast to user-specific trading session subscription
            subscription_key = f"trading_sessions:user:{user_id}"
            message = WebSocketMessage(
                type=message_type,
                data=data,
                user_id=user_id
            )
            
            await websocket_manager._broadcast_to_subscribers(subscription_key, message)
            
            # Also send directly to user in case they don't have specific subscription
            await websocket_manager.send_to_user(user_id, message)
            
        except Exception as e:
            logger.error(f"Error broadcasting session event: {e}")


class OpenOrderService:
    """Service for managing open orders."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(self, user_id: int, order_data: OpenOrderCreate) -> OpenOrder:
        """Create a new open order."""
        # Validate session ownership if session_id is provided
        if order_data.session_id:
            await self._validate_session_ownership(order_data.session_id, user_id)
        
        # Create order
        order = OpenOrder(
            user_id=user_id,
            remaining_quantity=order_data.quantity,
            **order_data.dict()
        )
        
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info(f"Created order {order.id} for user {user_id}")
        
        # Broadcast order creation event
        await self._broadcast_order_event(
            user_id,
            MessageType.ORDER_UPDATE,
            {
                "action": "created",
                "order_id": order.id,
                "session_id": order.session_id,
                "symbol": order.symbol,
                "order_type": order.order_type.value,
                "side": order.side.value,
                "quantity": float(order.quantity),
                "price": float(order.price) if order.price else None,
                "status": order.status.value,
                "created_at": order.created_at.isoformat()
            }
        )
        
        return order
    
    async def get_order(self, order_id: int, user_id: int) -> OpenOrder:
        """Get an open order by ID."""
        query = select(OpenOrder).where(
            and_(OpenOrder.id == order_id, OpenOrder.user_id == user_id)
        )
        
        result = await self.db.execute(query)
        order = result.scalars().first()
        
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        
        return order
    
    async def get_user_orders(
        self, 
        user_id: int, 
        session_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 50
    ) -> List[OpenOrder]:
        """Get open orders for a user."""
        query = select(OpenOrder).where(OpenOrder.user_id == user_id)
        
        if session_id:
            query = query.where(OpenOrder.session_id == session_id)
        
        if status:
            query = query.where(OpenOrder.status == status)
        
        query = query.order_by(OpenOrder.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_order(self, order_id: int, user_id: int, update_data: OpenOrderUpdate) -> OpenOrder:
        """Update an open order."""
        order = await self.get_order(order_id, user_id)
        
        # Only allow updates to pending orders
        if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
            raise BadRequestError("Cannot update non-pending order")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(order, field, value)
        
        order.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(order)
        
        # Broadcast order update event
        await self._broadcast_order_event(
            user_id,
            MessageType.ORDER_UPDATE,
            {
                "action": "updated",
                "order_id": order.id,
                "session_id": order.session_id,
                "symbol": order.symbol,
                "status": order.status.value,
                "updated_fields": list(update_dict.keys()),
                "updated_at": order.updated_at.isoformat()
            }
        )
        
        return order
    
    async def cancel_order(self, order_id: int, user_id: int) -> OpenOrder:
        """Cancel an open order."""
        order = await self.get_order(order_id, user_id)
        
        if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
            raise BadRequestError("Cannot cancel non-pending order")
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # Broadcast order cancellation event
        await self._broadcast_order_event(
            user_id,
            MessageType.ORDER_CANCELLED,
            {
                "order_id": order.id,
                "session_id": order.session_id,
                "symbol": order.symbol,
                "cancelled_at": order.updated_at.isoformat()
            }
        )
        
        return order
    
    async def bulk_create_orders(self, user_id: int, orders_data: List[OpenOrderCreate]) -> Tuple[List[OpenOrder], List[Dict[str, Any]]]:
        """Create multiple orders in bulk."""
        created_orders = []
        failed_orders = []
        
        for i, order_data in enumerate(orders_data):
            try:
                order = await self.create_order(user_id, order_data)
                created_orders.append(order)
            except Exception as e:
                failed_orders.append({
                    'index': i,
                    'order_data': order_data.dict(),
                    'error': str(e)
                })
        
        return created_orders, failed_orders
    
    async def _validate_session_ownership(self, session_id: int, user_id: int) -> bool:
        """Validate that the user owns the session."""
        query = select(TradingSession).where(
            and_(TradingSession.id == session_id, TradingSession.user_id == user_id)
        )
        
        result = await self.db.execute(query)
        session = result.scalars().first()
        
        if not session:
            raise UnauthorizedError("Session not found or access denied")
        
        return True
    
    async def _broadcast_order_event(
        self,
        user_id: int,
        message_type: MessageType,
        data: Dict[str, Any]
    ):
        """Broadcast order events via WebSocket."""
        try:
            # Broadcast to user-specific orders subscription
            subscription_key = f"orders:user:{user_id}"
            message = WebSocketMessage(
                type=message_type,
                data=data,
                user_id=user_id
            )
            
            await websocket_manager._broadcast_to_subscribers(subscription_key, message)
            
            # Also send directly to user
            await websocket_manager.send_to_user(user_id, message)
            
        except Exception as e:
            logger.error(f"Error broadcasting order event: {e}")
