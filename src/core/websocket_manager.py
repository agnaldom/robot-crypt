"""
WebSocket Manager for Real-time Data Streaming and Notifications.

This module provides WebSocket connection management and broadcasting capabilities
for real-time updates including price data, alerts, and portfolio changes.
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    PRICE_UPDATE = "price_update"
    ALERT_NOTIFICATION = "alert_notification"
    PORTFOLIO_UPDATE = "portfolio_update"
    TRADE_NOTIFICATION = "trade_notification"
    SYSTEM_NOTIFICATION = "system_notification"
    TRADING_SESSION_UPDATE = "trading_session_update"
    TRADING_SESSION_START = "trading_session_start"
    TRADING_SESSION_STOP = "trading_session_stop"
    TRADING_SESSION_PAUSE = "trading_session_pause"
    TRADING_SESSION_RESUME = "trading_session_resume"
    ORDER_UPDATE = "order_update"
    ORDER_EXECUTED = "order_executed"
    ORDER_CANCELLED = "order_cancelled"
    PERFORMANCE_UPDATE = "performance_update"
    RISK_ALERT = "risk_alert"
    HEARTBEAT = "heartbeat"
    SUBSCRIPTION_SUCCESS = "subscription_success"
    SUBSCRIPTION_ERROR = "subscription_error"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = None
    user_id: Optional[int] = None
    message_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "message_id": self.message_id
        }


@dataclass
class ConnectionInfo:
    """WebSocket connection information."""
    websocket: WebSocket
    user_id: int
    subscriptions: Set[str]
    connected_at: datetime
    last_heartbeat: datetime
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Active connections: connection_id -> ConnectionInfo
        self._connections: Dict[str, ConnectionInfo] = {}
        
        # User connections: user_id -> Set[connection_id]
        self._user_connections: Dict[int, Set[str]] = {}
        
        # Subscription mapping: subscription_key -> Set[connection_id]
        self._subscriptions: Dict[str, Set[str]] = {}
        
        # Connection lock for thread safety
        self._connection_lock = asyncio.Lock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # seconds
        self.max_connections_per_user = 5
        
        logger.info("WebSocket Manager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: The user ID for this connection
            
        Returns:
            Connection ID string
        """
        connection_id = str(uuid.uuid4())
        
        async with self._connection_lock:
            # Check connection limit per user
            if user_id in self._user_connections:
                if len(self._user_connections[user_id]) >= self.max_connections_per_user:
                    logger.warning(f"User {user_id} exceeded connection limit")
                    await websocket.close(code=1008, reason="Connection limit exceeded")
                    return None
            
            # Accept the connection
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                subscriptions=set(),
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            )
            
            # Store connection
            self._connections[connection_id] = connection_info
            
            # Add to user connections
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)
            
            logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
            
            # Send connection success message
            await self._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.SUBSCRIPTION_SUCCESS,
                    data={"message": "Connected successfully", "connection_id": connection_id},
                    user_id=user_id
                )
            )
            
            # Start background tasks if not already running
            if not self._cleanup_task:
                self._cleanup_task = asyncio.create_task(self._cleanup_connections())
            if not self._heartbeat_task:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: The connection ID to disconnect
        """
        async with self._connection_lock:
            if connection_id not in self._connections:
                return
            
            connection_info = self._connections[connection_id]
            user_id = connection_info.user_id
            
            # Remove from subscriptions
            for subscription_key in connection_info.subscriptions:
                if subscription_key in self._subscriptions:
                    self._subscriptions[subscription_key].discard(connection_id)
                    if not self._subscriptions[subscription_key]:
                        del self._subscriptions[subscription_key]
            
            # Remove from user connections
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(connection_id)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
            
            # Close websocket if still connected
            if connection_info.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await connection_info.websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket {connection_id}: {e}")
            
            # Remove connection
            del self._connections[connection_id]
            
            logger.info(f"WebSocket connection closed: {connection_id} for user {user_id}")
    
    async def subscribe(self, connection_id: str, subscription_key: str) -> bool:
        """
        Subscribe a connection to a specific data stream.
        
        Args:
            connection_id: The connection ID
            subscription_key: The subscription key (e.g., "price:BTC", "alerts:user:123")
            
        Returns:
            True if subscription was successful, False otherwise
        """
        async with self._connection_lock:
            if connection_id not in self._connections:
                return False
            
            connection_info = self._connections[connection_id]
            
            # Add to connection subscriptions
            connection_info.subscriptions.add(subscription_key)
            
            # Add to subscription mapping
            if subscription_key not in self._subscriptions:
                self._subscriptions[subscription_key] = set()
            self._subscriptions[subscription_key].add(connection_id)
            
            logger.info(f"Connection {connection_id} subscribed to {subscription_key}")
            
            # Send subscription success
            await self._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.SUBSCRIPTION_SUCCESS,
                    data={"subscription": subscription_key},
                    user_id=connection_info.user_id
                )
            )
            
            return True
    
    async def unsubscribe(self, connection_id: str, subscription_key: str) -> bool:
        """
        Unsubscribe a connection from a specific data stream.
        
        Args:
            connection_id: The connection ID
            subscription_key: The subscription key
            
        Returns:
            True if unsubscription was successful, False otherwise
        """
        async with self._connection_lock:
            if connection_id not in self._connections:
                return False
            
            connection_info = self._connections[connection_id]
            
            # Remove from connection subscriptions
            connection_info.subscriptions.discard(subscription_key)
            
            # Remove from subscription mapping
            if subscription_key in self._subscriptions:
                self._subscriptions[subscription_key].discard(connection_id)
                if not self._subscriptions[subscription_key]:
                    del self._subscriptions[subscription_key]
            
            logger.info(f"Connection {connection_id} unsubscribed from {subscription_key}")
            return True
    
    async def broadcast_price_update(self, asset_symbol: str, price_data: Dict[str, Any]):
        """
        Broadcast price update to all subscribers.
        
        Args:
            asset_symbol: The asset symbol (e.g., "BTC", "ETH")
            price_data: Price data dictionary
        """
        subscription_key = f"price:{asset_symbol}"
        
        message = WebSocketMessage(
            type=MessageType.PRICE_UPDATE,
            data={
                "asset_symbol": asset_symbol,
                "price": price_data.get("price"),
                "change_24h": price_data.get("change_24h"),
                "change_percentage_24h": price_data.get("change_percentage_24h"),
                "volume_24h": price_data.get("volume_24h"),
                "market_cap": price_data.get("market_cap"),
                "updated_at": price_data.get("updated_at", datetime.utcnow().isoformat())
            }
        )
        
        await self._broadcast_to_subscribers(subscription_key, message)
    
    async def broadcast_alert_notification(self, user_id: int, alert_data: Dict[str, Any]):
        """
        Broadcast alert notification to a specific user.
        
        Args:
            user_id: The user ID
            alert_data: Alert data dictionary
        """
        subscription_key = f"alerts:user:{user_id}"
        
        message = WebSocketMessage(
            type=MessageType.ALERT_NOTIFICATION,
            data={
                "alert_id": alert_data.get("id"),
                "alert_type": alert_data.get("alert_type"),
                "message": alert_data.get("message"),
                "asset_symbol": alert_data.get("asset_symbol"),
                "trigger_value": alert_data.get("trigger_value"),
                "current_value": alert_data.get("current_value"),
                "triggered_at": alert_data.get("triggered_at", datetime.utcnow().isoformat()),
                "priority": alert_data.get("priority", "normal")
            },
            user_id=user_id
        )
        
        await self._broadcast_to_subscribers(subscription_key, message)
    
    async def broadcast_portfolio_update(self, user_id: int, portfolio_data: Dict[str, Any]):
        """
        Broadcast portfolio update to a specific user.
        
        Args:
            user_id: The user ID
            portfolio_data: Portfolio data dictionary
        """
        subscription_key = f"portfolio:user:{user_id}"
        
        message = WebSocketMessage(
            type=MessageType.PORTFOLIO_UPDATE,
            data={
                "total_value": portfolio_data.get("total_value"),
                "total_profit_loss": portfolio_data.get("total_profit_loss"),
                "profit_loss_percentage": portfolio_data.get("profit_loss_percentage"),
                "assets": portfolio_data.get("assets", []),
                "updated_at": portfolio_data.get("updated_at", datetime.utcnow().isoformat())
            },
            user_id=user_id
        )
        
        await self._broadcast_to_subscribers(subscription_key, message)
    
    async def broadcast_trade_notification(self, user_id: int, trade_data: Dict[str, Any]):
        """
        Broadcast trade notification to a specific user.
        
        Args:
            user_id: The user ID
            trade_data: Trade data dictionary
        """
        subscription_key = f"trades:user:{user_id}"
        
        message = WebSocketMessage(
            type=MessageType.TRADE_NOTIFICATION,
            data={
                "trade_id": trade_data.get("id"),
                "asset_symbol": trade_data.get("asset_symbol"),
                "trade_type": trade_data.get("trade_type"),
                "quantity": trade_data.get("quantity"),
                "price": trade_data.get("price"),
                "total_value": trade_data.get("total_value"),
                "status": trade_data.get("status"),
                "executed_at": trade_data.get("executed_at", datetime.utcnow().isoformat())
            },
            user_id=user_id
        )
        
        await self._broadcast_to_subscribers(subscription_key, message)
    
    async def broadcast_system_notification(self, notification_data: Dict[str, Any], user_id: Optional[int] = None):
        """
        Broadcast system notification to all users or a specific user.
        
        Args:
            notification_data: Notification data dictionary
            user_id: Optional user ID to send to specific user only
        """
        if user_id:
            subscription_key = f"system:user:{user_id}"
        else:
            subscription_key = "system:all"
        
        message = WebSocketMessage(
            type=MessageType.SYSTEM_NOTIFICATION,
            data={
                "title": notification_data.get("title"),
                "message": notification_data.get("message"),
                "type": notification_data.get("type", "info"),
                "priority": notification_data.get("priority", "normal"),
                "action_url": notification_data.get("action_url"),
                "expires_at": notification_data.get("expires_at")
            },
            user_id=user_id
        )
        
        await self._broadcast_to_subscribers(subscription_key, message)
    
    async def send_to_user(self, user_id: int, message: WebSocketMessage):
        """
        Send a message to all connections of a specific user.
        
        Args:
            user_id: The user ID
            message: The message to send
        """
        if user_id not in self._user_connections:
            return
        
        message.user_id = user_id
        connection_ids = self._user_connections[user_id].copy()
        
        for connection_id in connection_ids:
            await self._send_to_connection(connection_id, message)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket connection statistics.
        
        Returns:
            Dictionary containing connection statistics
        """
        async with self._connection_lock:
            total_connections = len(self._connections)
            unique_users = len(self._user_connections)
            total_subscriptions = sum(len(subs) for subs in self._subscriptions.values())
            
            # Connection per user stats
            connections_per_user = {}
            for user_id, connections in self._user_connections.items():
                connections_per_user[user_id] = len(connections)
            
            # Subscription stats
            subscription_stats = {}
            for key, connections in self._subscriptions.items():
                subscription_stats[key] = len(connections)
            
            return {
                "total_connections": total_connections,
                "unique_users": unique_users,
                "total_subscriptions": total_subscriptions,
                "connections_per_user": connections_per_user,
                "subscription_stats": subscription_stats,
                "uptime": (datetime.utcnow() - self._connections[next(iter(self._connections))].connected_at).total_seconds() if self._connections else 0
            }
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: The connection ID
            message: The message to send
        """
        if connection_id not in self._connections:
            return
        
        connection_info = self._connections[connection_id]
        
        if connection_info.websocket.client_state != WebSocketState.CONNECTED:
            await self.disconnect(connection_id)
            return
        
        try:
            await connection_info.websocket.send_text(json.dumps(message.to_dict()))
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def _broadcast_to_subscribers(self, subscription_key: str, message: WebSocketMessage):
        """
        Broadcast a message to all subscribers of a specific subscription.
        
        Args:
            subscription_key: The subscription key
            message: The message to broadcast
        """
        if subscription_key not in self._subscriptions:
            return
        
        connection_ids = self._subscriptions[subscription_key].copy()
        
        for connection_id in connection_ids:
            await self._send_to_connection(connection_id, message)
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeat messages."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                current_time = datetime.utcnow()
                heartbeat_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={"timestamp": current_time.isoformat()}
                )
                
                # Send heartbeat to all connections
                connection_ids = list(self._connections.keys())
                for connection_id in connection_ids:
                    await self._send_to_connection(connection_id, heartbeat_message)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                break
    
    async def _cleanup_connections(self):
        """Background task to cleanup stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.utcnow()
                stale_connections = []
                
                for connection_id, connection_info in self._connections.items():
                    # Check if connection is stale
                    if (current_time - connection_info.last_heartbeat).total_seconds() > self.connection_timeout:
                        stale_connections.append(connection_id)
                
                # Remove stale connections
                for connection_id in stale_connections:
                    logger.info(f"Removing stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                break
    
    async def shutdown(self):
        """Shutdown the WebSocket manager and close all connections."""
        logger.info("Shutting down WebSocket Manager")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        # Close all connections
        connection_ids = list(self._connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)
        
        logger.info("WebSocket Manager shutdown completed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
