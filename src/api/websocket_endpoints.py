"""
WebSocket API endpoints for real-time communication.

This module provides WebSocket endpoints for real-time data streaming,
notifications, and bidirectional communication.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.websocket_manager import websocket_manager, MessageType, WebSocketMessage
from src.database.database import get_database
from src.core.security import get_current_user_websocket
from src.models.user import User
from src.services.asset_service import AssetService
from src.services.portfolio_service import PortfolioService
from src.services.alert_service import AlertService
from src.services.trading_session import TradingSessionService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = None,
    db: AsyncSession = Depends(get_database)
):
    """
    Main WebSocket endpoint for real-time communication.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID for this connection
        token: Optional authentication token
        db: Database session
    """
    connection_id = None
    
    try:
        # Authenticate user if token is provided
        if token:
            try:
                user = await get_current_user_websocket(token, db)
                if not user or user.id != user_id:
                    await websocket.close(code=1008, reason="Authentication failed")
                    return
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                await websocket.close(code=1008, reason="Authentication failed")
                return
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user_id)
        if not connection_id:
            return
        
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process the message
                await handle_client_message(connection_id, user_id, message_data, db)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                await websocket_manager._send_to_connection(
                    connection_id,
                    WebSocketMessage(
                        type=MessageType.ERROR,
                        data={"error": "Invalid JSON format"},
                        user_id=user_id
                    )
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket_manager._send_to_connection(
                    connection_id,
                    WebSocketMessage(
                        type=MessageType.ERROR,
                        data={"error": "Internal server error"},
                        user_id=user_id
                    )
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id)


async def handle_client_message(
    connection_id: str,
    user_id: int,
    message_data: Dict[str, Any],
    db: AsyncSession
):
    """
    Handle incoming messages from WebSocket clients.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        message_data: Message data from client
        db: Database session
    """
    try:
        message_type = message_data.get("type")
        data = message_data.get("data", {})
        
        if message_type == "subscribe":
            await handle_subscription(connection_id, user_id, data, db)
        elif message_type == "unsubscribe":
            await handle_unsubscription(connection_id, user_id, data)
        elif message_type == "get_portfolio":
            await handle_portfolio_request(connection_id, user_id, db)
        elif message_type == "get_alerts":
            await handle_alerts_request(connection_id, user_id, db)
        elif message_type == "get_price":
            await handle_price_request(connection_id, user_id, data, db)
        elif message_type == "get_trading_sessions":
            await handle_trading_sessions_request(connection_id, user_id, db)
        elif message_type == "get_orders":
            await handle_orders_request(connection_id, user_id, db)
        elif message_type == "heartbeat":
            await handle_heartbeat(connection_id, user_id)
        else:
            # Unknown message type
            await websocket_manager._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": f"Unknown message type: {message_type}"},
                    user_id=user_id
                )
            )
    
    except Exception as e:
        logger.error(f"Error handling client message: {e}")
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Failed to process message"},
                user_id=user_id
            )
        )


async def handle_subscription(
    connection_id: str,
    user_id: int,
    data: Dict[str, Any],
    db: AsyncSession
):
    """
    Handle subscription requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        data: Subscription data
        db: Database session
    """
    subscription_type = data.get("subscription_type")
    
    if subscription_type == "price_updates":
        # Subscribe to price updates for specific assets
        assets = data.get("assets", [])
        if not assets:
            # Get all assets if none specified
            asset_service = AssetService(db)
            all_assets = await asset_service.get_all_assets()
            assets = [asset.symbol for asset in all_assets]
        
        # Subscribe to each asset
        for asset_symbol in assets:
            subscription_key = f"price:{asset_symbol}"
            await websocket_manager.subscribe(connection_id, subscription_key)
    
    elif subscription_type == "alerts":
        # Subscribe to user alerts
        subscription_key = f"alerts:user:{user_id}"
        await websocket_manager.subscribe(connection_id, subscription_key)
    
    elif subscription_type == "portfolio":
        # Subscribe to portfolio updates
        subscription_key = f"portfolio:user:{user_id}"
        await websocket_manager.subscribe(connection_id, subscription_key)
    
    elif subscription_type == "trades":
        # Subscribe to trade notifications
        subscription_key = f"trades:user:{user_id}"
        await websocket_manager.subscribe(connection_id, subscription_key)
    
    elif subscription_type == "trading_sessions":
        # Subscribe to trading session updates
        subscription_key = f"trading_sessions:user:{user_id}"
        await websocket_manager.subscribe(connection_id, subscription_key)
    
    elif subscription_type == "orders":
        # Subscribe to order updates
        subscription_key = f"orders:user:{user_id}"
        await websocket_manager.subscribe(connection_id, subscription_key)
    
    elif subscription_type == "system":
        # Subscribe to system notifications
        subscription_key = f"system:user:{user_id}"
        await websocket_manager.subscribe(connection_id, subscription_key)
        
        # Also subscribe to global system notifications
        subscription_key = "system:all"
        await websocket_manager.subscribe(connection_id, subscription_key)
    
    else:
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.SUBSCRIPTION_ERROR,
                data={"error": f"Unknown subscription type: {subscription_type}"},
                user_id=user_id
            )
        )


async def handle_unsubscription(
    connection_id: str,
    user_id: int,
    data: Dict[str, Any]
):
    """
    Handle unsubscription requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        data: Unsubscription data
    """
    subscription_type = data.get("subscription_type")
    
    if subscription_type == "price_updates":
        assets = data.get("assets", [])
        for asset_symbol in assets:
            subscription_key = f"price:{asset_symbol}"
            await websocket_manager.unsubscribe(connection_id, subscription_key)
    
    elif subscription_type == "alerts":
        subscription_key = f"alerts:user:{user_id}"
        await websocket_manager.unsubscribe(connection_id, subscription_key)
    
    elif subscription_type == "portfolio":
        subscription_key = f"portfolio:user:{user_id}"
        await websocket_manager.unsubscribe(connection_id, subscription_key)
    
    elif subscription_type == "trades":
        subscription_key = f"trades:user:{user_id}"
        await websocket_manager.unsubscribe(connection_id, subscription_key)
    
    elif subscription_type == "trading_sessions":
        subscription_key = f"trading_sessions:user:{user_id}"
        await websocket_manager.unsubscribe(connection_id, subscription_key)
    
    elif subscription_type == "orders":
        subscription_key = f"orders:user:{user_id}"
        await websocket_manager.unsubscribe(connection_id, subscription_key)
    
    elif subscription_type == "system":
        subscription_key = f"system:user:{user_id}"
        await websocket_manager.unsubscribe(connection_id, subscription_key)
        subscription_key = "system:all"
        await websocket_manager.unsubscribe(connection_id, subscription_key)


async def handle_portfolio_request(
    connection_id: str,
    user_id: int,
    db: AsyncSession
):
    """
    Handle portfolio data requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        db: Database session
    """
    try:
        portfolio_service = PortfolioService(db)
        portfolio = await portfolio_service.get_portfolio_by_user_id(user_id)
        
        if portfolio:
            portfolio_data = await portfolio_service.get_portfolio_with_calculations(portfolio.id)
            
            await websocket_manager._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.PORTFOLIO_UPDATE,
                    data=portfolio_data,
                    user_id=user_id
                )
            )
        else:
            await websocket_manager._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Portfolio not found"},
                    user_id=user_id
                )
            )
    
    except Exception as e:
        logger.error(f"Error handling portfolio request: {e}")
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Failed to fetch portfolio data"},
                user_id=user_id
            )
        )


async def handle_alerts_request(
    connection_id: str,
    user_id: int,
    db: AsyncSession
):
    """
    Handle alerts data requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        db: Database session
    """
    try:
        alert_service = AlertService(db)
        alerts = await alert_service.get_alerts_by_user_id(user_id)
        
        alerts_data = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "asset_symbol": alert.asset_symbol,
                "trigger_value": float(alert.trigger_value),
                "is_active": alert.is_active,
                "created_at": alert.created_at.isoformat(),
                "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
                "message": alert.message
            }
            alerts_data.append(alert_dict)
        
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ALERT_NOTIFICATION,
                data={"alerts": alerts_data},
                user_id=user_id
            )
        )
    
    except Exception as e:
        logger.error(f"Error handling alerts request: {e}")
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Failed to fetch alerts data"},
                user_id=user_id
            )
        )


async def handle_price_request(
    connection_id: str,
    user_id: int,
    data: Dict[str, Any],
    db: AsyncSession
):
    """
    Handle price data requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        data: Request data
        db: Database session
    """
    try:
        asset_symbol = data.get("asset_symbol")
        if not asset_symbol:
            await websocket_manager._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Asset symbol is required"},
                    user_id=user_id
                )
            )
            return
        
        asset_service = AssetService(db)
        asset = await asset_service.get_asset_by_symbol(asset_symbol)
        
        if asset:
            price_data = {
                "asset_symbol": asset.symbol,
                "price": float(asset.current_price),
                "change_24h": float(asset.price_change_24h) if asset.price_change_24h else 0,
                "change_percentage_24h": float(asset.price_change_percentage_24h) if asset.price_change_percentage_24h else 0,
                "volume_24h": float(asset.volume_24h) if asset.volume_24h else 0,
                "market_cap": float(asset.market_cap) if asset.market_cap else 0,
                "updated_at": asset.updated_at.isoformat()
            }
            
            await websocket_manager._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.PRICE_UPDATE,
                    data=price_data,
                    user_id=user_id
                )
            )
        else:
            await websocket_manager._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": f"Asset not found: {asset_symbol}"},
                    user_id=user_id
                )
            )
    
    except Exception as e:
        logger.error(f"Error handling price request: {e}")
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Failed to fetch price data"},
                user_id=user_id
            )
        )


async def handle_trading_sessions_request(
    connection_id: str,
    user_id: int,
    db: AsyncSession
):
    """
    Handle trading sessions data requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        db: Database session
    """
    try:
        trading_session_service = TradingSessionService(db)
        sessions = await trading_session_service.get_user_sessions(user_id)
        
        sessions_data = []
        for session in sessions:
            session_dict = {
                "id": session.id,
                "name": session.name,
                "status": session.status,
                "strategy": session.strategy,
                "total_pnl": float(session.total_pnl) if session.total_pnl else 0,
                "unrealized_pnl": float(session.unrealized_pnl) if session.unrealized_pnl else 0,
                "realized_pnl": float(session.realized_pnl) if session.realized_pnl else 0,
                "created_at": session.created_at.isoformat(),
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None
            }
            sessions_data.append(session_dict)
        
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.TRADING_SESSION_UPDATE,
                data={"trading_sessions": sessions_data},
                user_id=user_id
            )
        )
    
    except Exception as e:
        logger.error(f"Error handling trading sessions request: {e}")
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Failed to fetch trading sessions data"},
                user_id=user_id
            )
        )


async def handle_orders_request(
    connection_id: str,
    user_id: int,
    db: AsyncSession
):
    """
    Handle orders data requests.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
        db: Database session
    """
    try:
        trading_session_service = TradingSessionService(db)
        orders = await trading_session_service.get_user_open_orders(user_id)
        
        orders_data = []
        for order in orders:
            order_dict = {
                "id": order.id,
                "trading_session_id": order.trading_session_id,
                "asset_symbol": order.asset_symbol,
                "order_type": order.order_type,
                "side": order.side,
                "quantity": float(order.quantity),
                "price": float(order.price) if order.price else None,
                "status": order.status,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            }
            orders_data.append(order_dict)
        
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ORDER_UPDATE,
                data={"orders": orders_data},
                user_id=user_id
            )
        )
    
    except Exception as e:
        logger.error(f"Error handling orders request: {e}")
        await websocket_manager._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Failed to fetch orders data"},
                user_id=user_id
            )
        )


async def handle_heartbeat(connection_id: str, user_id: int):
    """
    Handle heartbeat messages.
    
    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
    """
    # Update last heartbeat time
    if connection_id in websocket_manager._connections:
        websocket_manager._connections[connection_id].last_heartbeat = datetime.utcnow()
    
    # Send heartbeat response
    await websocket_manager._send_to_connection(
        connection_id,
        WebSocketMessage(
            type=MessageType.HEARTBEAT,
            data={"status": "pong"},
            user_id=user_id
        )
    )


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        WebSocket connection statistics
    """
    try:
        stats = await websocket_manager.get_connection_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket statistics")


@router.post("/ws/broadcast")
async def broadcast_system_notification(
    notification_data: Dict[str, Any],
    user_id: Optional[int] = None
):
    """
    Broadcast system notification to all users or a specific user.
    
    Args:
        notification_data: Notification data
        user_id: Optional user ID to send to specific user only
    """
    try:
        await websocket_manager.broadcast_system_notification(
            notification_data=notification_data,
            user_id=user_id
        )
        return {"status": "success", "message": "Notification broadcasted"}
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast notification")
