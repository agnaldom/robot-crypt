"""
Enhanced market data and news API integrations.
Provides access to CoinGecko, CoinPaprika APIs with resilient fallback logic,
and CryptoPanic for news with sentiment analysis.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from core.config import settings
from core.logging_setup import logger


class APIProvider(Enum):
    """Available API providers for market data."""
    COINGECKO = "coingecko"
    COINPAPRIKA = "coinpaprika"


class MarketDataException(Exception):
    """Exception raised for Market Data API errors."""
    pass


class NewsAPIException(Exception):
    """Exception raised for News API errors."""
    pass


@dataclass
class MarketData:
    """Market data structure for cryptocurrency."""
    symbol: str
    name: str
    price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    last_updated: Optional[datetime] = None
    provider: Optional[str] = None


@dataclass
class NewsArticle:
    """News article structure."""
    title: str
    description: str
    url: str
    published_at: datetime
    source: str
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    currencies: List[str] = None


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def acquire(self):
        """Acquire permission to make an API call."""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0]) + 1
            logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
            return await self.acquire()
        
        self.calls.append(now)


class EnhancedMarketDataProvider:
    """
    Enhanced market data provider with multiple API sources and fallback logic.
    """
    
    def __init__(self):
        self.session = None
        self.coingecko_limiter = RateLimiter(calls_per_minute=50)  # CoinGecko free tier
        self.coinpaprika_limiter = RateLimiter(calls_per_minute=100)  # CoinPaprika free tier
        self.cryptopanic_limiter = RateLimiter(calls_per_minute=200)  # CryptoPanic free tier
        
        # API endpoints
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.coinpaprika_base = "https://api.coinpaprika.com/v1"
        self.cryptopanic_base = "https://cryptopanic.com/api/free/v1"
        
        # Symbol mapping for different providers
        self.symbol_mapping = {
            "BTC": {"coingecko": "bitcoin", "coinpaprika": "btc-bitcoin"},
            "ETH": {"coingecko": "ethereum", "coinpaprika": "eth-ethereum"},
            "BNB": {"coingecko": "binancecoin", "coinpaprika": "bnb-binance-coin"},
            "USDT": {"coingecko": "tether", "coinpaprika": "usdt-tether"},
            "DOGE": {"coingecko": "dogecoin", "coinpaprika": "doge-dogecoin"},
            "SHIB": {"coingecko": "shiba-inu", "coinpaprika": "shib-shiba-inu"},
            "FLOKI": {"coingecko": "floki", "coinpaprika": "floki-floki-inu"},
        }
    
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
    
    async def _request(self, url: str, params: Dict[str, Any] = None, provider: str = "unknown") -> Dict[str, Any]:
        """
        Make an HTTP request with error handling and retries.
        
        Args:
            url: Request URL
            params: Query parameters
            provider: API provider name for logging
            
        Returns:
            Response data as dictionary
            
        Raises:
            MarketDataException: If request fails after retries
        """
        if not self.session:
            raise MarketDataException("HTTP session not initialized")
        
        params = params or {}
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Successful {provider} API request: {url}")
                        return data
                    elif response.status == 429:
                        # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"{provider} rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        response.raise_for_status()
                        
            except aiohttp.ClientError as e:
                logger.warning(f"{provider} API request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise MarketDataException(f"{provider} API request failed after {max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise MarketDataException(f"{provider} API request failed after {max_retries} attempts")
    
    def _get_symbol_id(self, symbol: str, provider: APIProvider) -> str:
        """Get provider-specific symbol ID."""
        symbol = symbol.upper()
        if symbol in self.symbol_mapping:
            return self.symbol_mapping[symbol][provider.value]
        return symbol.lower()
    
    async def get_crypto_prices_coingecko(self, symbols: List[str]) -> List[MarketData]:
        """
        Get cryptocurrency prices from CoinGecko.
        
        Args:
            symbols: List of cryptocurrency symbols
            
        Returns:
            List of MarketData objects
        """
        await self.coingecko_limiter.acquire()
        
        # Map symbols to CoinGecko IDs
        coin_ids = [self._get_symbol_id(symbol, APIProvider.COINGECKO) for symbol in symbols]
        
        url = f"{self.coingecko_base}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }
        
        try:
            data = await self._request(url, params, "CoinGecko")
            
            results = []
            for i, symbol in enumerate(symbols):
                coin_id = coin_ids[i]
                if coin_id in data:
                    coin_data = data[coin_id]
                    results.append(MarketData(
                        symbol=symbol.upper(),
                        name=coin_id,
                        price=coin_data.get("usd", 0),
                        price_change_24h=coin_data.get("usd_24h_change", 0),
                        price_change_percentage_24h=coin_data.get("usd_24h_change", 0),
                        market_cap=coin_data.get("usd_market_cap"),
                        volume_24h=coin_data.get("usd_24h_vol"),
                        last_updated=datetime.fromtimestamp(coin_data.get("last_updated_at", 0)),
                        provider="coingecko"
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"CoinGecko API error: {e}")
            raise MarketDataException(f"CoinGecko API error: {e}")
    
    async def get_crypto_prices_coinpaprika(self, symbols: List[str]) -> List[MarketData]:
        """
        Get cryptocurrency prices from CoinPaprika.
        
        Args:
            symbols: List of cryptocurrency symbols
            
        Returns:
            List of MarketData objects
        """
        await self.coinpaprika_limiter.acquire()
        
        results = []
        
        for symbol in symbols:
            try:
                coin_id = self._get_symbol_id(symbol, APIProvider.COINPAPRIKA)
                url = f"{self.coinpaprika_base}/tickers/{coin_id}"
                
                data = await self._request(url, provider="CoinPaprika")
                
                quotes = data.get("quotes", {}).get("USD", {})
                results.append(MarketData(
                    symbol=symbol.upper(),
                    name=data.get("name", ""),
                    price=quotes.get("price", 0),
                    price_change_24h=quotes.get("percent_change_24h", 0),
                    price_change_percentage_24h=quotes.get("percent_change_24h", 0),
                    market_cap=quotes.get("market_cap"),
                    volume_24h=quotes.get("volume_24h"),
                    circulating_supply=data.get("circulating_supply"),
                    total_supply=data.get("total_supply"),
                    last_updated=datetime.fromisoformat(data.get("last_updated", "").replace("Z", "+00:00")) if data.get("last_updated") else None,
                    provider="coinpaprika"
                ))
                
            except Exception as e:
                logger.warning(f"CoinPaprika API error for {symbol}: {e}")
                continue
        
        return results
    
    async def get_crypto_prices(self, symbols: List[str], use_fallback: bool = True) -> List[MarketData]:
        """
        Get cryptocurrency prices with fallback logic.
        
        Args:
            symbols: List of cryptocurrency symbols
            use_fallback: Whether to use fallback provider if primary fails
            
        Returns:
            List of MarketData objects
        """
        try:
            # Try CoinGecko first
            logger.info(f"Fetching prices for {symbols} from CoinGecko")
            return await self.get_crypto_prices_coingecko(symbols)
            
        except MarketDataException as e:
            logger.warning(f"CoinGecko failed: {e}")
            
            if use_fallback:
                try:
                    logger.info(f"Falling back to CoinPaprika for {symbols}")
                    return await self.get_crypto_prices_coinpaprika(symbols)
                except MarketDataException as fallback_e:
                    logger.error(f"CoinPaprika fallback also failed: {fallback_e}")
                    raise MarketDataException(f"Both CoinGecko and CoinPaprika failed: {e}, {fallback_e}")
            else:
                raise
    
    async def get_historical_data(self, symbol: str, days: int = 30, provider: APIProvider = APIProvider.COINGECKO) -> List[Dict[str, Any]]:
        """
        Get historical market data for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol
            days: Number of days of historical data
            provider: API provider to use
            
        Returns:
            List of historical data points
        """
        if provider == APIProvider.COINGECKO:
            await self.coingecko_limiter.acquire()
            
            coin_id = self._get_symbol_id(symbol, provider)
            url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily" if days > 1 else "hourly"
            }
            
            try:
                data = await self._request(url, params, "CoinGecko")
                
                # Convert to standardized format
                prices = data.get("prices", [])
                volumes = data.get("total_volumes", [])
                market_caps = data.get("market_caps", [])
                
                historical_data = []
                for i, price_point in enumerate(prices):
                    timestamp, price = price_point
                    historical_data.append({
                        "timestamp": datetime.fromtimestamp(timestamp / 1000),
                        "price": price,
                        "volume": volumes[i][1] if i < len(volumes) else None,
                        "market_cap": market_caps[i][1] if i < len(market_caps) else None
                    })
                
                return historical_data
                
            except Exception as e:
                logger.error(f"CoinGecko historical data error: {e}")
                raise MarketDataException(f"CoinGecko historical data error: {e}")
        
        else:
            raise MarketDataException(f"Historical data not supported for provider: {provider}")
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get global cryptocurrency market overview.
        
        Returns:
            Market overview data
        """
        await self.coingecko_limiter.acquire()
        
        url = f"{self.coingecko_base}/global"
        
        try:
            data = await self._request(url, provider="CoinGecko")
            global_data = data.get("data", {})
            
            return {
                "total_market_cap": global_data.get("total_market_cap", {}).get("usd", 0),
                "total_volume": global_data.get("total_volume", {}).get("usd", 0),
                "market_cap_percentage": global_data.get("market_cap_percentage", {}),
                "active_cryptocurrencies": global_data.get("active_cryptocurrencies", 0),
                "markets": global_data.get("markets", 0),
                "market_cap_change_24h": global_data.get("market_cap_change_percentage_24h_usd", 0),
                "updated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Market overview error: {e}")
            raise MarketDataException(f"Market overview error: {e}")


class EnhancedNewsProvider:
    """
    Enhanced news provider with CryptoPanic integration and sentiment analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'CRYPTOPANIC_API_KEY', None)
        self.session = None
        self.rate_limiter = RateLimiter(calls_per_minute=200)
        self.base_url = "https://cryptopanic.com/api/free/v1"
        
        # Sentiment keywords
        self.positive_keywords = [
            "bull", "bullish", "surge", "soar", "rally", "gain", "rise", "up",
            "breakout", "moon", "pump", "adoption", "partnership", "upgrade",
            "breakthrough", "launch", "success", "positive", "optimistic"
        ]
        
        self.negative_keywords = [
            "bear", "bearish", "crash", "plunge", "fall", "drop", "down",
            "collapse", "dump", "selloff", "decline", "loss", "negative",
            "ban", "hack", "scam", "regulation", "warning", "concern"
        ]
    
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
    
    async def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to CryptoPanic API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
        """
        if not self.session:
            raise NewsAPIException("HTTP session not initialized")
        
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        if self.api_key:
            params["auth_token"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()
                    
        except aiohttp.ClientError as e:
            logger.error(f"CryptoPanic API request failed: {e}")
            raise NewsAPIException(f"CryptoPanic API request failed: {e}")
    
    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment of text using keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, score) where sentiment is 'positive', 'negative', or 'neutral'
            and score is between -1 and 1
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            return "neutral", 0.0
        
        score = (positive_count - negative_count) / total_keywords
        
        if score > 0.3:
            return "positive", score
        elif score < -0.3:
            return "negative", score
        else:
            return "neutral", score
    
    async def get_crypto_news(
        self,
        currencies: Optional[List[str]] = None,
        filter_type: str = "hot",
        page: int = 1,
        limit: int = 20
    ) -> List[NewsArticle]:
        """
        Get cryptocurrency news from CryptoPanic.
        
        Args:
            currencies: List of currency codes to filter by
            filter_type: News filter type (hot, trending, latest, bullish, bearish)
            page: Page number
            limit: Number of articles per page
            
        Returns:
            List of NewsArticle objects
        """
        params = {
            "filter": filter_type,
            "page": page,
            "limit": min(limit, 100)  # CryptoPanic max limit
        }
        
        if currencies:
            params["currencies"] = ",".join(currencies)
        
        try:
            data = await self._request("posts", params)
            
            articles = []
            for post in data.get("results", []):
                title = post.get("title", "")
                content = post.get("content", "")
                
                # Analyze sentiment
                sentiment_text = f"{title} {content}"
                sentiment, sentiment_score = self._analyze_sentiment(sentiment_text)
                
                # Parse published date
                published_str = post.get("published_at", "")
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except ValueError:
                    published_at = datetime.now()
                
                articles.append(NewsArticle(
                    title=title,
                    description=content,
                    url=post.get("url", ""),
                    published_at=published_at,
                    source=post.get("source", {}).get("title", "Unknown"),
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    currencies=post.get("currencies", [])
                ))
            
            return articles
            
        except Exception as e:
            logger.error(f"CryptoPanic news error: {e}")
            raise NewsAPIException(f"CryptoPanic news error: {e}")
    
    async def get_market_sentiment(self, symbol: str, days: int = 3) -> Dict[str, Any]:
        """
        Calculate market sentiment for a specific cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol
            days: Number of days to analyze
            
        Returns:
            Sentiment analysis results
        """
        try:
            # Get news for the specific currency
            articles = await self.get_crypto_news(
                currencies=[symbol.upper()],
                filter_type="latest",
                limit=50
            )
            
            # Filter articles by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_articles = [
                article for article in articles
                if article.published_at >= cutoff_date
            ]
            
            if not recent_articles:
                return {
                    "symbol": symbol,
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "article_count": 0,
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}
                }
            
            # Calculate sentiment distribution
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            total_score = 0.0
            
            for article in recent_articles:
                sentiment_counts[article.sentiment] += 1
                total_score += article.sentiment_score
            
            # Calculate overall metrics
            total_articles = len(recent_articles)
            avg_sentiment_score = total_score / total_articles
            
            # Determine overall sentiment
            if avg_sentiment_score > 0.2:
                overall_sentiment = "positive"
            elif avg_sentiment_score < -0.2:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            # Calculate confidence based on article count and sentiment consistency
            confidence = min(0.5 + (total_articles / 100), 0.95)
            
            return {
                "symbol": symbol,
                "sentiment": overall_sentiment,
                "sentiment_score": avg_sentiment_score,
                "confidence": confidence,
                "article_count": total_articles,
                "sentiment_distribution": sentiment_counts,
                "analyzed_period_days": days
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error for {symbol}: {e}")
            raise NewsAPIException(f"Sentiment analysis error for {symbol}: {e}")


# Convenience functions for easy usage
async def get_market_data(symbols: List[str], use_fallback: bool = True) -> List[MarketData]:
    """
    Get market data for cryptocurrencies.
    
    Args:
        symbols: List of cryptocurrency symbols
        use_fallback: Whether to use fallback provider
        
    Returns:
        List of MarketData objects
    """
    async with EnhancedMarketDataProvider() as provider:
        return await provider.get_crypto_prices(symbols, use_fallback)


async def get_news(
    currencies: Optional[List[str]] = None,
    filter_type: str = "hot",
    limit: int = 20
) -> List[NewsArticle]:
    """
    Get cryptocurrency news.
    
    Args:
        currencies: List of currency codes to filter by
        filter_type: News filter type
        limit: Number of articles
        
    Returns:
        List of NewsArticle objects
    """
    async with EnhancedNewsProvider() as provider:
        return await provider.get_crypto_news(currencies, filter_type, limit=limit)


async def get_sentiment(symbol: str, days: int = 3) -> Dict[str, Any]:
    """
    Get market sentiment for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol
        days: Number of days to analyze
        
    Returns:
        Sentiment analysis results
    """
    async with EnhancedNewsProvider() as provider:
        return await provider.get_market_sentiment(symbol, days)


# Example usage
async def main():
    """Example usage of the enhanced market data and news providers."""
    
    # Test market data
    print("Testing market data...")
    try:
        market_data = await get_market_data(["BTC", "ETH", "BNB"])
        for data in market_data:
            print(f"{data.symbol}: ${data.price:.2f} ({data.price_change_percentage_24h:.2f}%)")
    except Exception as e:
        print(f"Market data error: {e}")
    
    # Test news
    print("\nTesting news...")
    try:
        news = await get_news(currencies=["BTC", "ETH"], limit=5)
        for article in news:
            print(f"{article.title} - {article.sentiment}")
    except Exception as e:
        print(f"News error: {e}")
    
    # Test sentiment
    print("\nTesting sentiment...")
    try:
        sentiment = await get_sentiment("BTC")
        print(f"BTC sentiment: {sentiment['sentiment']} (score: {sentiment['sentiment_score']:.2f})")
    except Exception as e:
        print(f"Sentiment error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
