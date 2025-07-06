#!/usr/bin/env python3
"""
CoinMarketCap API Client for Market Data and Cryptocurrency Information
Provides comprehensive cryptocurrency market data, rankings, and metadata.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class CoinMarketCapAPIClient:
    """
    CoinMarketCap API Client for fetching cryptocurrency market data
    Requires API key from CoinMarketCap Pro API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CoinMarketCap API client.
        
        Args:
            api_key: CoinMarketCap API key (optional, will use from settings if not provided)
        """
        self.api_key = api_key or getattr(settings, 'COINMARKETCAP_API_KEY', None)
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.session = None
        self.rate_limit_delay = 1.0  # 1 second between requests for free tier
        self.last_request_time = 0
        
        # Symbol mappings for common cryptocurrencies
        self.symbol_to_id = {
            "BTC": 1,
            "ETH": 1027,
            "BNB": 1839,
            "ADA": 2010,
            "DOT": 6636,
            "LINK": 1975,
            "UNI": 7083,
            "DOGE": 74,
            "SHIB": 5994,
            "SOL": 5426,
            "MATIC": 3890,
            "AVAX": 5805,
            "XRP": 52,
            "LTC": 2
        }
        
        if not self.api_key:
            logger.warning("CoinMarketCap API key not provided. Some features may not work.")
        else:
            logger.info("CoinMarketCapAPIClient initialized with API key")
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'deflate, gzip'
        }
        
        if self.api_key:
            headers['X-CMC_PRO_API_KEY'] = self.api_key
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply rate limiting to respect CoinMarketCap limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to CoinMarketCap API with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None if error
        """
        if not self.session:
            raise Exception("HTTP session not initialized. Use async context manager.")
        
        if not self.api_key:
            logger.error("CoinMarketCap API key is required for API requests")
            return None
        
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Successful CoinMarketCap API request: {endpoint}")
                    return data
                elif response.status == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"CoinMarketCap rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                elif response.status == 401:
                    logger.error("CoinMarketCap API key is invalid or missing")
                    return None
                elif response.status == 400:
                    logger.error(f"CoinMarketCap API bad request: {endpoint}")
                    return None
                else:
                    logger.error(f"CoinMarketCap API error: {response.status} - {endpoint}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"CoinMarketCap API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in CoinMarketCap API request: {e}")
            return None
    
    def _get_symbol_id(self, symbol: str) -> Optional[int]:
        """
        Get CoinMarketCap ID for a symbol.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            
        Returns:
            CoinMarketCap ID or None
        """
        # Remove trading pair suffix
        base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
        return self.symbol_to_id.get(base_symbol.upper())
    
    async def get_latest_quotes(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get latest price quotes for cryptocurrencies.
        
        Args:
            symbols: List of cryptocurrency symbols
            
        Returns:
            Dictionary with latest quotes
        """
        try:
            # Convert symbols to IDs
            ids = []
            symbol_map = {}
            
            for symbol in symbols:
                symbol_id = self._get_symbol_id(symbol)
                if symbol_id:
                    ids.append(str(symbol_id))
                    symbol_map[str(symbol_id)] = symbol
            
            if not ids:
                logger.warning("No valid symbols found for CoinMarketCap lookup")
                return None
            
            params = {
                'id': ','.join(ids),
                'convert': 'USD'
            }
            
            data = await self._make_request("cryptocurrency/quotes/latest", params)
            
            if data and 'data' in data:
                results = {}
                
                for id_str, coin_data in data['data'].items():
                    symbol = symbol_map.get(id_str)
                    if symbol and 'quote' in coin_data and 'USD' in coin_data['quote']:
                        quote = coin_data['quote']['USD']
                        
                        results[symbol] = {
                            "symbol": symbol,
                            "name": coin_data.get('name'),
                            "price": quote.get('price'),
                            "price_change_24h": quote.get('percent_change_24h'),
                            "price_change_7d": quote.get('percent_change_7d'),
                            "market_cap": quote.get('market_cap'),
                            "volume_24h": quote.get('volume_24h'),
                            "circulating_supply": coin_data.get('circulating_supply'),
                            "total_supply": coin_data.get('total_supply'),
                            "max_supply": coin_data.get('max_supply'),
                            "cmc_rank": coin_data.get('cmc_rank'),
                            "last_updated": quote.get('last_updated'),
                            "source": "coinmarketcap"
                        }
                
                return results
            else:
                logger.warning("No data received from CoinMarketCap")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching latest quotes: {e}")
            return None
    
    async def get_listings_latest(self, start: int = 1, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Get latest cryptocurrency listings ranked by market cap.
        
        Args:
            start: Starting rank (1-based)
            limit: Number of cryptocurrencies to return
            
        Returns:
            List of cryptocurrency data
        """
        try:
            params = {
                'start': start,
                'limit': min(limit, 5000),  # CoinMarketCap max limit
                'convert': 'USD',
                'sort': 'market_cap'
            }
            
            data = await self._make_request("cryptocurrency/listings/latest", params)
            
            if data and 'data' in data:
                listings = []
                
                for coin in data['data']:
                    if 'quote' in coin and 'USD' in coin['quote']:
                        quote = coin['quote']['USD']
                        
                        listings.append({
                            "id": coin.get('id'),
                            "name": coin.get('name'),
                            "symbol": coin.get('symbol'),
                            "slug": coin.get('slug'),
                            "cmc_rank": coin.get('cmc_rank'),
                            "price": quote.get('price'),
                            "price_change_24h": quote.get('percent_change_24h'),
                            "price_change_7d": quote.get('percent_change_7d'),
                            "market_cap": quote.get('market_cap'),
                            "volume_24h": quote.get('volume_24h'),
                            "circulating_supply": coin.get('circulating_supply'),
                            "total_supply": coin.get('total_supply'),
                            "max_supply": coin.get('max_supply'),
                            "last_updated": quote.get('last_updated')
                        })
                
                return listings
            else:
                logger.warning("No listings data received from CoinMarketCap")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching latest listings: {e}")
            return None
    
    async def get_global_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get global cryptocurrency market metrics.
        
        Returns:
            Global market metrics
        """
        try:
            params = {'convert': 'USD'}
            
            data = await self._make_request("global-metrics/quotes/latest", params)
            
            if data and 'data' in data:
                metrics = data['data']
                quote = metrics.get('quote', {}).get('USD', {})
                
                return {
                    "active_cryptocurrencies": metrics.get('active_cryptocurrencies'),
                    "total_cryptocurrencies": metrics.get('total_cryptocurrencies'),
                    "active_market_pairs": metrics.get('active_market_pairs'),
                    "active_exchanges": metrics.get('active_exchanges'),
                    "total_market_cap": quote.get('total_market_cap'),
                    "total_volume_24h": quote.get('total_volume_24h'),
                    "total_volume_24h_reported": quote.get('total_volume_24h_reported'),
                    "altcoin_volume_24h": quote.get('altcoin_volume_24h'),
                    "altcoin_market_cap": quote.get('altcoin_market_cap'),
                    "btc_dominance": metrics.get('btc_dominance'),
                    "eth_dominance": metrics.get('eth_dominance'),
                    "defi_volume_24h": metrics.get('defi_volume_24h'),
                    "defi_market_cap": metrics.get('defi_market_cap'),
                    "defi_24h_percentage_change": metrics.get('defi_24h_percentage_change'),
                    "stablecoin_volume_24h": metrics.get('stablecoin_volume_24h'),
                    "stablecoin_market_cap": metrics.get('stablecoin_market_cap'),
                    "derivatives_volume_24h": metrics.get('derivatives_volume_24h'),
                    "last_updated": quote.get('last_updated'),
                    "source": "coinmarketcap"
                }
            else:
                logger.warning("No global metrics data received from CoinMarketCap")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching global metrics: {e}")
            return None
    
    async def get_trending_cryptocurrencies(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get trending cryptocurrencies (gainers and losers).
        
        Returns:
            List of trending cryptocurrencies
        """
        try:
            data = await self._make_request("cryptocurrency/trending/latest")
            
            if data and 'data' in data:
                trending_data = data['data']
                trending_list = []
                
                # Process gainers
                for gainer in trending_data.get('gainers', []):
                    if 'quote' in gainer and 'USD' in gainer['quote']:
                        quote = gainer['quote']['USD']
                        trending_list.append({
                            "id": gainer.get('id'),
                            "name": gainer.get('name'),
                            "symbol": gainer.get('symbol'),
                            "price": quote.get('price'),
                            "price_change_24h": quote.get('percent_change_24h'),
                            "market_cap": quote.get('market_cap'),
                            "volume_24h": quote.get('volume_24h'),
                            "trend_type": "gainer"
                        })
                
                # Process losers
                for loser in trending_data.get('losers', []):
                    if 'quote' in loser and 'USD' in loser['quote']:
                        quote = loser['quote']['USD']
                        trending_list.append({
                            "id": loser.get('id'),
                            "name": loser.get('name'),
                            "symbol": loser.get('symbol'),
                            "price": quote.get('price'),
                            "price_change_24h": quote.get('percent_change_24h'),
                            "market_cap": quote.get('market_cap'),
                            "volume_24h": quote.get('volume_24h'),
                            "trend_type": "loser"
                        })
                
                return trending_list
            else:
                logger.warning("No trending data received from CoinMarketCap")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching trending cryptocurrencies: {e}")
            return None
    
    async def get_cryptocurrency_info(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get metadata information for cryptocurrencies.
        
        Args:
            symbols: List of cryptocurrency symbols
            
        Returns:
            Dictionary with cryptocurrency metadata
        """
        try:
            # Convert symbols to IDs
            ids = []
            symbol_map = {}
            
            for symbol in symbols:
                symbol_id = self._get_symbol_id(symbol)
                if symbol_id:
                    ids.append(str(symbol_id))
                    symbol_map[str(symbol_id)] = symbol
            
            if not ids:
                logger.warning("No valid symbols found for CoinMarketCap info lookup")
                return None
            
            params = {'id': ','.join(ids)}
            
            data = await self._make_request("cryptocurrency/info", params)
            
            if data and 'data' in data:
                results = {}
                
                for id_str, coin_info in data['data'].items():
                    symbol = symbol_map.get(id_str)
                    if symbol:
                        results[symbol] = {
                            "id": coin_info.get('id'),
                            "name": coin_info.get('name'),
                            "symbol": coin_info.get('symbol'),
                            "category": coin_info.get('category'),
                            "description": coin_info.get('description'),
                            "slug": coin_info.get('slug'),
                            "logo": coin_info.get('logo'),
                            "subreddit": coin_info.get('subreddit'),
                            "notice": coin_info.get('notice'),
                            "tags": coin_info.get('tags', []),
                            "platform": coin_info.get('platform'),
                            "date_added": coin_info.get('date_added'),
                            "twitter_username": coin_info.get('twitter_username'),
                            "is_hidden": coin_info.get('is_hidden'),
                            "date_launched": coin_info.get('date_launched'),
                            "contract_address": coin_info.get('contract_address', []),
                            "self_reported_circulating_supply": coin_info.get('self_reported_circulating_supply'),
                            "self_reported_tags": coin_info.get('self_reported_tags'),
                            "self_reported_market_cap": coin_info.get('self_reported_market_cap'),
                            "infinite_supply": coin_info.get('infinite_supply')
                        }
                
                return results
            else:
                logger.warning("No info data received from CoinMarketCap")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency info: {e}")
            return None


# Convenience functions for easy usage
async def get_coinmarketcap_quotes(symbols: List[str], api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get latest quotes from CoinMarketCap for multiple symbols.
    
    Args:
        symbols: List of cryptocurrency symbols
        api_key: CoinMarketCap API key
        
    Returns:
        Dictionary with quote data
    """
    async with CoinMarketCapAPIClient(api_key) as client:
        return await client.get_latest_quotes(symbols)


async def get_coinmarketcap_global_metrics(api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get global cryptocurrency market metrics from CoinMarketCap.
    
    Args:
        api_key: CoinMarketCap API key
        
    Returns:
        Global market metrics
    """
    async with CoinMarketCapAPIClient(api_key) as client:
        return await client.get_global_metrics()


# Example usage
async def main():
    """Example usage of the CoinMarketCap API client."""
    
    print("Testing CoinMarketCap API client...")
    
    # Note: You need a valid API key for this to work
    api_key = getattr(settings, 'COINMARKETCAP_API_KEY', None)
    
    if not api_key:
        print("⚠️  CoinMarketCap API key not found. Please set COINMARKETCAP_API_KEY in settings.")
        return
    
    async with CoinMarketCapAPIClient(api_key) as client:
        # Test latest quotes
        print("\n1. Testing latest quotes for BTC, ETH, BNB...")
        quotes = await client.get_latest_quotes(["BTC", "ETH", "BNB"])
        if quotes:
            for symbol, data in quotes.items():
                print(f"{symbol}: ${data['price']:,.2f} ({data['price_change_24h']:+.2f}%) - Rank #{data['cmc_rank']}")
        
        # Test global metrics
        print("\n2. Testing global metrics...")
        global_metrics = await client.get_global_metrics()
        if global_metrics:
            print(f"Total Market Cap: ${global_metrics['total_market_cap']:,.0f}")
            print(f"BTC Dominance: {global_metrics['btc_dominance']:.2f}%")
            print(f"Active Cryptocurrencies: {global_metrics['active_cryptocurrencies']}")
        
        # Test trending cryptocurrencies
        print("\n3. Testing trending cryptocurrencies...")
        trending = await client.get_trending_cryptocurrencies()
        if trending:
            print("Trending cryptocurrencies:")
            for coin in trending[:5]:
                print(f"  {coin['name']} ({coin['symbol']}): {coin['price_change_24h']:+.2f}% - {coin['trend_type']}")
        
        # Test listings
        print("\n4. Testing latest listings (top 10)...")
        listings = await client.get_listings_latest(1, 10)
        if listings:
            print("Top 10 cryptocurrencies by market cap:")
            for coin in listings:
                print(f"  #{coin['cmc_rank']} {coin['name']} ({coin['symbol']}): ${coin['price']:,.4f}")


if __name__ == "__main__":
    asyncio.run(main())
