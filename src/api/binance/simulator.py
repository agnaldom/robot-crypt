"""
Binance API simulator for testing and development.
"""
import time
import uuid
import random
import json
import copy
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal, ROUND_DOWN

from src.core.logging_setup import logger


class BinanceSimulatorException(Exception):
    """Exception raised for Binance simulator errors."""
    pass


class BinanceSimulator:
    """
    Simulated Binance API client for testing without real API calls.
    The interface mirrors the actual BinanceClient but uses local data and simulation.
    """
    
    def __init__(self, initial_balance: Dict[str, float] = None):
        """
        Initialize Binance simulator.
        
        Args:
            initial_balance (Dict[str, float], optional): Initial wallet balance.
                Defaults to {"USDT": 10000.0, "BTC": 0.1, "ETH": 1.0}.
        """
        self.balances = initial_balance or {"USDT": 10000.0, "BTC": 0.1, "ETH": 1.0}
        self.orders = []
        self.open_orders = []
        self.order_id_counter = 1
        
        # Price data (updated through set_price_data or add_candlestick_data)
        self.price_data = {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 400.0
        }
        
        # Candlestick data
        self.klines_data = {}
        
        # Account trade history
        self.trade_history = []
        
        logger.info("Binance simulator initialized with balances: %s", self.balances)
    
    def set_price_data(self, symbol: str, price: float):
        """
        Set price for a symbol.
        
        Args:
            symbol (str): Symbol
            price (float): Price
        """
        self.price_data[symbol] = price
        logger.debug(f"Set {symbol} price to {price}")
    
    def add_candlestick_data(
        self, 
        symbol: str, 
        interval: str, 
        open_time: int,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        close_time: Optional[int] = None
    ):
        """
        Add candlestick data.
        
        Args:
            symbol (str): Symbol
            interval (str): Interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            open_time (int): Open time in milliseconds
            open_price (float): Open price
            high_price (float): High price
            low_price (float): Low price
            close_price (float): Close price
            volume (float): Volume
            close_time (int, optional): Close time in milliseconds. Defaults to open_time + interval.
        """
        if symbol not in self.klines_data:
            self.klines_data[symbol] = {}
        
        if interval not in self.klines_data[symbol]:
            self.klines_data[symbol][interval] = []
        
        # Calculate close time if not provided
        if close_time is None:
            # Convert interval to milliseconds
            interval_ms = self._interval_to_milliseconds(interval)
            close_time = open_time + interval_ms - 1
        
        kline = [
            open_time,              # Open time
            str(open_price),        # Open
            str(high_price),        # High
            str(low_price),         # Low
            str(close_price),       # Close
            str(volume),            # Volume
            close_time,             # Close time
            str(volume * close_price),  # Quote asset volume
            10,                     # Number of trades
            str(volume * 0.5),      # Taker buy base asset volume
            str(volume * 0.5 * close_price),  # Taker buy quote asset volume
            "0"                     # Ignore
        ]
        
        self.klines_data[symbol][interval].append(kline)
        # Also update current price
        self.price_data[symbol] = close_price
    
    def _interval_to_milliseconds(self, interval: str) -> int:
        """
        Convert interval string to milliseconds.
        
        Args:
            interval (str): Interval string (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        
        Returns:
            int: Milliseconds
        
        Raises:
            BinanceSimulatorException: If interval is invalid
        """
        seconds_per_unit = {
            "m": 60,
            "h": 60 * 60,
            "d": 24 * 60 * 60,
            "w": 7 * 24 * 60 * 60,
            "M": 30 * 24 * 60 * 60
        }
        
        try:
            unit = interval[-1]
            if unit not in seconds_per_unit:
                raise ValueError()
            
            num = int(interval[:-1])
            return num * seconds_per_unit[unit] * 1000
        
        except (ValueError, IndexError):
            raise BinanceSimulatorException(f"Invalid interval: {interval}")
    
    def _round_step_size(self, quantity: float, step_size: float) -> float:
        """
        Round quantity to step size.
        
        Args:
            quantity (float): Quantity
            step_size (float): Step size
        
        Returns:
            float: Rounded quantity
        """
        precision = len(str(step_size).split('.')[-1])
        return float(Decimal(str(quantity)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))
    
    def _update_balance(self, asset: str, amount: float):
        """
        Update balance for an asset.
        
        Args:
            asset (str): Asset
            amount (float): Amount to add (positive) or subtract (negative)
        
        Raises:
            BinanceSimulatorException: If insufficient balance
        """
        if asset not in self.balances:
            self.balances[asset] = 0.0
        
        new_balance = self.balances[asset] + amount
        
        if new_balance < 0:
            raise BinanceSimulatorException(f"Insufficient {asset} balance")
        
        self.balances[asset] = new_balance
        logger.debug(f"Updated {asset} balance to {new_balance}")
    
    def _execute_order(self, order: Dict[str, Any]):
        """
        Execute an order.
        
        Args:
            order (Dict[str, Any]): Order to execute
        
        Returns:
            Dict[str, Any]: Updated order
        """
        symbol = order["symbol"]
        side = order["side"]
        order_type = order["type"]
        quantity = float(order["origQty"])
        
        # Extract base and quote assets from symbol
        base_asset = symbol[:-4] if symbol.endswith("USDT") else symbol[:3]
        quote_asset = symbol[-4:] if symbol.endswith("USDT") else symbol[3:]
        
        # Set execution price
        if order_type == "MARKET":
            # Use current price for market orders
            execution_price = self.price_data.get(symbol, 0)
        else:
            # Use order price for limit orders
            execution_price = float(order["price"])
        
        total_value = quantity * execution_price
        
        # Update balances based on order side
        if side == "BUY":
            self._update_balance(base_asset, quantity)
            self._update_balance(quote_asset, -total_value)
        else:  # SELL
            self._update_balance(base_asset, -quantity)
            self._update_balance(quote_asset, total_value)
        
        # Update order status
        order["status"] = "FILLED"
        order["executedQty"] = str(quantity)
        order["cummulativeQuoteQty"] = str(total_value)
        
        # Add to trade history
        trade = {
            "id": len(self.trade_history) + 1,
            "orderId": order["orderId"],
            "symbol": symbol,
            "price": str(execution_price),
            "qty": str(quantity),
            "quoteQty": str(total_value),
            "commission": "0",
            "commissionAsset": quote_asset,
            "time": int(time.time() * 1000),
            "isBuyer": side == "BUY",
            "isMaker": order_type != "MARKET",
            "isBestMatch": True
        }
        
        self.trade_history.append(trade)
        
        # Remove from open orders if it was there
        self.open_orders = [o for o in self.open_orders if o["orderId"] != order["orderId"]]
        
        logger.info(f"Executed {side} order for {quantity} {base_asset} at {execution_price} {quote_asset}")
        
        return order
    
    # Public API methods (match BinanceClient interface)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Simulated exchange info."""
        return {
            "timezone": "UTC",
            "serverTime": int(time.time() * 1000),
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                    "filters": [
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00001000",
                            "maxQty": "9000.00000000",
                            "stepSize": "0.00001000"
                        },
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01000000",
                            "maxPrice": "1000000.00000000",
                            "tickSize": "0.01000000"
                        }
                    ]
                },
                {
                    "symbol": "ETHUSDT",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "quoteAsset": "USDT",
                    "filters": [
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00010000",
                            "maxQty": "9000.00000000",
                            "stepSize": "0.00010000"
                        },
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01000000",
                            "maxPrice": "1000000.00000000",
                            "tickSize": "0.01000000"
                        }
                    ]
                },
                {
                    "symbol": "BNBUSDT",
                    "status": "TRADING",
                    "baseAsset": "BNB",
                    "quoteAsset": "USDT",
                    "filters": [
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00100000",
                            "maxQty": "9000.00000000",
                            "stepSize": "0.00100000"
                        },
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01000000",
                            "maxPrice": "1000000.00000000",
                            "tickSize": "0.01000000"
                        }
                    ]
                }
            ]
        }
    
    def get_server_time(self) -> int:
        """Simulated server time."""
        return int(time.time() * 1000)
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Simulated ticker price."""
        if symbol:
            if symbol not in self.price_data:
                raise BinanceSimulatorException(f"Unknown symbol: {symbol}")
            return {"symbol": symbol, "price": str(self.price_data[symbol])}
        else:
            return [{"symbol": s, "price": str(p)} for s, p in self.price_data.items()]
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List[Any]]:
        """Simulated klines data."""
        if symbol not in self.klines_data or interval not in self.klines_data.get(symbol, {}):
            # If no data, generate some fake data
            now = int(time.time() * 1000)
            interval_ms = self._interval_to_milliseconds(interval)
            base_price = self.price_data.get(symbol, 50000.0)
            
            klines = []
            for i in range(limit):
                open_time = now - ((limit - i) * interval_ms)
                close_time = open_time + interval_ms - 1
                
                # Generate random price data around base price
                price_change = random.uniform(-0.01, 0.01)
                open_price = base_price * (1 + random.uniform(-0.01, 0.01))
                close_price = open_price * (1 + price_change)
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
                volume = random.uniform(10, 100)
                
                kline = [
                    open_time,                  # Open time
                    str(open_price),            # Open
                    str(high_price),            # High
                    str(low_price),             # Low
                    str(close_price),           # Close
                    str(volume),                # Volume
                    close_time,                 # Close time
                    str(volume * close_price),  # Quote asset volume
                    10,                         # Number of trades
                    str(volume * 0.5),          # Taker buy base asset volume
                    str(volume * 0.5 * close_price),  # Taker buy quote asset volume
                    "0"                         # Ignore
                ]
                
                klines.append(kline)
            
            # Update base price for next time
            self.price_data[symbol] = float(klines[-1][4])  # Last close price
            
            return klines
        
        # Filter by time if provided
        filtered_klines = self.klines_data[symbol][interval]
        
        if start_time:
            filtered_klines = [k for k in filtered_klines if k[0] >= start_time]
        
        if end_time:
            filtered_klines = [k for k in filtered_klines if k[0] <= end_time]
        
        # Sort by open time and limit
        filtered_klines = sorted(filtered_klines, key=lambda x: x[0])[:limit]
        
        return filtered_klines
    
    # Authenticated API methods
    
    def get_account(self) -> Dict[str, Any]:
        """Simulated account info."""
        balances = []
        for asset, free in self.balances.items():
            balances.append({
                "asset": asset,
                "free": str(free),
                "locked": "0.00000000"
            })
        
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": balances
        }
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = 'GTC',
        **kwargs
    ) -> Dict[str, Any]:
        """Simulated order creation."""
        # Validate inputs
        if symbol not in self.price_data:
            raise BinanceSimulatorException(f"Unknown symbol: {symbol}")
        
        if side not in ["BUY", "SELL"]:
            raise BinanceSimulatorException(f"Invalid side: {side}")
        
        if order_type not in ["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_LIMIT"]:
            raise BinanceSimulatorException(f"Invalid order type: {order_type}")
        
        if order_type == "LIMIT" and not price:
            raise BinanceSimulatorException("Price is required for LIMIT orders")
        
        # Create order object
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        client_order_id = kwargs.get("newClientOrderId", f"simulated-{uuid.uuid4()}")
        
        order = {
            "symbol": symbol,
            "orderId": order_id,
            "orderListId": -1,
            "clientOrderId": client_order_id,
            "transactTime": int(time.time() * 1000),
            "price": str(price) if price else "0.00000000",
            "origQty": str(quantity),
            "executedQty": "0.00000000",
            "cummulativeQuoteQty": "0.00000000",
            "status": "NEW",
            "timeInForce": time_in_force,
            "type": order_type,
            "side": side,
            "fills": []
        }
        
        # Save the order
        self.orders.append(copy.deepcopy(order))
        
        # For market orders, execute immediately
        if order_type == "MARKET":
            return self._execute_order(order)
        else:
            # For limit orders, add to open orders
            self.open_orders.append(copy.deepcopy(order))
            return order
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simulated open orders."""
        if symbol:
            return [o for o in self.open_orders if o["symbol"] == symbol]
        return self.open_orders
    
    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulated order cancellation."""
        if not order_id and not orig_client_order_id:
            raise BinanceSimulatorException("Either orderId or origClientOrderId must be provided")
        
        # Find the order
        order = None
        for o in self.open_orders:
            if (order_id and o["orderId"] == order_id) or \
               (orig_client_order_id and o["clientOrderId"] == orig_client_order_id):
                if o["symbol"] == symbol:
                    order = o
                    break
        
        if not order:
            raise BinanceSimulatorException("Order not found")
        
        # Update order status
        order["status"] = "CANCELED"
        
        # Remove from open orders
        self.open_orders = [o for o in self.open_orders if o["orderId"] != order["orderId"]]
        
        # Update the stored order
        for i, o in enumerate(self.orders):
            if o["orderId"] == order["orderId"]:
                self.orders[i] = copy.deepcopy(order)
                break
        
        return order
