"""
Market data API router for Robot-Crypt.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.core.config import Settings
from src.core.market_data_client import MarketDataClient
from src.core.logger import logger

router = APIRouter(prefix="/market", tags=["market"])

# Initialize market data client
settings = Settings()
market_client = MarketDataClient(settings.COINGECKO_API_KEY)
executor = ThreadPoolExecutor(max_workers=4)


async def get_market_client() -> MarketDataClient:
    """Dependency to get market data client."""
    return market_client


@router.get("/price/{symbol}")
async def get_current_price(
    symbol: str,
    client: MarketDataClient = Depends(get_market_client)
) -> Dict[str, Any]:
    """
    Get current price for a trading pair.
    
    Args:
        symbol: Trading pair symbol (e.g., BTC/USDT)
        
    Returns:
        Dictionary containing current price data
    """
    try:
        # Run synchronous method in executor
        loop = asyncio.get_event_loop()
        price_data = await loop.run_in_executor(
            executor, client.get_current_price, symbol
        )
        
        if not price_data:
            raise HTTPException(
                status_code=404,
                detail=f"Price data not found for {symbol}"
            )
            
        return {
            "symbol": symbol,
            "price": price_data.get("price"),
            "volume_24h": price_data.get("volume_24h"),
            "price_change_24h": price_data.get("price_change_24h"),
            "market_cap": price_data.get("market_cap"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch price data for {symbol}"
        )


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    days: int = Query(default=7, ge=1, le=365, description="Number of days of historical data"),
    client: MarketDataClient = Depends(get_market_client)
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
        # Run synchronous method in executor
        loop = asyncio.get_event_loop()
        historical_data = await loop.run_in_executor(
            executor, client.get_historical_data, symbol, days
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"Historical data not found for {symbol}"
            )
            
        return {
            "symbol": symbol,
            "days": days,
            "data": historical_data,
            "count": len(historical_data) if historical_data else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical data for {symbol}"
        )


@router.get("/trending")
async def get_trending_coins(
    limit: int = Query(default=10, ge=1, le=50, description="Number of trending coins to return"),
    client: MarketDataClient = Depends(get_market_client)
) -> Dict[str, Any]:
    """
    Get trending coins data.
    
    Args:
        limit: Number of trending coins to return (1-50)
        
    Returns:
        Dictionary containing trending coins data
    """
    try:
        # Run synchronous method in executor
        loop = asyncio.get_event_loop()
        trending_data = await loop.run_in_executor(
            executor, client.get_trending_coins, limit
        )
        
        if not trending_data:
            raise HTTPException(
                status_code=404,
                detail="Trending coins data not available"
            )
            
        return {
            "trending_coins": trending_data,
            "count": len(trending_data) if trending_data else 0,
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
    symbols: List[str] = Query(default=["BTC/USDT", "ETH/USDT", "BNB/USDT"], description="List of trading pairs"),
    client: MarketDataClient = Depends(get_market_client)
) -> Dict[str, Any]:
    """
    Get market summary for multiple trading pairs.
    
    Args:
        symbols: List of trading pair symbols
        
    Returns:
        Dictionary containing market summary data
    """
    try:
        # Run synchronous method in executor for each symbol
        loop = asyncio.get_event_loop()
        
        # Create tasks for parallel execution
        tasks = []
        for symbol in symbols:
            task = loop.run_in_executor(
                executor, client.get_current_price, symbol
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        market_data = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                logger.error(f"Error fetching data for {symbol}: {str(result)}")
                market_data[symbol] = {"error": str(result)}
            else:
                market_data[symbol] = result
        
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
    limit: int = Query(default=10, ge=1, le=50, description="Number of news articles to return"),
    client: MarketDataClient = Depends(get_market_client)
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
        
        # Run synchronous method in executor
        loop = asyncio.get_event_loop()
        news_data = await loop.run_in_executor(
            executor, client.get_coin_news, coin_symbol, limit
        )
        
        if not news_data:
            raise HTTPException(
                status_code=404,
                detail=f"News data not found for {symbol}"
            )
            
        return {
            "symbol": symbol,
            "coin": coin_symbol,
            "news": news_data,
            "count": len(news_data) if news_data else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch news for {symbol}"
        )


@router.get("/health")
async def health_check(
    client: MarketDataClient = Depends(get_market_client)
) -> Dict[str, Any]:
    """
    Health check endpoint for market data service.
    
    Returns:
        Dictionary containing health status
    """
    try:
        # Test API connectivity by fetching BTC price
        loop = asyncio.get_event_loop()
        test_data = await loop.run_in_executor(
            executor, client.get_current_price, "BTC/USDT"
        )
        
        api_healthy = test_data is not None
        
        return {
            "status": "healthy" if api_healthy else "degraded",
            "api_connectivity": api_healthy,
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
