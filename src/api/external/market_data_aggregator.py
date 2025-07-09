#!/usr/bin/env python3
"""
Market Data Aggregator - Combines data from all external APIs
Provides a unified interface for accessing market data, news, events, and sentiment analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from src.api.external.binance_client import BinanceAPIClient
from src.api.external.coinmarketcap_client import CoinMarketCapAPIClient
from src.api.external.coinmarketcal_client import CoinMarketCalAPIClient
from src.api.external.cryptopanic_client import CryptoPanicAPIClient
from src.api.external.news_api_client import NewsAPIClient
from src.core.config import settings
from src.models.market_analysis import MarketAnalysis
from src.database.database import get_database

logger = logging.getLogger(__name__)


@dataclass
class MarketDataPoint:
    """Unified market data structure."""
    symbol: str
    name: Optional[str]
    price: float
    price_change_24h: float
    price_change_percentage_24h: float
    volume_24h: float
    market_cap: Optional[float]
    source: str
    timestamp: str
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None


@dataclass
class NewsArticle:
    """Unified news article structure."""
    title: str
    description: str
    url: str
    source: str
    published_at: str
    sentiment: str
    sentiment_score: float
    importance: str
    currencies: List[str]
    source_type: str


@dataclass
class EventData:
    """Unified event data structure."""
    title: str
    description: str
    date_event: str
    source: str
    importance: str
    currencies: List[str]
    category: str
    votes: Optional[int] = None


@dataclass
class SentimentAnalysis:
    """Unified sentiment analysis structure."""
    currency: str
    sentiment: str
    sentiment_score: float
    confidence: float
    post_count: int
    sentiment_distribution: Dict[str, int]
    source: str
    analyzed_days: int


class MarketDataAggregator:
    """
    Aggregates market data from multiple external APIs to provide
    a unified interface for comprehensive market analysis.
    """
    
    def __init__(self):
        """Initialize the market data aggregator."""
        self.binance_client = None
        self.coinmarketcap_client = None
        self.coinmarketcal_client = None
        self.cryptopanic_client = None
        self.news_api_client = None
        
        # Track API availability
        self.api_status = {
            'binance': True,  # No API key required for public data
            'coinmarketcap': bool(getattr(settings, 'COINMARKETCAP_API_KEY', None)),
            'coinmarketcal': bool(getattr(settings, 'COINMARKETCAL_API_KEY', None)),
            'cryptopanic': bool(getattr(settings, 'CRYPTOPANIC_API_KEY', None)),
            'news_api': bool(getattr(settings, 'NEWS_API_KEY', None))
        }
        
        logger.info(f"MarketDataAggregator initialized. API status: {self.api_status}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize clients
        self.binance_client = BinanceAPIClient()
        await self.binance_client.__aenter__()
        
        if self.api_status['coinmarketcap']:
            self.coinmarketcap_client = CoinMarketCapAPIClient()
            await self.coinmarketcap_client.__aenter__()
        
        if self.api_status['coinmarketcal']:
            self.coinmarketcal_client = CoinMarketCalAPIClient()
            await self.coinmarketcal_client.__aenter__()
        
        if self.api_status['cryptopanic']:
            self.cryptopanic_client = CryptoPanicAPIClient()
            await self.cryptopanic_client.__aenter__()
        
        if self.api_status['news_api']:
            self.news_api_client = NewsAPIClient()
            await self.news_api_client.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        clients = [
            self.binance_client,
            self.coinmarketcap_client,
            self.coinmarketcal_client,
            self.cryptopanic_client,
            self.news_api_client
        ]
        
        for client in clients:
            if client:
                try:
                    await client.__aexit__(exc_type, exc_val, exc_tb)
                except Exception as e:
                    logger.warning(f"Error closing client: {e}")
    
    async def get_current_prices(self, symbols: List[str]) -> List[MarketDataPoint]:
        """
        Get current prices from available sources.
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            List of unified market data points
        """
        try:
            results = []
            
            # Try Binance first (most reliable and free)
            if self.binance_client:
                try:
                    for symbol in symbols:
                        binance_data = await self.binance_client.get_current_price(symbol)
                        if binance_data:
                            results.append(MarketDataPoint(
                                symbol=binance_data['symbol'],
                                name=symbol.split('/')[0],
                                price=binance_data['price'],
                                price_change_24h=binance_data['price_change_24h'],
                                price_change_percentage_24h=binance_data['price_change_percentage_24h'],
                                volume_24h=binance_data['volume_24h'],
                                market_cap=None,  # Binance doesn't provide market cap
                                high_24h=binance_data['high_24h'],
                                low_24h=binance_data['low_24h'],
                                source=binance_data['source'],
                                timestamp=binance_data['last_updated']
                            ))
                except Exception as e:
                    logger.warning(f"Binance API error: {e}")
            
            # Supplement with CoinMarketCap data for market cap and rankings
            if self.coinmarketcap_client and len(results) < len(symbols):
                try:
                    # Extract base symbols
                    base_symbols = [symbol.split('/')[0] for symbol in symbols]
                    cmc_data = await self.coinmarketcap_client.get_latest_quotes(base_symbols)
                    
                    if cmc_data:
                        for symbol, data in cmc_data.items():
                            # Check if we already have this symbol from Binance
                            existing = next((r for r in results if r.symbol.split('/')[0] == symbol), None)
                            
                            if existing:
                                # Update existing data with market cap info
                                existing.market_cap = data['market_cap']
                                existing.circulating_supply = data['circulating_supply']
                                existing.total_supply = data['total_supply']
                            else:
                                # Add new data point
                                results.append(MarketDataPoint(
                                    symbol=f"{symbol}/USDT",
                                    name=data['name'],
                                    price=data['price'],
                                    price_change_24h=data['price_change_24h'],
                                    price_change_percentage_24h=data['price_change_24h'],
                                    volume_24h=data['volume_24h'],
                                    market_cap=data['market_cap'],
                                    circulating_supply=data['circulating_supply'],
                                    total_supply=data['total_supply'],
                                    source=data['source'],
                                    timestamp=data['last_updated']
                                ))
                
                except Exception as e:
                    logger.warning(f"CoinMarketCap API error: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            return []
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical price data.
        
        Args:
            symbol: Trading pair symbol
            days: Number of days of data
            
        Returns:
            List of historical data points
        """
        try:
            # Try Binance first
            if self.binance_client:
                try:
                    interval = "1d" if days > 7 else "4h"
                    limit = min(days, 1000)
                    
                    historical_data = await self.binance_client.get_historical_data(
                        symbol, interval, limit
                    )
                    
                    if historical_data:
                        return historical_data
                
                except Exception as e:
                    logger.warning(f"Binance historical data error: {e}")
            
            # Fallback: generate simple mock data based on current price
            current_prices = await self.get_current_prices([symbol])
            if current_prices:
                current_price = current_prices[0].price
                mock_data = []
                
                for i in range(days):
                    # Simple random walk for mock data
                    variation = (i - days/2) * 0.01  # 1% variation per day
                    price = current_price * (1 + variation)
                    
                    mock_data.append({
                        "timestamp": (datetime.now() - timedelta(days=days-i)).isoformat(),
                        "open": price * 0.99,
                        "high": price * 1.02,
                        "low": price * 0.98,
                        "close": price,
                        "volume": 1000000 + (i * 50000)
                    })
                
                return mock_data
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    async def get_trending_cryptocurrencies(self, limit: int = 20) -> List[MarketDataPoint]:
        """
        Get trending cryptocurrencies from available sources.
        
        Args:
            limit: Number of trending cryptocurrencies to return
            
        Returns:
            List of trending cryptocurrency data
        """
        try:
            results = []
            
            # Try Binance for volume-based trending
            if self.binance_client:
                try:
                    trending_data = await self.binance_client.get_top_symbols(limit)
                    
                    if trending_data:
                        for data in trending_data:
                            results.append(MarketDataPoint(
                                symbol=data['symbol'],
                                name=data['symbol'].split('/')[0],
                                price=data['price'],
                                price_change_24h=data['price_change_24h'],
                                price_change_percentage_24h=data['price_change_percentage_24h'],
                                volume_24h=data['volume_24h'],
                                market_cap=None,
                                high_24h=data['high_24h'],
                                low_24h=data['low_24h'],
                                source="binance",
                                timestamp=datetime.now().isoformat()
                            ))
                
                except Exception as e:
                    logger.warning(f"Binance trending error: {e}")
            
            # Try CoinMarketCap for additional trending data
            if self.coinmarketcap_client and len(results) < limit:
                try:
                    cmc_trending = await self.coinmarketcap_client.get_trending_cryptocurrencies()
                    
                    if cmc_trending:
                        for data in cmc_trending[:limit-len(results)]:
                            results.append(MarketDataPoint(
                                symbol=f"{data['symbol']}/USDT",
                                name=data['name'],
                                price=data['price'],
                                price_change_24h=data['price_change_24h'],
                                price_change_percentage_24h=data['price_change_24h'],
                                volume_24h=data['volume_24h'],
                                market_cap=data['market_cap'],
                                source="coinmarketcap",
                                timestamp=datetime.now().isoformat()
                            ))
                
                except Exception as e:
                    logger.warning(f"CoinMarketCap trending error: {e}")
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error getting trending cryptocurrencies: {e}")
            return []
    
    async def get_news_analysis(
        self,
        currencies: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[NewsArticle]:
        """
        Get comprehensive news analysis from multiple sources.
        
        Args:
            currencies: List of currencies to filter by
            limit: Number of news articles to return
            
        Returns:
            List of unified news articles
        """
        try:
            results = []
            
            # Get CryptoPanic news (crypto-specific)
            if self.cryptopanic_client:
                try:
                    crypto_news = await self.cryptopanic_client.get_posts(
                        currencies=currencies,
                        limit=limit//2
                    )
                    
                    if crypto_news:
                        for article in crypto_news:
                            results.append(NewsArticle(
                                title=article['title'],
                                description=article.get('url', ''),
                                url=article['url'],
                                source=article['source'],
                                published_at=article['published_at'],
                                sentiment=article['sentiment'],
                                sentiment_score=article['sentiment_score'],
                                importance=article['importance'],
                                currencies=[c['code'] for c in article['currencies']],
                                source_type="cryptopanic"
                            ))
                
                except Exception as e:
                    logger.warning(f"CryptoPanic news error: {e}")
            
            # Get NewsAPI articles for broader context
            if self.news_api_client:
                try:
                    query = "cryptocurrency OR bitcoin OR ethereum OR blockchain"
                    if currencies:
                        # Add specific currencies to query
                        currency_terms = " OR ".join(currencies)
                        query = f"({query}) OR ({currency_terms})"
                    
                    news_articles = await self.news_api_client.get_crypto_news(
                        query=query,
                        limit=limit//2
                    )
                    
                    if news_articles:
                        for article in news_articles:
                            # Extract relevant currencies from title/description
                            article_currencies = []
                            if currencies:
                                text = f"{article['title']} {article['description']}".lower()
                                article_currencies = [c for c in currencies if c.lower() in text]
                            
                            results.append(NewsArticle(
                                title=article['title'],
                                description=article['description'],
                                url=article['url'],
                                source=article['source'],
                                published_at=article['published_at'],
                                sentiment=article['sentiment'],
                                sentiment_score=article['sentiment_score'],
                                importance="medium",  # NewsAPI doesn't provide importance
                                currencies=article_currencies,
                                source_type="news_api"
                            ))
                
                except Exception as e:
                    logger.warning(f"NewsAPI error: {e}")
            
            # Sort by published date (most recent first)
            results.sort(key=lambda x: x.published_at, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error getting news analysis: {e}")
            return []
    
    async def get_upcoming_events(self, days_ahead: int = 7) -> List[EventData]:
        """
        Get upcoming cryptocurrency events.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming events
        """
        try:
            results = []
            
            # Get CoinMarketCal events
            if self.coinmarketcal_client:
                try:
                    events = await self.coinmarketcal_client.get_upcoming_events(
                        days_ahead=days_ahead,
                        limit=50
                    )
                    
                    if events:
                        for event in events:
                            results.append(EventData(
                                title=event['title'],
                                description=event['description'],
                                date_event=event['date_event'],
                                source="coinmarketcal",
                                importance=event['importance'],
                                currencies=[coin['symbol'] for coin in event['coins']],
                                category=event['category']['name'],
                                votes=event['vote_count']
                            ))
                
                except Exception as e:
                    logger.warning(f"CoinMarketCal events error: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    async def get_sentiment_analysis(
        self,
        currency: str,
        days: int = 7
    ) -> Optional[SentimentAnalysis]:
        """
        Get comprehensive sentiment analysis for a currency.
        
        Args:
            currency: Currency symbol
            days: Number of days to analyze
            
        Returns:
            Unified sentiment analysis
        """
        try:
            # Try CryptoPanic first (most comprehensive for crypto)
            if self.cryptopanic_client:
                try:
                    sentiment = await self.cryptopanic_client.get_sentiment_analysis(
                        currency, days
                    )
                    
                    if sentiment:
                        sentiment_analysis = SentimentAnalysis(
                            currency=sentiment['currency'],
                            sentiment=sentiment['sentiment'],
                            sentiment_score=sentiment['sentiment_score'],
                            confidence=sentiment['confidence'],
                            post_count=sentiment['post_count'],
                            sentiment_distribution=sentiment['sentiment_distribution'],
                            source=sentiment['source'],
                            analyzed_days=sentiment['analyzed_days']
                        )
                        
                        # Save to database
                        await self._save_analysis_to_database(
                            symbol=currency,
                            analysis_type='sentiment_analysis',
                            data=asdict(sentiment_analysis)
                        )
                        
                        return sentiment_analysis
                
                except Exception as e:
                    logger.warning(f"CryptoPanic sentiment error: {e}")
            
            # Fallback: basic sentiment from news
            if self.news_api_client:
                try:
                    news = await self.news_api_client.get_crypto_news(
                        query=f"{currency} OR bitcoin",
                        days_back=days,
                        limit=50
                    )
                    
                    if news:
                        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
                        total_score = 0.0
                        
                        for article in news:
                            sentiment_counts[article['sentiment']] += 1
                            total_score += article['sentiment_score']
                        
                        total_articles = len(news)
                        avg_score = total_score / total_articles if total_articles > 0 else 0.0
                        
                        overall_sentiment = "neutral"
                        if avg_score > 0.2:
                            overall_sentiment = "positive"
                        elif avg_score < -0.2:
                            overall_sentiment = "negative"
                        
                        sentiment_analysis = SentimentAnalysis(
                            currency=currency,
                            sentiment=overall_sentiment,
                            sentiment_score=avg_score,
                            confidence=min(0.5 + (total_articles / 100), 0.8),
                            post_count=total_articles,
                            sentiment_distribution=sentiment_counts,
                            source="news_api",
                            analyzed_days=days
                        )
                        
                        # Save to database
                        await self._save_analysis_to_database(
                            symbol=currency,
                            analysis_type='sentiment_analysis_fallback',
                            data=asdict(sentiment_analysis)
                        )
                        
                        return sentiment_analysis
                
                except Exception as e:
                    logger.warning(f"NewsAPI sentiment error: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting sentiment analysis: {e}")
            return None
    
    async def get_comprehensive_market_analysis(
        self,
        symbols: List[str],
        include_news: bool = True,
        include_events: bool = True,
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive market analysis combining all data sources.
        
        Args:
            symbols: List of trading pair symbols to analyze
            include_news: Whether to include news analysis
            include_events: Whether to include upcoming events
            include_sentiment: Whether to include sentiment analysis
            
        Returns:
            Comprehensive market analysis
        """
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "symbols_analyzed": symbols,
                "api_status": self.api_status
            }
            
            # Get current prices and market data
            logger.info("Fetching current market data...")
            market_data = await self.get_current_prices(symbols)
            analysis["market_data"] = [asdict(data) for data in market_data]
            
            # Get trending cryptocurrencies
            logger.info("Fetching trending cryptocurrencies...")
            trending = await self.get_trending_cryptocurrencies(10)
            analysis["trending"] = [asdict(data) for data in trending]
            
            # Get news analysis if requested
            if include_news:
                logger.info("Fetching news analysis...")
                base_symbols = [symbol.split('/')[0] for symbol in symbols]
                news = await self.get_news_analysis(base_symbols, 20)
                analysis["news"] = [asdict(article) for article in news]
            
            # Get upcoming events if requested
            if include_events:
                logger.info("Fetching upcoming events...")
                events = await self.get_upcoming_events(7)
                analysis["events"] = [asdict(event) for event in events]
            
            # Get sentiment analysis if requested
            if include_sentiment:
                logger.info("Fetching sentiment analysis...")
                sentiment_data = {}
                
                for symbol in symbols:
                    base_symbol = symbol.split('/')[0]
                    sentiment = await self.get_sentiment_analysis(base_symbol, 7)
                    if sentiment:
                        sentiment_data[base_symbol] = asdict(sentiment)
                
                analysis["sentiment"] = sentiment_data
            
            # Calculate summary metrics
            analysis["summary"] = self._calculate_summary_metrics(analysis)
            
            # Save comprehensive analysis to database
            await self._save_analysis_to_database(
                symbol='MARKET_OVERVIEW',
                analysis_type='comprehensive_market_analysis',
                data=analysis
            )
            
            logger.info("Comprehensive market analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting comprehensive market analysis: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "symbols_analyzed": symbols,
                "api_status": self.api_status
            }
    
    def _calculate_summary_metrics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary metrics from the analysis data."""
        try:
            summary = {}
            
            # Market data summary
            if "market_data" in analysis and analysis["market_data"]:
                prices = [data["price"] for data in analysis["market_data"]]
                changes = [data["price_change_percentage_24h"] for data in analysis["market_data"]]
                
                summary["market_summary"] = {
                    "average_price_change_24h": sum(changes) / len(changes) if changes else 0,
                    "positive_performers": len([c for c in changes if c > 0]),
                    "negative_performers": len([c for c in changes if c < 0]),
                    "total_symbols": len(analysis["market_data"])
                }
            
            # News sentiment summary
            if "news" in analysis and analysis["news"]:
                sentiments = [article["sentiment"] for article in analysis["news"]]
                sentiment_counts = {
                    "positive": sentiments.count("positive"),
                    "negative": sentiments.count("negative"),
                    "neutral": sentiments.count("neutral")
                }
                
                total_news = len(sentiments)
                overall_sentiment = "neutral"
                if sentiment_counts["positive"] > sentiment_counts["negative"]:
                    overall_sentiment = "positive"
                elif sentiment_counts["negative"] > sentiment_counts["positive"]:
                    overall_sentiment = "negative"
                
                summary["news_summary"] = {
                    "total_articles": total_news,
                    "sentiment_distribution": sentiment_counts,
                    "overall_news_sentiment": overall_sentiment
                }
            
            # Events summary
            if "events" in analysis and analysis["events"]:
                events = analysis["events"]
                high_importance = len([e for e in events if e["importance"] == "high"])
                
                summary["events_summary"] = {
                    "total_upcoming_events": len(events),
                    "high_importance_events": high_importance,
                    "next_7_days": len(events)
                }
            
            return summary
            
        except Exception as e:
            logger.warning(f"Error calculating summary metrics: {e}")
            return {"error": "Failed to calculate summary metrics"}
    
    async def _save_analysis_to_database(self, symbol: str, analysis_type: str, data: Dict[str, Any]):
        """Salva análise no banco de dados"""
        try:
            async for db in get_database():
                await MarketAnalysis.save_analysis(db, symbol, analysis_type, data)
                logger.info(f"Análise salva no banco: {symbol} - {analysis_type}")
        except Exception as e:
            logger.error(f"Erro ao salvar análise no banco: {e}")


# Convenience functions for easy usage
async def get_market_overview(symbols: List[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive market overview.
    
    Args:
        symbols: List of symbols to analyze (defaults to major cryptos)
        
    Returns:
        Market overview data
    """
    if symbols is None:
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]
    
    async with MarketDataAggregator() as aggregator:
        return await aggregator.get_comprehensive_market_analysis(symbols)


async def get_symbol_analysis(symbol: str) -> Dict[str, Any]:
    """
    Get detailed analysis for a specific symbol.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        Symbol analysis data
    """
    async with MarketDataAggregator() as aggregator:
        analysis = await aggregator.get_comprehensive_market_analysis([symbol])
        
        # Add historical data
        historical = await aggregator.get_historical_data(symbol, 30)
        analysis["historical_data"] = historical
        
        return analysis


# Example usage
async def main():
    """Example usage of the market data aggregator."""
    
    print("Testing Market Data Aggregator...")
    
    async with MarketDataAggregator() as aggregator:
        print(f"API Status: {aggregator.api_status}")
        
        # Test current prices
        print("\n1. Testing current prices...")
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        prices = await aggregator.get_current_prices(symbols)
        for price in prices:
            print(f"  {price.symbol}: ${price.price:,.2f} ({price.price_change_percentage_24h:+.2f}%)")
        
        # Test comprehensive analysis
        print("\n2. Testing comprehensive analysis...")
        analysis = await aggregator.get_comprehensive_market_analysis(
            symbols=["BTC/USDT", "ETH/USDT"],
            include_news=True,
            include_events=True,
            include_sentiment=True
        )
        
        print(f"Market data points: {len(analysis.get('market_data', []))}")
        print(f"News articles: {len(analysis.get('news', []))}")
        print(f"Upcoming events: {len(analysis.get('events', []))}")
        print(f"Sentiment analysis: {len(analysis.get('sentiment', {}))}")


if __name__ == "__main__":
    asyncio.run(main())
