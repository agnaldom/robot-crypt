"""
Market data API router for Robot-Crypt.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.core.config import Settings
from src.core.logger import logger
from src.api.external.market_data_aggregator import MarketDataAggregator, get_market_overview, get_symbol_analysis

router = APIRouter(prefix="/market", tags=["market"])

# Initialize settings
settings = Settings()
executor = ThreadPoolExecutor(max_workers=4)


@router.get("/price/{symbol}")
async def get_current_price(
    symbol: str
) -> Dict[str, Any]:
    """
    Get current price for a trading pair.
    
    Args:
        symbol: Trading pair symbol (e.g., BTC/USDT)
        
    Returns:
        Dictionary containing current price data
    """
    try:
        async with MarketDataAggregator() as aggregator:
            prices = await aggregator.get_current_prices([symbol])
            
            if not prices:
                raise HTTPException(
                    status_code=404,
                    detail=f"Price data not found for {symbol}"
                )
            
            price_data = prices[0]
            
            return {
                "symbol": price_data.symbol,
                "name": price_data.name,
                "price": price_data.price,
                "price_change_24h": price_data.price_change_24h,
                "price_change_percentage_24h": price_data.price_change_percentage_24h,
                "volume_24h": price_data.volume_24h,
                "market_cap": price_data.market_cap,
                "high_24h": price_data.high_24h,
                "low_24h": price_data.low_24h,
                "source": price_data.source,
                "timestamp": price_data.timestamp
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch price data for {symbol}"
        )


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    days: int = Query(default=7, ge=1, le=365, description="Number of days of historical data")
) -> Dict[str, Any]:
    """
    Get historical price data for a trading pair.
    
    Args:
        symbol: Trading pair symbol (e.g., BTC/USDT)
        days: Number of days of historical data (1-365)
        
    Returns:
        Dictionary containing historical price data
    """
    try:
        async with MarketDataAggregator() as aggregator:
            historical_data = await aggregator.get_historical_data(symbol, days)
            
            if not historical_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Historical data not found for {symbol}"
                )
            
            return {
                "symbol": symbol,
                "days": days,
                "data": historical_data,
                "count": len(historical_data),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical data for {symbol}"
        )


@router.get("/trending")
async def get_trending_coins(
    limit: int = Query(default=10, ge=1, le=50, description="Number of trending coins to return")
) -> Dict[str, Any]:
    """
    Get trending coins data.
    
    Args:
        limit: Number of trending coins to return (1-50)
        
    Returns:
        Dictionary containing trending coins data
    """
    try:
        async with MarketDataAggregator() as aggregator:
            trending_data = await aggregator.get_trending_cryptocurrencies(limit)
            
            trending_coins = []
            for data in trending_data:
                trending_coins.append({
                    "symbol": data.symbol,
                    "name": data.name,
                    "price": data.price,
                    "price_change_24h": data.price_change_24h,
                    "price_change_percentage_24h": data.price_change_percentage_24h,
                    "volume_24h": data.volume_24h,
                    "market_cap": data.market_cap,
                    "source": data.source
                })
            
            return {
                "trending_coins": trending_coins,
                "count": len(trending_coins),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error fetching trending coins: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch trending coins data"
        )


@router.get("/market-summary")
async def get_market_summary(
    symbols: List[str] = Query(default=["BTC/USDT", "ETH/USDT", "BNB/USDT"], description="List of trading pairs")
) -> Dict[str, Any]:
    """
    Get market summary for multiple trading pairs.
    
    Args:
        symbols: List of trading pair symbols
        
    Returns:
        Dictionary containing market summary data
    """
    try:
        async with MarketDataAggregator() as aggregator:
            prices = await aggregator.get_current_prices(symbols)
            
            market_data = {}
            for price in prices:
                market_data[price.symbol] = {
                    "symbol": price.symbol,
                    "name": price.name,
                    "price": price.price,
                    "price_change_24h": price.price_change_24h,
                    "price_change_percentage_24h": price.price_change_percentage_24h,
                    "volume_24h": price.volume_24h,
                    "market_cap": price.market_cap,
                    "source": price.source
                }
            
            # Add any symbols that weren't found
            for symbol in symbols:
                if symbol not in market_data:
                    market_data[symbol] = {"error": "Data not available"}
            
            return {
                "market_summary": market_data,
                "symbols_count": len(symbols),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error fetching market summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch market summary"
        )


@router.get("/news/{symbol}")
async def get_coin_news(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of news articles to return")
) -> Dict[str, Any]:
    """
    Get news articles for a specific coin.
    
    Args:
        symbol: Trading pair symbol (e.g., BTC/USDT)
        limit: Number of news articles to return (1-50)
        
    Returns:
        Dictionary containing news articles
    """
    try:
        # Extract coin symbol from trading pair
        coin_symbol = symbol.split('/')[0] if '/' in symbol else symbol
        
        async with MarketDataAggregator() as aggregator:
            news_articles = await aggregator.get_news_analysis([coin_symbol], limit)
            
            news_data = []
            for article in news_articles:
                news_data.append({
                    "title": article.title,
                    "description": article.description,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at,
                    "sentiment": article.sentiment,
                    "sentiment_score": article.sentiment_score,
                    "importance": article.importance,
                    "currencies": article.currencies,
                    "source_type": article.source_type
                })
            
            return {
                "symbol": symbol,
                "coin": coin_symbol,
                "news": news_data,
                "count": len(news_data),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch news for {symbol}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for market data service.
    
    Returns:
        Dictionary containing health status
    """
    try:
        # Test real API connectivity
        async with MarketDataAggregator() as aggregator:
            # Test basic functionality
            test_prices = await aggregator.get_current_prices(["BTC/USDT"])
            api_healthy = bool(test_prices)
            
            return {
                "status": "healthy" if api_healthy else "degraded",
                "api_connectivity": api_healthy,
                "api_status": aggregator.api_status,
                "data_sources": {
                    "binance": aggregator.api_status.get('binance', False),
                    "coinmarketcap": aggregator.api_status.get('coinmarketcap', False),
                    "coinmarketcal": aggregator.api_status.get('coinmarketcal', False),
                    "cryptopanic": aggregator.api_status.get('cryptopanic', False),
                    "news_api": aggregator.api_status.get('news_api', False)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "api_connectivity": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/analysis")
async def get_comprehensive_analysis(
    symbols: List[str] = Query(default=["BTC/USDT", "ETH/USDT", "BNB/USDT"], description="List of trading pairs to analyze"),
    include_news: bool = Query(default=True, description="Include news analysis"),
    include_events: bool = Query(default=True, description="Include upcoming events"),
    include_sentiment: bool = Query(default=True, description="Include sentiment analysis")
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
        async with MarketDataAggregator() as aggregator:
            analysis = await aggregator.get_comprehensive_market_analysis(
                symbols=symbols,
                include_news=include_news,
                include_events=include_events,
                include_sentiment=include_sentiment
            )
            
            return analysis
        
    except Exception as e:
        logger.error(f"Error fetching comprehensive analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch comprehensive market analysis"
        )


@router.get("/sentiment/{symbol}")
async def get_sentiment_analysis(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get sentiment analysis for a specific cryptocurrency.
    
    Args:
        symbol: Trading pair symbol (e.g., BTC/USDT)
        days: Number of days to analyze
        
    Returns:
        Sentiment analysis data
    """
    try:
        # Extract coin symbol from trading pair
        coin_symbol = symbol.split('/')[0] if '/' in symbol else symbol
        
        async with MarketDataAggregator() as aggregator:
            sentiment = await aggregator.get_sentiment_analysis(coin_symbol, days)
            
            if not sentiment:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sentiment data not found for {symbol}"
                )
            
            return {
                "symbol": symbol,
                "coin": coin_symbol,
                "sentiment": sentiment.sentiment,
                "sentiment_score": sentiment.sentiment_score,
                "confidence": sentiment.confidence,
                "post_count": sentiment.post_count,
                "sentiment_distribution": sentiment.sentiment_distribution,
                "analyzed_days": sentiment.analyzed_days,
                "source": sentiment.source,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sentiment for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sentiment analysis for {symbol}"
        )


@router.get("/events")
async def get_upcoming_events(
    days_ahead: int = Query(default=7, ge=1, le=30, description="Number of days to look ahead"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of events to return")
) -> Dict[str, Any]:
    """
    Get upcoming cryptocurrency events.
    
    Args:
        days_ahead: Number of days to look ahead
        limit: Maximum number of events to return
        
    Returns:
        List of upcoming events
    """
    try:
        async with MarketDataAggregator() as aggregator:
            events = await aggregator.get_upcoming_events(days_ahead)
            
            events_data = []
            for event in events[:limit]:
                events_data.append({
                    "title": event.title,
                    "description": event.description,
                    "date_event": event.date_event,
                    "source": event.source,
                    "importance": event.importance,
                    "currencies": event.currencies,
                    "category": event.category,
                    "votes": event.votes
                })
            
            return {
                "events": events_data,
                "count": len(events_data),
                "days_ahead": days_ahead,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch upcoming events"
        )
