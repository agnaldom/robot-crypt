"""Market data API client for CoinGecko and CoinPaprika integration."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from src.core.config import settings


logger = logging.getLogger(__name__)


class MarketDataClient:
    """Client for fetching market data from CoinGecko with CoinPaprika fallback."""
    
    def __init__(self):
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.coinpaprika_base_url = "https://api.coinpaprika.com/v1"
        self.timeout = ClientTimeout(total=30)
        self.session: Optional[ClientSession] = None
        
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _fetch_coingecko(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Fetch data from CoinGecko API."""
        try:
            session = await self._get_session()
            url = f"{self.coingecko_base_url}/{endpoint}"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning("CoinGecko rate limit exceeded")
                    await asyncio.sleep(1)
                    return None
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching from CoinGecko: {e}")
            return None
    
    async def _fetch_coinpaprika(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Fetch data from CoinPaprika API (fallback)."""
        try:
            session = await self._get_session()
            url = f"{self.coinpaprika_base_url}/{endpoint}"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"CoinPaprika API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching from CoinPaprika: {e}")
            return None
    
    async def get_coin_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Dict containing price, market_cap, volume, etc.
        """
        # Try CoinGecko first
        params = {
            'ids': symbol.lower(),
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        
        data = await self._fetch_coingecko("simple/price", params)
        if data and symbol.lower() in data:
            coin_data = data[symbol.lower()]
            return {
                'symbol': symbol,
                'price': coin_data.get('usd'),
                'market_cap': coin_data.get('usd_market_cap'),
                'volume_24h': coin_data.get('usd_24h_vol'),
                'change_24h': coin_data.get('usd_24h_change'),
                'last_updated': datetime.fromtimestamp(coin_data.get('last_updated_at', 0)),
                'source': 'coingecko'
            }
        
        # Fallback to CoinPaprika
        logger.info(f"Falling back to CoinPaprika for {symbol}")
        
        # Get coin list to find the correct ID
        coins_data = await self._fetch_coinpaprika("coins")
        if not coins_data:
            return None
        
        # Find coin by symbol
        coin_id = None
        for coin in coins_data:
            if coin['symbol'].lower() == symbol.lower():
                coin_id = coin['id']
                break
        
        if not coin_id:
            logger.warning(f"Coin {symbol} not found in CoinPaprika")
            return None
        
        # Get detailed coin data
        coin_data = await self._fetch_coinpaprika(f"tickers/{coin_id}")
        if coin_data:
            return {
                'symbol': symbol,
                'price': coin_data.get('quotes', {}).get('USD', {}).get('price'),
                'market_cap': coin_data.get('quotes', {}).get('USD', {}).get('market_cap'),
                'volume_24h': coin_data.get('quotes', {}).get('USD', {}).get('volume_24h'),
                'change_24h': coin_data.get('quotes', {}).get('USD', {}).get('percent_change_24h'),
                'last_updated': datetime.now(),
                'source': 'coinpaprika'
            }
        
        return None
    
    async def get_supported_coins(self) -> List[Dict[str, str]]:
        """Get list of supported cryptocurrencies.
        
        Returns:
            List of coins with id, symbol, and name
        """
        # Try CoinGecko first
        data = await self._fetch_coingecko("coins/list")
        if data:
            return [{
                'id': coin['id'],
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'source': 'coingecko'
            } for coin in data[:1000]]  # Limit to top 1000
        
        # Fallback to CoinPaprika
        logger.info("Falling back to CoinPaprika for coin list")
        data = await self._fetch_coinpaprika("coins")
        if data:
            return [{
                'id': coin['id'],
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'source': 'coinpaprika'
            } for coin in data if coin['is_active']]
        
        return []
    
    async def get_historical_prices(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical price data for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol
            days: Number of days of historical data
            
        Returns:
            List of price data points
        """
        # Try CoinGecko first
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily' if days > 1 else 'hourly'
        }
        
        data = await self._fetch_coingecko(f"coins/{symbol.lower()}/market_chart", params)
        if data and 'prices' in data:
            return [{
                'timestamp': datetime.fromtimestamp(price[0] / 1000),
                'price': price[1],
                'symbol': symbol,
                'source': 'coingecko'
            } for price in data['prices']]
        
        # CoinPaprika doesn't have free historical data
        logger.warning(f"No historical data available for {symbol}")
        return []
    
    async def get_market_summary(self) -> Optional[Dict[str, Any]]:
        """Get overall market summary.
        
        Returns:
            Dict with market cap, volume, dominance, etc.
        """
        # Try CoinGecko global data
        data = await self._fetch_coingecko("global")
        if data and 'data' in data:
            global_data = data['data']
            return {
                'total_market_cap': global_data.get('total_market_cap', {}).get('usd'),
                'total_volume': global_data.get('total_volume', {}).get('usd'),
                'market_cap_percentage': global_data.get('market_cap_percentage', {}),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies'),
                'markets': global_data.get('markets'),
                'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd'),
                'source': 'coingecko'
            }
        
        # Fallback to CoinPaprika global stats
        data = await self._fetch_coinpaprika("global")
        if data:
            return {
                'total_market_cap': data.get('market_cap_usd'),
                'total_volume': data.get('volume_24h_usd'),
                'market_cap_percentage': {'btc': data.get('bitcoin_dominance_percentage')},
                'active_cryptocurrencies': data.get('cryptocurrencies_number'),
                'markets': None,
                'market_cap_change_24h': data.get('market_cap_change_24h'),
                'source': 'coinpaprika'
            }
        
        return None


# Global instance
market_data_client = MarketDataClient()


class MarketDataException(Exception):
    """Exception raised for Market Data API errors."""
    pass


class MarketDataProvider:
    """
    Class for accessing external market data APIs.
    """

    def __init__(self, api_key: str):
        """
        Initialize MarketDataProvider.

        Args:
            api_key (str): API key for the data provider.
        """
        self.api_key = api_key

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a GET request to the data provider.

        Args:
            endpoint (str): API endpoint URL.
            params (Dict[str, Any]): Query parameters.

        Returns:
            Dict[str, Any]: Response data.

        Raises:
            MarketDataException: If the request fails.
        """
        try:
            response = requests.get(endpoint, params=params, headers={
                'Authorization': f'Bearer {self.api_key}'
            })
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Market data request failed: {e}")
            raise MarketDataException(f"Request failed: {e}")
        return response.json()

    def get_crypto_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Retrieve current prices for specified cryptocurrencies.

        Args:
            symbols (List[str]): List of cryptocurrency symbols.

        Returns:
            Dict[str, float]: Current prices indexed by symbol.
        """
        endpoint = "https://api.example.com/v1/prices"
        params = {
            "symbols": ",".join(symbols)
        }
        data = self._request(endpoint, params)
        return {symbol: data[symbol]['price'] for symbol in symbols}

    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Retrieve historical market data for a specified cryptocurrency.

        Args:
            symbol (str): Cryptocurrency symbol.
            start_date (str): Start date for historical data (YYYY-MM-DD).
            end_date (str): End date for historical data (YYYY-MM-DD).

        Returns:
            List[Dict[str, Any]]: Historical data records.
        """
        endpoint = "https://api.example.com/v1/historical"
        params = {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date
        }
        return self._request(endpoint, params)['data']

