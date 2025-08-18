"""
BingX API client implementation for cryptocurrency trading.
"""
import time
import hmac
import hashlib
import json
from typing import Dict, List, Optional, Any, Union
import urllib.parse
import requests

from src.core.logging_setup import logger


class BingXAPIException(Exception):
    """Exception raised for BingX API errors."""
    pass


class BingXClient:
    """
    Client for interacting with the BingX API.
    
    BingX API Documentation: https://bingx-api.github.io/docs/
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        base_url: str = "https://open-api.bingx.com",
        testnet: bool = False
    ):
        """
        Initialize BingX API client.
        
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
            'User-Agent': 'robot-crypt-bingx/1.0'
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
            BingXAPIException: If the response indicates an error
        """
        try:
            data = response.json()
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text}")
            raise BingXAPIException(f"Invalid JSON response: {response.text}")
        
        # BingX API returns code 0 for success
        if data.get('code') != 0:
            error_msg = data.get('msg', 'Unknown error')
            logger.error(f"BingX API error: {error_msg}")
            raise BingXAPIException(f"API error: {error_msg}")
        
        return data
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make request to BingX API.
        
        Args:
            method (str): HTTP method (GET, POST, DELETE, etc.)
            endpoint (str): API endpoint
            params (Dict[str, Any], optional): Request parameters
            signed (bool, optional): Whether request requires signature
        
        Returns:
            Dict[str, Any]: Response data
        
        Raises:
            BingXAPIException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare parameters
        params = params or {}
        
        # Add timestamp for signed requests
        if signed:
            if not self.api_key or not self.api_secret:
                raise BingXAPIException("API key and secret required for authenticated endpoints")
            
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
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return self._handle_response(response)
        
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise BingXAPIException(f"Request failed: {str(e)}")
    
    # Public API methods
    
    def get_server_time(self) -> int:
        """
        Get server time.
        
        Returns:
            int: Server time in milliseconds
        """
        response = self._request('GET', '/openApi/spot/v1/time')
        return response['data']['serverTime']
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information.
        
        Returns:
            Dict[str, Any]: Exchange information
        """
        return self._request('GET', '/openApi/spot/v1/common/symbols')
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get latest price for a symbol or all symbols.
        
        Args:
            symbol (str, optional): Symbol to get price for
        
        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: Price data
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/openApi/spot/v1/ticker/price', params)
    
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
        
        response = self._request('GET', '/openApi/spot/v1/market/kline', params)
        return response['data']
    
    # Authenticated API methods
    
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dict[str, Any]: Account information
        """
        return self._request('GET', '/openApi/spot/v1/account/balance', signed=True)
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            symbol (str): Symbol to place order for
            side (str): Order side (BUY or SELL)
            order_type (str): Order type (LIMIT, MARKET, etc.)
            quantity (float): Order quantity
            price (float, optional): Order price for limit orders
            **kwargs: Additional parameters
        
        Returns:
            Dict[str, Any]: Order response
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
        }
        
        if order_type == 'LIMIT':
            if not price:
                raise BingXAPIException("Price is required for LIMIT orders")
            params['price'] = price
        
        # Add any additional parameters
        params.update(kwargs)
        
        return self._request('POST', '/openApi/spot/v1/trade/order', params=params, signed=True)
    
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
        
        response = self._request('GET', '/openApi/spot/v1/trade/openOrders', params=params, signed=True)
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
            BingXAPIException: If neither order_id nor orig_client_order_id is provided
        """
        if not order_id and not orig_client_order_id:
            raise BingXAPIException("Either orderId or origClientOrderId must be provided")
        
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('DELETE', '/openApi/spot/v1/trade/order', params=params, signed=True)
