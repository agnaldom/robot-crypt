#!/usr/bin/env python3
"""
Binance API Client for Real-time Market Data
Provides cryptocurrency prices, trading volumes, and market data from Binance.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BinanceAPIClient:
    """
    Binance API Client for fetching real-time market data
    Uses Binance public API endpoints (no authentication required for market data)
    """
    
    def __init__(self):
        """Initialize the Binance API client."""
        self.base_url = "https://api.binance.com/api/v3"
        self.session = None
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Common symbol mappings
        self.symbol_mappings = {
            "BTC/USDT": "BTCUSDT",
            "ETH/USDT": "ETHUSDT", 
            "BNB/USDT": "BNBUSDT",
            "ADA/USDT": "ADAUSDT",
            "DOT/USDT": "DOTUSDT",
            "LINK/USDT": "LINKUSDT",
            "UNI/USDT": "UNIUSDT",
            "DOGE/USDT": "DOGEUSDT",
            "SHIB/USDT": "SHIBUSDT",
            "SOL/USDT": "SOLUSDT",
            "MATIC/USDT": "MATICUSDT",
            "AVAX/USDT": "AVAXUSDT",
            "XRP/USDT": "XRPUSDT",
            "LTC/USDT": "LTCUSDT"
        }
        
        logger.info("BinanceAPIClient initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply rate limiting to respect Binance limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to Binance API with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None if error
        """
        if not self.session:
            raise Exception("HTTP session not initialized. Use async context manager.")
        
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Successful Binance API request: {endpoint}")
                    return data
                elif response.status == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Binance rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                else:
                    logger.error(f"Binance API error: {response.status} - {endpoint}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"Binance API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Binance API request: {e}")
            return None
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize trading pair symbol for Binance API.
        
        Args:
            symbol: Trading pair (e.g., BTC/USDT)
            
        Returns:
            Binance format symbol (e.g., BTCUSDT)
        """
        if symbol in self.symbol_mappings:
            return self.symbol_mappings[symbol]
        
        # Remove slash and convert to uppercase
        return symbol.replace('/', '').upper()
    
    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price for a trading pair.
        
        Args:
            symbol: Trading pair symbol (e.g., BTC/USDT)
            
        Returns:
            Dictionary with current price data
        """
        try:
            binance_symbol = self._normalize_symbol(symbol)
            
            # Get 24hr ticker statistics
            data = await self._make_request("ticker/24hr", {"symbol": binance_symbol})
            
            if data:
                return {
                    "symbol": symbol,
                    "price": float(data["lastPrice"]),
                    "price_change_24h": float(data["priceChange"]),
                    "price_change_percentage_24h": float(data["priceChangePercent"]),
                    "volume_24h": float(data["volume"]),
                    "quote_volume_24h": float(data["quoteVolume"]),
                    "high_24h": float(data["highPrice"]),
                    "low_24h": float(data["lowPrice"]),
                    "open_price": float(data["openPrice"]),
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": "binance"
                }
            else:
                logger.warning(f"No price data found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, interval: str = "1d", limit: int = 100) -> Optional[List[Dict]]:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit: Number of klines to return (max 1000)
            
        Returns:
            List of historical data points
        """
        try:
            binance_symbol = self._normalize_symbol(symbol)
            
            params = {
                "symbol": binance_symbol,
                "interval": interval,
                "limit": min(limit, 1000)
            }
            
            data = await self._make_request("klines", params)
            
            if data:
                historical_data = []
                for kline in data:
                    historical_data.append({
                        "timestamp": datetime.fromtimestamp(kline[0] / 1000).isoformat(),
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5]),
                        "close_time": datetime.fromtimestamp(kline[6] / 1000).isoformat(),
                        "quote_volume": float(kline[7]),
                        "trades_count": int(kline[8])
                    })
                
                return historical_data
            else:
                logger.warning(f"No historical data found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_top_symbols(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top trading symbols by 24h volume.
        
        Args:
            limit: Number of symbols to return
            
        Returns:
            List of top symbols with market data
        """
        try:
            # Get all 24hr ticker data
            data = await self._make_request("ticker/24hr")
            
            if data:
                # Filter USDT pairs and sort by quote volume
                usdt_pairs = [
                    ticker for ticker in data 
                    if ticker["symbol"].endswith("USDT") and float(ticker["quoteVolume"]) > 0
                ]
                
                # Sort by 24h quote volume (descending)
                usdt_pairs.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
                
                top_symbols = []
                for ticker in usdt_pairs[:limit]:
                    symbol = ticker["symbol"]
                    # Convert BTCUSDT to BTC/USDT format
                    formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
                    
                    top_symbols.append({
                        "symbol": formatted_symbol,
                        "price": float(ticker["lastPrice"]),
                        "price_change_24h": float(ticker["priceChange"]),
                        "price_change_percentage_24h": float(ticker["priceChangePercent"]),
                        "volume_24h": float(ticker["volume"]),
                        "quote_volume_24h": float(ticker["quoteVolume"]),
                        "high_24h": float(ticker["highPrice"]),
                        "low_24h": float(ticker["lowPrice"]),
                        "trades_count": int(ticker["count"])
                    })
                
                return top_symbols
            else:
                logger.warning("No ticker data available")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching top symbols: {e}")
            return []
    
    async def get_exchange_info(self) -> Optional[Dict[str, Any]]:
        """
        Get exchange trading rules and symbol information.
        
        Returns:
            Exchange information
        """
        try:
            data = await self._make_request("exchangeInfo")
            
            if data:
                return {
                    "timezone": data.get("timezone"),
                    "server_time": datetime.fromtimestamp(data.get("serverTime", 0) / 1000).isoformat(),
                    "symbols_count": len(data.get("symbols", [])),
                    "rate_limits": data.get("rateLimits", []),
                    "exchange_filters": data.get("exchangeFilters", [])
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching exchange info: {e}")
            return None
    
    async def get_market_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market summary for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary with market data for each symbol
        """
        try:
            results = {}
            
            # Process symbols in parallel (but respect rate limits)
            tasks = []
            for symbol in symbols:
                task = asyncio.create_task(self.get_current_price(symbol))
                tasks.append((symbol, task))
            
            # Wait for all tasks to complete
            for symbol, task in tasks:
                try:
                    price_data = await task
                    results[symbol] = price_data
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
                    results[symbol] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching market summary: {e}")
            return {}


# Convenience function for easy usage
async def get_binance_data(symbols: List[str]) -> Dict[str, Any]:
    """
    Get market data from Binance for multiple symbols.
    
    Args:
        symbols: List of trading pair symbols
        
    Returns:
        Dictionary with market data
    """
    async with BinanceAPIClient() as client:
        return await client.get_market_summary(symbols)


# Example usage
async def main():
    """Example usage of the Binance API client."""
    
    print("Testing Binance API client...")
    
    async with BinanceAPIClient() as client:
        # Test current price
        print("\n1. Testing current price for BTC/USDT...")
        btc_price = await client.get_current_price("BTC/USDT")
        if btc_price:
            print(f"BTC/USDT: ${btc_price['price']:,.2f} ({btc_price['price_change_percentage_24h']:+.2f}%)")
        
        # Test historical data
        print("\n2. Testing historical data...")
        historical = await client.get_historical_data("BTC/USDT", "1d", 7)
        if historical:
            print(f"Retrieved {len(historical)} days of historical data")
            print(f"Latest close: ${historical[-1]['close']}")
        
        # Test top symbols
        print("\n3. Testing top symbols...")
        top_symbols = await client.get_top_symbols(5)
        if top_symbols:
            print("Top 5 symbols by volume:")
            for symbol_data in top_symbols:
                print(f"  {symbol_data['symbol']}: ${symbol_data['price']:,.4f} "
                      f"({symbol_data['price_change_percentage_24h']:+.2f}%)")
        
        # Test exchange info
        print("\n4. Testing exchange info...")
        exchange_info = await client.get_exchange_info()
        if exchange_info:
            print(f"Exchange timezone: {exchange_info['timezone']}")
            print(f"Available symbols: {exchange_info['symbols_count']}")


if __name__ == "__main__":
    asyncio.run(main())
