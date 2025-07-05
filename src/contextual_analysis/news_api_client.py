#!/usr/bin/env python3
"""
News API Client - CoinGecko Integration
Provides news data fetching capabilities using CoinGecko's free API
"""

import logging
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsApiClient:
    """
    News API Client using CoinGecko's free API
    Provides cryptocurrency news and market data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NewsApiClient
        
        Args:
            api_key: API key for news service (optional, not needed for CoinGecko)
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RobotCrypt/1.0 (Crypto Trading Bot)',
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 1.0  # CoinGecko rate limit: 1 request per second
        self.last_request_time = 0
        
        # Cache for coin list to avoid repeated API calls
        self._coin_list_cache = None
        self._coin_list_cache_time = 0
        self._cache_duration = 3600  # 1 hour
        
        logger.info("NewsApiClient initialized with CoinGecko API")
    
    def _rate_limit(self):
        """
        Implement rate limiting to respect CoinGecko's limits
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Make a request to CoinGecko API with rate limiting
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data or None if failed
        """
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def _get_coin_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all coins from CoinGecko (with caching)
        
        Returns:
            List of coin data
        """
        current_time = time.time()
        
        # Check cache
        if (self._coin_list_cache and 
            current_time - self._coin_list_cache_time < self._cache_duration):
            return self._coin_list_cache
        
        # Fetch new data
        data = self._make_request("coins/list")
        if data:
            self._coin_list_cache = data
            self._coin_list_cache_time = current_time
            return data
        
        return self._coin_list_cache or []
    
    def _symbol_to_coin_id(self, symbol: str) -> Optional[str]:
        """
        Convert a symbol to CoinGecko coin ID
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            CoinGecko coin ID or None
        """
        symbol = symbol.upper().replace('/USDT', '').replace('/BTC', '').replace('/ETH', '')
        
        # Common mappings
        symbol_mappings = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'XRP': 'ripple',
            'SOL': 'solana',
            'MATIC': 'polygon',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'FTM': 'fantom',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'ICP': 'internet-computer',
            'THETA': 'theta-token',
            'XLM': 'stellar',
            'TRX': 'tron',
            'ETC': 'ethereum-classic',
            'HBAR': 'hedera-hashgraph',
            'FIL': 'filecoin',
            'AAVE': 'aave',
            'COMP': 'compound-coin',
            'MKR': 'maker',
            'SUSHI': 'sushi',
            'CRV': 'curve-dao-token',
            'YFI': 'yearn-finance',
            'SNX': 'havven',
            'BAT': 'basic-attention-token',
            'ZRX': '0x',
            'ENJ': 'enjincoin',
            'MANA': 'decentraland',
            'SAND': 'the-sandbox',
            'AXS': 'axie-infinity',
            'GALA': 'gala',
            'CHZ': 'chiliz',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'EOS': 'eos',
            'XTZ': 'tezos',
            'NEO': 'neo',
            'IOTA': 'iota',
            'DASH': 'dash',
            'ZEC': 'zcash',
            'XMR': 'monero'
        }
        
        if symbol in symbol_mappings:
            return symbol_mappings[symbol]
        
        # Try to find in coin list
        coin_list = self._get_coin_list()
        for coin in coin_list:
            if coin.get('symbol', '').upper() == symbol:
                return coin.get('id')
        
        return None
    
    def get_crypto_news(self, symbols: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get cryptocurrency news using CoinGecko's market data and trending coins
        
        Args:
            symbols: List of crypto symbols to filter news
            limit: Maximum number of news items to return
            
        Returns:
            List of news items with market data and trending information
        """
        logger.info(f"Fetching crypto news for symbols: {symbols}, limit: {limit}")
        
        news_items = []
        
        try:
            # Get trending coins
            trending_data = self._make_request("search/trending")
            if trending_data and 'coins' in trending_data:
                for coin in trending_data['coins'][:limit]:
                    coin_data = coin.get('item', {})
                    news_item = {
                        'title': f"Trending: {coin_data.get('name', 'Unknown')} ({coin_data.get('symbol', 'N/A')})",
                        'description': f"Currently trending #{coin.get('market_cap_rank', 'N/A')} in market cap",
                        'url': f"https://www.coingecko.com/en/coins/{coin_data.get('id', '')}",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinGecko Trending',
                        'symbol': coin_data.get('symbol', '').upper(),
                        'coin_id': coin_data.get('id', ''),
                        'market_cap_rank': coin_data.get('market_cap_rank'),
                        'price_btc': coin_data.get('price_btc', 0),
                        'type': 'trending'
                    }
                    
                    # Filter by symbols if provided
                    if symbols is None or coin_data.get('symbol', '').upper() in [s.upper() for s in symbols]:
                        news_items.append(news_item)
            
            # Get market data for top coins
            market_data = self._make_request("coins/markets", {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': min(limit, 50),
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h,7d'
            })
            
            if market_data:
                for coin in market_data:
                    # Create news items for significant price movements
                    price_change_24h = coin.get('price_change_percentage_24h', 0)
                    price_change_7d = coin.get('price_change_percentage_7d', 0)
                    
                    if abs(price_change_24h) > 5:  # Significant movement
                        direction = "up" if price_change_24h > 0 else "down"
                        news_item = {
                            'title': f"{coin.get('name')} ({coin.get('symbol', '').upper()}) {direction} {abs(price_change_24h):.2f}% in 24h",
                            'description': f"Current price: ${coin.get('current_price', 0):.6f}, 7d change: {price_change_7d:.2f}%",
                            'url': f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                            'published_at': datetime.now().isoformat(),
                            'source': 'CoinGecko Market Data',
                            'symbol': coin.get('symbol', '').upper(),
                            'coin_id': coin.get('id', ''),
                            'current_price': coin.get('current_price', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'price_change_24h': price_change_24h,
                            'price_change_7d': price_change_7d,
                            'type': 'price_movement'
                        }
                        
                        # Filter by symbols if provided
                        if symbols is None or coin.get('symbol', '').upper() in [s.upper() for s in symbols]:
                            news_items.append(news_item)
            
            # Sort by relevance (price change magnitude)
            news_items.sort(key=lambda x: abs(x.get('price_change_24h', 0)), reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
        
        return news_items[:limit]
    
    def get_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get general market news and global crypto metrics
        
        Args:
            limit: Maximum number of news items to return
            
        Returns:
            List of market news items
        """
        logger.info(f"Fetching market news, limit: {limit}")
        
        news_items = []
        
        try:
            # Get global market data
            global_data = self._make_request("global")
            if global_data and 'data' in global_data:
                data = global_data['data']
                
                # Market cap dominance news
                btc_dominance = data.get('market_cap_percentage', {}).get('btc', 0)
                eth_dominance = data.get('market_cap_percentage', {}).get('eth', 0)
                
                news_items.append({
                    'title': f"Bitcoin dominance at {btc_dominance:.2f}%, Ethereum at {eth_dominance:.2f}%",
                    'description': f"Total market cap: ${data.get('total_market_cap', {}).get('usd', 0):,.0f}",
                    'url': "https://www.coingecko.com/en/global_charts",
                    'published_at': datetime.now().isoformat(),
                    'source': 'CoinGecko Global',
                    'total_market_cap': data.get('total_market_cap', {}).get('usd', 0),
                    'total_volume': data.get('total_volume', {}).get('usd', 0),
                    'btc_dominance': btc_dominance,
                    'eth_dominance': eth_dominance,
                    'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                    'type': 'market_overview'
                })
                
                # Volume analysis
                volume_change = data.get('market_cap_change_percentage_24h_usd', 0)
                if abs(volume_change) > 2:
                    direction = "increased" if volume_change > 0 else "decreased"
                    news_items.append({
                        'title': f"Total crypto market cap {direction} by {abs(volume_change):.2f}% in 24h",
                        'description': f"Market showing {'bullish' if volume_change > 0 else 'bearish'} sentiment",
                        'url': "https://www.coingecko.com/en/global_charts",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinGecko Global',
                        'market_cap_change_24h': volume_change,
                        'type': 'market_movement'
                    })
            
            # Get DeFi data
            defi_data = self._make_request("global/decentralized_finance_defi")
            if defi_data and 'data' in defi_data:
                defi = defi_data['data']
                news_items.append({
                    'title': f"DeFi Total Value Locked: ${defi.get('defi_market_cap', 0):,.0f}",
                    'description': f"DeFi dominance: {defi.get('defi_dominance', 0):.2f}% of total market",
                    'url': "https://www.coingecko.com/en/defi",
                    'published_at': datetime.now().isoformat(),
                    'source': 'CoinGecko DeFi',
                    'defi_market_cap': defi.get('defi_market_cap', 0),
                    'defi_dominance': defi.get('defi_dominance', 0),
                    'type': 'defi_update'
                })
                
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
        
        return news_items[:limit]
    
    def search_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for news by query using CoinGecko search
        
        Args:
            query: Search query
            limit: Maximum number of news items to return
            
        Returns:
            List of search results as news items
        """
        logger.info(f"Searching news for query: {query}, limit: {limit}")
        
        news_items = []
        
        try:
            # Search for coins
            search_data = self._make_request("search", {'query': query})
            if search_data:
                # Process coin results
                for coin in search_data.get('coins', [])[:limit]:
                    news_item = {
                        'title': f"Search Result: {coin.get('name')} ({coin.get('symbol', '').upper()})",
                        'description': f"Market cap rank: #{coin.get('market_cap_rank', 'N/A')}",
                        'url': f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinGecko Search',
                        'symbol': coin.get('symbol', '').upper(),
                        'coin_id': coin.get('id', ''),
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'large_image': coin.get('large'),
                        'type': 'search_result'
                    }
                    news_items.append(news_item)
                
                # Process exchange results
                for exchange in search_data.get('exchanges', [])[:limit//2]:
                    news_item = {
                        'title': f"Exchange: {exchange.get('name')}",
                        'description': f"Market type: {exchange.get('market_type', 'N/A')}",
                        'url': f"https://www.coingecko.com/en/exchanges/{exchange.get('id', '')}",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinGecko Search',
                        'exchange_id': exchange.get('id', ''),
                        'market_type': exchange.get('market_type'),
                        'type': 'exchange_result'
                    }
                    news_items.append(news_item)
                
        except Exception as e:
            logger.error(f"Error searching news: {e}")
        
        return news_items[:limit]
    
    def get_coin_news(self, coin_id: str) -> List[Dict[str, Any]]:
        """
        Get specific news and data for a coin
        
        Args:
            coin_id: CoinGecko coin ID
            
        Returns:
            List of news items for the specific coin
        """
        logger.info(f"Fetching news for coin: {coin_id}")
        
        news_items = []
        
        try:
            # Get detailed coin data
            coin_data = self._make_request(f"coins/{coin_id}", {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true'
            })
            
            if coin_data:
                market_data = coin_data.get('market_data', {})
                
                # Price action news
                price_change_24h = market_data.get('price_change_percentage_24h', 0)
                if abs(price_change_24h) > 3:
                    direction = "surged" if price_change_24h > 0 else "dropped"
                    news_items.append({
                        'title': f"{coin_data.get('name')} {direction} {abs(price_change_24h):.2f}% in 24 hours",
                        'description': f"Current price: ${market_data.get('current_price', {}).get('usd', 0):.6f}",
                        'url': f"https://www.coingecko.com/en/coins/{coin_id}",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinGecko',
                        'coin_id': coin_id,
                        'symbol': coin_data.get('symbol', '').upper(),
                        'price_change_24h': price_change_24h,
                        'current_price': market_data.get('current_price', {}).get('usd', 0),
                        'type': 'price_update'
                    })
                
                # Volume analysis
                volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                market_cap = market_data.get('market_cap', {}).get('usd', 0)
                if volume_24h > 0 and market_cap > 0:
                    volume_ratio = volume_24h / market_cap
                    if volume_ratio > 0.1:  # High volume day
                        news_items.append({
                            'title': f"{coin_data.get('name')} shows high trading volume",
                            'description': f"24h volume: ${volume_24h:,.0f} (ratio: {volume_ratio:.2%})",
                            'url': f"https://www.coingecko.com/en/coins/{coin_id}",
                            'published_at': datetime.now().isoformat(),
                            'source': 'CoinGecko',
                            'coin_id': coin_id,
                            'volume_24h': volume_24h,
                            'volume_ratio': volume_ratio,
                            'type': 'volume_analysis'
                        })
                
                # Development activity
                dev_data = coin_data.get('developer_data', {})
                if dev_data.get('commit_count_4_weeks', 0) > 50:
                    news_items.append({
                        'title': f"{coin_data.get('name')} shows active development",
                        'description': f"Recent commits: {dev_data.get('commit_count_4_weeks', 0)} in 4 weeks",
                        'url': f"https://www.coingecko.com/en/coins/{coin_id}",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinGecko',
                        'coin_id': coin_id,
                        'commits_4_weeks': dev_data.get('commit_count_4_weeks', 0),
                        'type': 'development_activity'
                    })
                
        except Exception as e:
            logger.error(f"Error fetching coin news: {e}")
        
        return news_items
    
    def get_exchanges_status(self) -> List[Dict[str, Any]]:
        """
        Get exchange status information
        
        Returns:
            List of exchange status news items
        """
        logger.info("Fetching exchange status information")
        
        news_items = []
        
        try:
            # Get exchange data
            exchanges_data = self._make_request("exchanges", {
                'per_page': 20,
                'page': 1
            })
            
            if exchanges_data:
                for exchange in exchanges_data:
                    # Check for significant volume changes
                    volume_change = exchange.get('trade_volume_24h_btc_normalized', 0)
                    if volume_change > 1000:  # Significant volume
                        news_items.append({
                            'title': f"{exchange.get('name')} trading volume: {volume_change:.0f} BTC",
                            'description': f"Trust score: {exchange.get('trust_score', 0)}/10",
                            'url': exchange.get('url', ''),
                            'published_at': datetime.now().isoformat(),
                            'source': 'CoinGecko Exchanges',
                            'exchange_id': exchange.get('id', ''),
                            'trust_score': exchange.get('trust_score', 0),
                            'volume_24h_btc': volume_change,
                            'type': 'exchange_volume'
                        })
                        
        except Exception as e:
            logger.error(f"Error fetching exchange status: {e}")
        
        return news_items[:10]
