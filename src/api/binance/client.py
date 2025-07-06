"""
Binance API client implementation.
"""
import time
import hmac
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple, Union
import urllib.parse
import requests

from core.config import settings
from core.logging_setup import logger


class BinanceAPIException(Exception):
    """Exception raised for Binance API errors."""
    pass


class BinanceClient:
    """
    Client for interacting with the Binance API.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        base_url: str = "https://api.binance.com",
        testnet: bool = False
    ):
        """
        Initialize Binance API client.
        
        Args:
            api_key (str, optional): Binance API key. Defaults to None.
            api_secret (str, optional): Binance API secret. Defaults to None.
            base_url (str, optional): Base URL for API. Defaults to "https://api.binance.com".
            testnet (bool, optional): Whether to use testnet. Defaults to False.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Use testnet if specified
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = base_url
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'robot-crypt/1.0'
        })
        
        if self.api_key:
            self.session.headers.update({
                'X-MBX-APIKEY': self.api_key
            })
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """
        Generate signature for authenticated requests.
        
        Args:
            data (Dict[str, Any]): Request parameters
        
        Returns:
            str: HMAC SHA256 signature
        """
        query_string = urllib.parse.urlencode(data)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
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
            BinanceAPIException: If the response indicates an error
        """
        if not response.ok:
            error_data = response.json() if response.text else {"error": response.reason}
            logger.error(f"Binance API error: {error_data}")
            raise BinanceAPIException(f"API error: {error_data}")
        
        return response.json()
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
        version: str = "v3"
    ) -> Dict[str, Any]:
        """
        Make request to Binance API.
        
        Args:
            method (str): HTTP method (GET, POST, DELETE, etc.)
            endpoint (str): API endpoint
            params (Dict[str, Any], optional): Request parameters. Defaults to None.
            signed (bool, optional): Whether request requires signature. Defaults to False.
            version (str, optional): API version. Defaults to "v3".
        
        Returns:
            Dict[str, Any]: Response data
        
        Raises:
            BinanceAPIException: If the request fails
        """
        url = f"{self.base_url}/api/{version}/{endpoint}"
        
        # Prepare parameters
        params = params or {}
        
        # Add timestamp for signed requests
        if signed:
            if not self.api_key or not self.api_secret:
                raise BinanceAPIException("API key and secret required for authenticated endpoints")
            
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, data=params)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return self._handle_response(response)
        
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise BinanceAPIException(f"Request failed: {str(e)}")
    
    # Public API methods
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information.
        
        Returns:
            Dict[str, Any]: Exchange information
        """
        return self._request('GET', 'exchangeInfo')
    
    def get_server_time(self) -> int:
        """
        Get server time.
        
        Returns:
            int: Server time in milliseconds
        """
        response = self._request('GET', 'time')
        return response['serverTime']
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get latest price for a symbol or all symbols.
        
        Args:
            symbol (str, optional): Symbol to get price for. Defaults to None (all symbols).
        
        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: Price data
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', 'ticker/price', params)
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List[Any]]:
        """
        Get klines/candlestick data.
        
        Args:
            symbol (str): Symbol to get klines for
            interval (str): Interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time (int, optional): Start time in milliseconds. Defaults to None.
            end_time (int, optional): End time in milliseconds. Defaults to None.
            limit (int, optional): Number of results. Defaults to 500, max 1000.
        
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
        
        return self._request('GET', 'klines', params)
    
    # Authenticated API methods
    
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dict[str, Any]: Account information
        """
        return self._request('GET', 'account', signed=True)
    
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
        """
        Create a new order.
        
        Args:
            symbol (str): Symbol to place order for
            side (str): Order side (BUY or SELL)
            order_type (str): Order type (LIMIT, MARKET, STOP_LOSS, etc.)
            quantity (float): Order quantity
            price (float, optional): Order price, required for limit orders. Defaults to None.
            time_in_force (str, optional): Time in force. Defaults to 'GTC'.
            **kwargs: Additional parameters
        
        Returns:
            Dict[str, Any]: Order response
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timestamp': int(time.time() * 1000)
        }
        
        if order_type == 'LIMIT':
            if not price:
                raise BinanceAPIException("Price is required for LIMIT orders")
            params['price'] = price
            params['timeInForce'] = time_in_force
        
        # Add any additional parameters
        params.update(kwargs)
        
        return self._request('POST', 'order', params=params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders.
        
        Args:
            symbol (str, optional): Symbol to get orders for. Defaults to None (all symbols).
        
        Returns:
            List[Dict[str, Any]]: Open orders
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', 'openOrders', params=params, signed=True)
    
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
            order_id (int, optional): Order ID. Defaults to None.
            orig_client_order_id (str, optional): Original client order ID. Defaults to None.
        
        Returns:
            Dict[str, Any]: Cancellation response
        
        Raises:
            BinanceAPIException: If neither order_id nor orig_client_order_id is provided
        """
        if not order_id and not orig_client_order_id:
            raise BinanceAPIException("Either orderId or origClientOrderId must be provided")
        
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('DELETE', 'order', params=params, signed=True)
