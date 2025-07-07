#!/usr/bin/env python3
"""
Telegram Service - Simplified interface for Telegram notifications
Provides easy-to-use functions for common notification patterns
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Import the existing TelegramNotifier
try:
    from src.notifications.telegram_notifier import TelegramNotifier
except ImportError:
    TelegramNotifier = None

logger = logging.getLogger(__name__)

class TelegramService:
    """
    Simplified Telegram service for easy integration with trading systems
    """
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize the Telegram service
        
        Args:
            bot_token (str): Telegram bot token (defaults to env var TELEGRAM_BOT_TOKEN)
            chat_id (str): Telegram chat ID (defaults to env var TELEGRAM_CHAT_ID)
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.logger = logging.getLogger(__name__)
        
        # Additional chat IDs for different notification types
        self.audit_chat_id = os.getenv("TELEGRAM_AUDIT_CHAT_ID", self.chat_id)
        self.alerts_chat_id = os.getenv("TELEGRAM_ALERTS_CHAT_ID", self.chat_id)
        self.reports_chat_id = os.getenv("TELEGRAM_REPORTS_CHAT_ID", self.chat_id)
        
        # Initialize the underlying notifier
        self.notifier = None
        if TelegramNotifier and self.bot_token and self.chat_id:
            try:
                self.notifier = TelegramNotifier(self.bot_token, self.chat_id)
                self.logger.info("Telegram service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram notifier: {e}")
        else:
            self.logger.warning("Telegram service not available - missing bot token or chat ID")
    
    def is_available(self) -> bool:
        """Check if Telegram service is available"""
        return self.notifier is not None
    
    async def send_message(self, message: str, chat_id: str = None) -> bool:
        """
        Send a plain text message
        
        Args:
            message (str): Message text
            chat_id (str): Optional chat ID (defaults to main chat)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            # Use provided chat_id or default
            target_chat = chat_id or self.chat_id
            
            # Temporarily change the notifier's chat_id if needed
            original_chat_id = self.notifier.chat_id
            if target_chat != original_chat_id:
                self.notifier.chat_id = target_chat
            
            result = self.notifier.send_message(message)
            
            # Restore original chat_id
            self.notifier.chat_id = original_chat_id
            
            return result
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def send_trade_notification(self, trade_data: Dict[str, Any]) -> bool:
        """
        Send a trade notification with rich formatting
        
        Args:
            trade_data (dict): Trade information containing:
                - symbol: Trading pair
                - side: BUY/SELL
                - price: Trade price
                - quantity: Trade quantity
                - profit_loss: P&L percentage (optional)
                - strategy: Strategy name (optional)
                - reason: Trade reason (optional)
                
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            # Prepare title
            side = trade_data.get('side', '').upper()
            symbol = trade_data.get('symbol', 'N/A')
            title = f"{side} de {symbol}"
            
            # Prepare detailed message
            details = []
            if 'reason' in trade_data:
                details.append(f"Motivo: {trade_data['reason']}")
            if 'strategy' in trade_data:
                details.append(f"Estratégia: {trade_data['strategy']}")
            
            detail_message = "\n".join(details) if details else None
            
            return self.notifier.notify_trade(title, detail_message, trade_data)
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
            return False
    
    async def send_error_alert(self, error_message: str, component: str = None, 
                             traceback: str = None) -> bool:
        """
        Send an error alert notification
        
        Args:
            error_message (str): Error description
            component (str): System component where error occurred
            traceback (str): Error traceback (optional)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            return self.notifier.notify_error(error_message, traceback, component)
        except Exception as e:
            self.logger.error(f"Error sending error alert: {e}")
            return False
    
    async def send_risk_alert(self, alert_type: str, message: str, 
                            symbol: str = None, severity: str = "medium") -> bool:
        """
        Send a risk management alert
        
        Args:
            alert_type (str): Type of risk alert
            message (str): Alert message
            symbol (str): Trading pair (optional)
            severity (str): Alert severity (low/medium/high)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            # Format severity emoji
            severity_emoji = {
                "low": "🟡",
                "medium": "🟠", 
                "high": "🔴"
            }.get(severity.lower(), "⚠️")
            
            # Format message
            formatted_message = f"{severity_emoji} ALERTA DE RISCO: {alert_type.upper()}\n\n{message}"
            if symbol:
                formatted_message += f"\n\nPar: {symbol}"
            
            return await self.send_message(formatted_message, self.alerts_chat_id)
        except Exception as e:
            self.logger.error(f"Error sending risk alert: {e}")
            return False
    
    async def send_performance_summary(self, performance_data: Dict[str, Any]) -> bool:
        """
        Send a performance summary notification
        
        Args:
            performance_data (dict): Performance metrics including:
                - initial_capital: Starting capital
                - current_capital: Current capital
                - total_trades: Total number of trades
                - profit_trades: Number of profitable trades
                - loss_trades: Number of losing trades
                - additional_metrics: Other metrics (optional)
                
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            return self.notifier.notify_portfolio_summary(
                initial_capital=performance_data.get('initial_capital', 0),
                current_capital=performance_data.get('current_capital', 0),
                total_trades=performance_data.get('total_trades', 0),
                profit_trades=performance_data.get('profit_trades', 0),
                loss_trades=performance_data.get('loss_trades', 0),
                additional_metrics=performance_data.get('additional_metrics')
            )
        except Exception as e:
            self.logger.error(f"Error sending performance summary: {e}")
            return False
    
    async def send_market_alert(self, symbol: str, alert_type: str, 
                              message: str, market_data: Dict[str, Any] = None) -> bool:
        """
        Send a market condition alert
        
        Args:
            symbol (str): Trading pair
            alert_type (str): Type of market alert (bullish/bearish/volatility/etc)
            message (str): Alert message
            market_data (dict): Additional market data (optional)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            return self.notifier.notify_market_alert(symbol, alert_type, message, market_data)
        except Exception as e:
            self.logger.error(f"Error sending market alert: {e}")
            return False
    
    async def send_analysis_report(self, symbol: str, analysis_type: str, 
                                 details: str, chart_data: Dict[str, Any] = None,
                                 timeframe: str = None) -> bool:
        """
        Send a market analysis report
        
        Args:
            symbol (str): Trading pair
            analysis_type (str): Type of analysis
            details (str): Analysis details
            chart_data (dict): Chart and indicator data (optional)
            timeframe (str): Analysis timeframe (optional)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            return self.notifier.notify_analysis(symbol, analysis_type, details, chart_data, timeframe)
        except Exception as e:
            self.logger.error(f"Error sending analysis report: {e}")
            return False
    
    async def send_system_status(self, status_message: str, details: Dict[str, Any] = None,
                               status_type: str = "info") -> bool:
        """
        Send a system status notification
        
        Args:
            status_message (str): Status message
            details (dict): Additional status details (optional)
            status_type (str): Type of status (info/warning/success/error)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            return self.notifier.notify_status(status_message, details, status_type)
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False
    
    async def send_audit_log(self, action: str, details: Dict[str, Any], 
                           user_id: str = None) -> bool:
        """
        Send an audit log notification
        
        Args:
            action (str): Action performed
            details (dict): Action details
            user_id (str): User who performed the action (optional)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            # Format audit message
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            message = f"📝 AUDIT LOG - {timestamp}\n\n"
            message += f"Action: {action}\n"
            if user_id:
                message += f"User: {user_id}\n"
            
            # Add details
            if details:
                message += "\nDetails:\n"
                for key, value in details.items():
                    message += f"• {key}: {value}\n"
            
            return await self.send_message(message, self.audit_chat_id)
        except Exception as e:
            self.logger.error(f"Error sending audit log: {e}")
            return False
    
    async def send_document(self, file_path: str, caption: str = None, 
                          chat_id: str = None) -> bool:
        """
        Send a document (PDF, CSV, etc.) to Telegram
        
        Args:
            file_path (str): Path to the file
            caption (str): File caption (optional)
            chat_id (str): Target chat ID (optional)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            import requests
            
            # Prepare file upload
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
            
            target_chat = chat_id or self.chat_id
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': target_chat,
                    'caption': caption or f"File: {file_path.name}"
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
                
                self.logger.info(f"Document sent successfully: {file_path.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending document: {e}")
            return False
    
    async def send_confirmation_request(self, message: str, action_id: str,
                                      timeout_seconds: int = 300) -> bool:
        """
        Send a confirmation request with action buttons
        
        Args:
            message (str): Confirmation message
            action_id (str): Unique identifier for the action
            timeout_seconds (int): Timeout for the confirmation (default: 5 minutes)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            # Prepare trade info for confirmation
            trade_info = {
                'id': action_id,
                'message': message,
                'timeout': timeout_seconds
            }
            
            return self.notifier.send_trade_confirmation(trade_info, require_confirmation=True)
        except Exception as e:
            self.logger.error(f"Error sending confirmation request: {e}")
            return False
    
    async def send_emergency_alert(self, alert_message: str, 
                                 additional_info: Dict[str, Any] = None) -> bool:
        """
        Send an emergency alert to all configured chats
        
        Args:
            alert_message (str): Emergency alert message
            additional_info (dict): Additional emergency information (optional)
            
        Returns:
            bool: True if sent successfully to at least one chat
        """
        if not self.is_available():
            self.logger.warning("Telegram service not available")
            return False
        
        try:
            # Format emergency message
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            message = f"🚨 EMERGENCY ALERT - {timestamp}\n\n"
            message += f"⚠️ {alert_message}\n"
            
            if additional_info:
                message += "\n📊 Additional Information:\n"
                for key, value in additional_info.items():
                    message += f"• {key}: {value}\n"
            
            message += "\n🔧 Immediate action may be required!"
            
            # Send to all configured chats
            chats = [self.chat_id, self.alerts_chat_id, self.audit_chat_id]
            success_count = 0
            
            for chat in set(chats):  # Remove duplicates
                if chat:
                    if await self.send_message(message, chat):
                        success_count += 1
            
            return success_count > 0
        except Exception as e:
            self.logger.error(f"Error sending emergency alert: {e}")
            return False

# Singleton instance for easy access
_telegram_service = None

def get_telegram_service() -> TelegramService:
    """Get the singleton Telegram service instance"""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service

# Convenience functions for direct usage
async def send_trade_report(trade_data: Dict[str, Any]) -> bool:
    """Send a trade report notification"""
    service = get_telegram_service()
    return await service.send_trade_notification(trade_data)

async def send_risk_alert(alert_type: str, message: str, symbol: str = None, 
                        severity: str = "medium") -> bool:
    """Send a risk management alert"""
    service = get_telegram_service()
    return await service.send_risk_alert(alert_type, message, symbol, severity)

async def send_performance_summary(performance_data: Dict[str, Any]) -> bool:
    """Send a performance summary report"""
    service = get_telegram_service()
    return await service.send_performance_summary(performance_data)

async def send_system_alert(message: str, severity: str = "info") -> bool:
    """Send a system status alert"""
    service = get_telegram_service()
    return await service.send_system_status(message, status_type=severity)

async def send_emergency_stop(reason: str, additional_info: Dict[str, Any] = None) -> bool:
    """Send an emergency stop notification"""
    service = get_telegram_service()
    return await service.send_emergency_alert(f"EMERGENCY STOP TRIGGERED: {reason}", additional_info)

async def send_audit_notification(action: str, details: Dict[str, Any], 
                                user_id: str = None) -> bool:
    """Send an audit trail notification"""
    service = get_telegram_service()
    return await service.send_audit_log(action, details, user_id)
