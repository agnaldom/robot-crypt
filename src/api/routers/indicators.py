"""
Indicators router for Robot-Crypt API.
"""

from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_user, get_current_active_superuser
from src.database.database import get_database
from src.schemas.technical_indicator import TechnicalIndicator, TechnicalIndicatorCreate
from src.schemas.macro_indicator import MacroIndicator, MacroIndicatorCreate
from src.schemas.user import User
from src.services.asset_service import AssetService
from src.services.technical_indicator_service import TechnicalIndicatorService
from src.services.macro_indicator_service import MacroIndicatorService

router = APIRouter()


@router.get("/technical", response_model=List[TechnicalIndicator])
async def read_technical_indicators(
    skip: int = 0,
    limit: int = 100,
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    indicator_type: Optional[str] = Query(None, description="Filter by indicator type"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve technical indicators with optional filters.
    """
    technical_service = TechnicalIndicatorService(db)
    indicators = await technical_service.get_multi(
        skip=skip,
        limit=limit,
        asset_id=asset_id,
        indicator_type=indicator_type,
        timeframe=timeframe
    )
    return indicators


@router.post("/technical", response_model=TechnicalIndicator)
async def create_technical_indicator(
    indicator_in: TechnicalIndicatorCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new technical indicator.
    """
    technical_service = TechnicalIndicatorService(db)
    indicator = await technical_service.create(indicator_in)
    return indicator


@router.get("/macro", response_model=List[MacroIndicator])
async def read_macro_indicators(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by category"),
    impact: Optional[str] = Query(None, description="Filter by impact level"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve macro indicators with optional filters.
    """
    macro_service = MacroIndicatorService(db)
    indicators = await macro_service.get_multi(
        skip=skip,
        limit=limit,
        category=category,
        impact=impact
    )
    return indicators


@router.post("/macro", response_model=MacroIndicator)
async def create_macro_indicator(
    indicator_in: MacroIndicatorCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new macro indicator.
    """
    macro_service = MacroIndicatorService(db)
    indicator = await macro_service.create(indicator_in)
    return indicator


@router.post("/calculate")
async def calculate_indicators(
    asset_symbol: str,
    timeframe: str = "1h",
    indicators: List[str] = Query(["RSI", "MA", "EMA"], description="List of indicators to calculate"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Calculate technical indicators for an asset.
    """
    asset_service = AssetService(db)
    technical_service = TechnicalIndicatorService(db)
    
    asset = await asset_service.get_by_symbol(asset_symbol)
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Calculate requested indicators using the service
    calculated_indicators = await technical_service.calculate_multiple_indicators(
        asset_id=asset.id,
        timeframe=timeframe,
        indicators=indicators
    )
    
    return {
        "asset_symbol": asset_symbol,
        "asset_id": asset.id,
        "timeframe": timeframe,
        "indicators": calculated_indicators,
        "calculated_at": datetime.now().isoformat()
    }


@router.get("/signals")
async def get_trading_signals(
    asset_symbol: Optional[str] = Query(None, description="Filter by asset symbol"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    strength_min: Optional[float] = Query(None, ge=0, le=1, description="Minimum signal strength"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get trading signals based on technical indicators.
    """
    asset_service = AssetService(db)
    technical_service = TechnicalIndicatorService(db)
    
    signals = []
    
    if asset_symbol:
        # Generate signals for specific asset
        asset = await asset_service.get_by_symbol(asset_symbol)
        if asset:
            signal_data = await technical_service.generate_trading_signals(
                asset_id=asset.id,
                timeframe="1h"
            )
            
            signals.append({
                "asset_symbol": asset_symbol,
                "signal_type": signal_data["signal"],
                "strength": signal_data["confidence"],
                "price": asset.current_price,
                "reasoning": ", ".join([s["reason"] for s in signal_data["individual_signals"]]),
                "indicators_used": signal_data["indicators_used"],
                "individual_signals": signal_data["individual_signals"],
                "timestamp": signal_data["generated_at"]
            })
    else:
        # Generate signals for multiple assets
        popular_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT"]
        
        for symbol in popular_symbols:
            asset = await asset_service.get_by_symbol(symbol)
            if asset:
                signal_data = await technical_service.generate_trading_signals(
                    asset_id=asset.id,
                    timeframe="1h"
                )
                
                signals.append({
                    "asset_symbol": symbol,
                    "signal_type": signal_data["signal"],
                    "strength": signal_data["confidence"],
                    "price": asset.current_price,
                    "reasoning": ", ".join([s["reason"] for s in signal_data["individual_signals"]]) if signal_data["individual_signals"] else "No specific signals",
                    "indicators_used": signal_data["indicators_used"],
                    "timestamp": signal_data["generated_at"]
                })
    
    # Apply filters
    if signal_type:
        signals = [s for s in signals if s["signal_type"] == signal_type]
    
    if strength_min is not None:
        signals = [s for s in signals if s["strength"] >= strength_min]
    
    return {
        "signals": signals,
        "generated_at": datetime.now().isoformat(),
        "total_signals": len(signals)
    }


@router.get("/market-overview")
async def get_market_overview(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get overall market overview with key indicators.
    """
    macro_service = MacroIndicatorService(db)
    asset_service = AssetService(db)
    
    # Get market sentiment analysis
    sentiment_analysis = await macro_service.get_market_sentiment_analysis()
    
    # Get Fear & Greed Index
    fear_greed = await macro_service.get_fear_greed_index()
    
    # Get recent economic events
    recent_events = await macro_service.get_recent_events(days_back=3)
    upcoming_events = await macro_service.get_upcoming_events(days_ahead=7)
    
    # Get market indices
    indices = await macro_service.get_by_category("index", limit=5)
    
    # Mock some market data for demonstration
    # In a real implementation, this would come from market data APIs
    mock_market_data = {
        "market_trend": {
            "direction": "bullish" if sentiment_analysis["sentiment_score"] > 60 else "bearish" if sentiment_analysis["sentiment_score"] < 40 else "sideways",
            "strength": abs(sentiment_analysis["sentiment_score"] - 50) / 50,
            "timeframe": "daily"
        },
        "volume_analysis": {
            "total_volume_24h": 28500000000,
            "change_24h": -5.2,
            "above_average": False
        },
        "top_movers": {
            "gainers": [
                {"symbol": "ADA/USDT", "change": 8.5},
                {"symbol": "SOL/USDT", "change": 6.2}
            ],
            "losers": [
                {"symbol": "DOGE/USDT", "change": -4.8},
                {"symbol": "SHIB/USDT", "change": -3.2}
            ]
        }
    }
    
    return {
        "fear_greed_index": {
            "value": fear_greed.value if fear_greed else None,
            "classification": fear_greed.metadata.get("classification") if fear_greed else None,
            "last_updated": fear_greed.created_at.isoformat() if fear_greed else None
        },
        "market_sentiment": {
            "score": sentiment_analysis["sentiment_score"],
            "sentiment": sentiment_analysis["overall_sentiment"],
            "factors": sentiment_analysis["sentiment_factors"]
        },
        "market_trend": mock_market_data["market_trend"],
        "volume_analysis": mock_market_data["volume_analysis"],
        "top_movers": mock_market_data["top_movers"],
        "recent_events": [
            {
                "name": event.name,
                "impact": event.impact,
                "date": event.event_date.isoformat() if event.event_date else event.created_at.isoformat()
            }
            for event in recent_events[:3]
        ],
        "upcoming_events": [
            {
                "name": event.name,
                "impact": event.impact,
                "date": event.event_date.isoformat() if event.event_date else None
            }
            for event in upcoming_events[:3]
        ],
        "market_indices": [
            {
                "name": idx.name,
                "value": idx.value,
                "change_percent": idx.metadata.get("change_percent")
            }
            for idx in indices
        ],
        "generated_at": datetime.now().isoformat()
    }
