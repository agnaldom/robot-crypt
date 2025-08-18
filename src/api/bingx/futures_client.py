"""
BingX Futures API client implementation for perpetual USD contracts.
"""
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Union
import urllib.parse
import requests

from src.core.logging_setup import logger


class BingXFuturesAPIException(Exception):
    """Exception raised for BingX Futures API errors."""
    pass


class BingXFuturesClient:
    """
    Client for interacting with the BingX Futures API.
    
    Specialized for perpetual USD contracts trading.
    BingX Futures API Documentation: https://bingx-api.github.io/docs/
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        base_url: str = "https://open-api.bingx.com",
        testnet: bool = False
    ):
        """
        Initialize BingX Futures API client.
        
        Args:
            api_key (str, optional): BingX API key
            api_secret (str, optional): BingX API secret
            base_url (str, optional): Base URL for API
            testnet (bool, optional): Whether to use testnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Use testnet if specified
        if testnet:
            self.base_url = "https://open-api-testnet.bingx.com"
        else:
            self.base_url = base_url
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'robot-crypt-bingx-futures/1.0'
        })
        
        if self.api_key:
            self.session.headers.update({
                'X-BX-APIKEY': self.api_key
            })
    
    def _generate_signature(self, params: str) -> str:
        """
        Generate signature for authenticated requests.
        
        Args:
            params (str): Request parameters string
        
        Returns:
            str: HMAC SHA256 signature
        """
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response.
        
        Args:
            response (requests.Response): Response from API
        
        Returns:
            Dict[str, Any]: Parsed response data
        
        Raises:
            BingXFuturesAPIException: If the response indicates an error
        """
        try:
            data = response.json()
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text}")
            raise BingXFuturesAPIException(f"Invalid JSON response: {response.text}")
        
        # BingX API returns code 0 for success
        if data.get('code') != 0:
            error_msg = data.get('msg', 'Unknown error')
            logger.error(f"BingX Futures API error: {error_msg}")
            raise BingXFuturesAPIException(f"API error: {error_msg}")
        
        return data
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make request to BingX Futures API.
        
        Args:
            method (str): HTTP method (GET, POST, DELETE, etc.)
            endpoint (str): API endpoint
            params (Dict[str, Any], optional): Request parameters
            signed (bool, optional): Whether request requires signature
        
        Returns:
            Dict[str, Any]: Response data
        
        Raises:
            BingXFuturesAPIException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare parameters
        params = params or {}
        
        # Add timestamp for signed requests
        if signed:
            if not self.api_key or not self.api_secret:
                raise BingXFuturesAPIException("API key and secret required for authenticated endpoints")
            
            params['timestamp'] = int(time.time() * 1000)
            
            # Create query string for signature
            query_string = urllib.parse.urlencode(sorted(params.items()))
            signature = self._generate_signature(query_string)
            params['signature'] = signature
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, json=params)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params)
            elif method == 'PUT':
                response = self.session.put(url, json=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return self._handle_response(response)
        
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise BingXFuturesAPIException(f"Request failed: {str(e)}")
    
    # Public API methods
    
    def get_server_time(self) -> int:
        """
        Get server time.
        
        Returns:
            int: Server time in milliseconds
        """
        response = self._request('GET', '/openApi/swap/v2/server/time')
        return response['data']['serverTime']
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get futures exchange information.
        
        Returns:
            Dict[str, Any]: Exchange information
        """
        return self._request('GET', '/openApi/swap/v2/quote/contracts')
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get latest price for a symbol or all symbols.
        
        Args:
            symbol (str, optional): Symbol to get price for (e.g., BTC-USDT)
        
        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: Price data
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/openApi/swap/v2/quote/price', params)
    
    def get_ticker_24hr(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get 24hr ticker price change statistics.
        
        Args:
            symbol (str, optional): Symbol to get stats for
        
        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: 24hr ticker statistics
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/openApi/swap/v2/quote/ticker', params)
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List[Any]]:
        """
        Get klines/candlestick data for futures.
        
        Args:
            symbol (str): Symbol to get klines for (e.g., BTC-USDT)
            interval (str): Interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time (int, optional): Start time in milliseconds
            end_time (int, optional): End time in milliseconds
            limit (int, optional): Number of results (max 1000)
        
        Returns:
            List[List[Any]]: Kline data
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        
        if end_time:
            params['endTime'] = end_time
        
        response = self._request('GET', '/openApi/swap/v3/quote/klines', params)
        return response['data']
    
    def get_depth(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book depth.
        
        Args:
            symbol (str): Symbol to get depth for
            limit (int, optional): Number of levels (5, 10, 20, 50, 100, 500, 1000)
        
        Returns:
            Dict[str, Any]: Order book data
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return self._request('GET', '/openApi/swap/v2/quote/depth', params)
    
    # Authenticated API methods
    
    def get_account(self) -> Dict[str, Any]:
        """
        Get futures account information.
        
        Returns:
            Dict[str, Any]: Account information
        """
        return self._request('GET', '/openApi/swap/v2/user/balance', signed=True)
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Args:
            symbol (str, optional): Symbol to get positions for
        
        Returns:
            List[Dict[str, Any]]: Position data
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        response = self._request('GET', '/openApi/swap/v2/user/positions', params=params, signed=True)
        return response['data']
    
    def create_order(
        self,
        symbol: str,
        side: str,
        position_side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        reduce_only: bool = False,
        time_in_force: str = 'GTC',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new futures order.
        
        Args:
            symbol (str): Symbol to place order for (e.g., BTC-USDT)
            side (str): Order side (BUY or SELL)
            position_side (str): Position side (LONG or SHORT)
            order_type (str): Order type (LIMIT, MARKET, STOP, TAKE_PROFIT, etc.)
            quantity (float): Order quantity
            price (float, optional): Order price for limit orders
            reduce_only (bool, optional): Whether to reduce position only
            time_in_force (str, optional): Time in force (GTC, IOC, FOK)
            **kwargs: Additional parameters
        
        Returns:
            Dict[str, Any]: Order response
        """
        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'type': order_type,
            'quantity': quantity,
            'reduceOnly': reduce_only,
            'timeInForce': time_in_force
        }
        
        if order_type in ['LIMIT', 'STOP', 'TAKE_PROFIT']:
            if not price:
                raise BingXFuturesAPIException(f"Price is required for {order_type} orders")
            params['price'] = price
        
        # Add any additional parameters
        params.update(kwargs)
        
        return self._request('POST', '/openApi/swap/v2/trade/order', params=params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders.
        
        Args:
            symbol (str, optional): Symbol to get orders for
        
        Returns:
            List[Dict[str, Any]]: Open orders
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        response = self._request('GET', '/openApi/swap/v2/trade/openOrders', params=params, signed=True)
        return response['data']
    
    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            symbol (str): Symbol
            order_id (int, optional): Order ID
            orig_client_order_id (str, optional): Original client order ID
        
        Returns:
            Dict[str, Any]: Cancellation response
        
        Raises:
            BingXFuturesAPIException: If neither order_id nor orig_client_order_id is provided
        """
        if not order_id and not orig_client_order_id:
            raise BingXFuturesAPIException("Either orderId or origClientOrderId must be provided")
        
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('DELETE', '/openApi/swap/v2/trade/order', params=params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancel all open orders for a symbol.
        
        Args:
            symbol (str): Symbol to cancel orders for
        
        Returns:
            Dict[str, Any]: Cancellation response
        """
        params = {'symbol': symbol}
        
        return self._request('DELETE', '/openApi/swap/v2/trade/allOpenOrders', params=params, signed=True)
    
    def set_leverage(self, symbol: str, leverage: int, side: str = 'BOTH') -> Dict[str, Any]:
        """
        Set leverage for a symbol.
        
        Args:
            symbol (str): Symbol to set leverage for
            leverage (int): Leverage value (1-125)
            side (str, optional): Position side (LONG, SHORT, BOTH)
        
        Returns:
            Dict[str, Any]: Response
        """
        params = {
            'symbol': symbol,
            'leverage': leverage,
            'side': side
        }
        
        return self._request('POST', '/openApi/swap/v2/trade/leverage', params=params, signed=True)
    
    def set_position_mode(self, dual_side: bool = True) -> Dict[str, Any]:
        """
        Set position mode (hedge or one-way).
        
        Args:
            dual_side (bool, optional): True for hedge mode, False for one-way mode
        
        Returns:
            Dict[str, Any]: Response
        """
        params = {
            'dualSidePosition': dual_side
        }
        
        return self._request('POST', '/openApi/swap/v2/trade/positionSide/dual', params=params, signed=True)
    
    def get_income_history(
        self,
        symbol: Optional[str] = None,
        income_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get income history.
        
        Args:
            symbol (str, optional): Symbol to get income for
            income_type (str, optional): Income type (TRANSFER, WELCOME_BONUS, etc.)
            start_time (int, optional): Start time in milliseconds
            end_time (int, optional): End time in milliseconds
            limit (int, optional): Number of results (max 1000)
        
        Returns:
            List[Dict[str, Any]]: Income history
        """
        params = {'limit': limit}
        
        if symbol:
            params['symbol'] = symbol
        
        if income_type:
            params['incomeType'] = income_type
        
        if start_time:
            params['startTime'] = start_time
        
        if end_time:
            params['endTime'] = end_time
        
        response = self._request('GET', '/openApi/swap/v2/user/income', params=params, signed=True)
        return response['data']
    
    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trade history.
        
        Args:
            symbol (str, optional): Symbol to get trades for
            start_time (int, optional): Start time in milliseconds
            end_time (int, optional): End time in milliseconds
            limit (int, optional): Number of results (max 1000)
        
        Returns:
            List[Dict[str, Any]]: Trade history
        """
        params = {'limit': limit}
        
        if symbol:
            params['symbol'] = symbol
        
        if start_time:
            params['startTime'] = start_time
        
        if end_time:
            params['endTime'] = end_time
        
        response = self._request('GET', '/openApi/swap/v2/user/trades', params=params, signed=True)
        return response['data']
