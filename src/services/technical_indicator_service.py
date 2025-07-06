from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import asyncio

from src.models.technical_indicator import TechnicalIndicator
from src.schemas.technical_indicator import TechnicalIndicatorCreate, TechnicalIndicatorUpdate


class TechnicalIndicatorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, indicator_id: int) -> Optional[TechnicalIndicator]:
        """Get technical indicator by ID"""
        result = await self.db.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[int] = None,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> List[TechnicalIndicator]:
        """Get multiple technical indicators with filters"""
        query = select(TechnicalIndicator)
        
        conditions = []
        if asset_id:
            conditions.append(TechnicalIndicator.asset_id == asset_id)
        if indicator_type:
            conditions.append(TechnicalIndicator.indicator_type == indicator_type)
        if timeframe:
            conditions.append(TechnicalIndicator.timeframe == timeframe)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(TechnicalIndicator.calculated_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, indicator_in: TechnicalIndicatorCreate) -> TechnicalIndicator:
        """Create new technical indicator"""
        db_indicator = TechnicalIndicator(
            asset_id=indicator_in.asset_id,
            indicator_type=indicator_in.indicator_type,
            timeframe=indicator_in.timeframe,
            value=indicator_in.value,
            parameters=indicator_in.parameters,
            calculated_at=datetime.utcnow()
        )
        
        self.db.add(db_indicator)
        await self.db.commit()
        await self.db.refresh(db_indicator)
        
        return db_indicator

    async def update(
        self, 
        indicator_id: int, 
        indicator_in: TechnicalIndicatorUpdate
    ) -> Optional[TechnicalIndicator]:
        """Update technical indicator"""
        result = await self.db.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id)
        )
        db_indicator = result.scalar_one_or_none()
        
        if not db_indicator:
            return None
        
        update_data = indicator_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_indicator, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_indicator)
        
        return db_indicator

    async def delete(self, indicator_id: int) -> Optional[TechnicalIndicator]:
        """Delete technical indicator"""
        result = await self.db.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id)
        )
        db_indicator = result.scalar_one_or_none()
        
        if not db_indicator:
            return None
        
        await self.db.delete(db_indicator)
        await self.db.commit()
        
        return db_indicator

    async def get_by_asset_and_type(
        self,
        asset_id: int,
        indicator_type: str,
        timeframe: str,
        limit: int = 1
    ) -> List[TechnicalIndicator]:
        """Get latest indicators for specific asset, type and timeframe"""
        query = select(TechnicalIndicator).where(
            and_(
                TechnicalIndicator.asset_id == asset_id,
                TechnicalIndicator.indicator_type == indicator_type,
                TechnicalIndicator.timeframe == timeframe
            )
        ).order_by(TechnicalIndicator.calculated_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest_for_asset(
        self,
        asset_id: int,
        timeframe: str = "1h"
    ) -> Dict[str, TechnicalIndicator]:
        """Get latest indicators for an asset grouped by type"""
        query = select(TechnicalIndicator).where(
            and_(
                TechnicalIndicator.asset_id == asset_id,
                TechnicalIndicator.timeframe == timeframe
            )
        ).order_by(TechnicalIndicator.calculated_at.desc())
        
        result = await self.db.execute(query)
        indicators = result.scalars().all()
        
        # Group by indicator type, keeping only the latest
        latest_indicators = {}
        for indicator in indicators:
            if indicator.indicator_type not in latest_indicators:
                latest_indicators[indicator.indicator_type] = indicator
        
        return latest_indicators

    async def calculate_rsi(
        self,
        asset_id: int,
        timeframe: str = "1h",
        period: int = 14
    ) -> Optional[float]:
        """Calculate RSI indicator (mock implementation)"""
        # In a real implementation, this would fetch price data and calculate RSI
        # For now, return a mock value
        import random
        rsi_value = random.uniform(20, 80)
        
        # Store the calculated indicator
        indicator_in = TechnicalIndicatorCreate(
            asset_id=asset_id,
            indicator_type="RSI",
            timeframe=timeframe,
            value=rsi_value,
            parameters={"period": period}
        )
        
        await self.create(indicator_in)
        return rsi_value

    async def calculate_moving_average(
        self,
        asset_id: int,
        timeframe: str = "1h",
        period: int = 20,
        ma_type: str = "SMA"
    ) -> Optional[float]:
        """Calculate Moving Average indicator (mock implementation)"""
        # In a real implementation, this would fetch price data and calculate MA
        # For now, return a mock value
        import random
        ma_value = random.uniform(40000, 60000)
        
        # Store the calculated indicator
        indicator_in = TechnicalIndicatorCreate(
            asset_id=asset_id,
            indicator_type=ma_type,
            timeframe=timeframe,
            value=ma_value,
            parameters={"period": period}
        )
        
        await self.create(indicator_in)
        return ma_value

    async def calculate_exponential_moving_average(
        self,
        asset_id: int,
        timeframe: str = "1h",
        period: int = 12
    ) -> Optional[float]:
        """Calculate Exponential Moving Average indicator (mock implementation)"""
        # In a real implementation, this would fetch price data and calculate EMA
        # For now, return a mock value
        import random
        ema_value = random.uniform(41000, 59000)
        
        # Store the calculated indicator
        indicator_in = TechnicalIndicatorCreate(
            asset_id=asset_id,
            indicator_type="EMA",
            timeframe=timeframe,
            value=ema_value,
            parameters={"period": period}
        )
        
        await self.create(indicator_in)
        return ema_value

    async def calculate_multiple_indicators(
        self,
        asset_id: int,
        timeframe: str = "1h",
        indicators: List[str] = None
    ) -> Dict[str, Any]:
        """Calculate multiple indicators for an asset"""
        if not indicators:
            indicators = ["RSI", "SMA", "EMA"]
        
        results = {}
        
        for indicator in indicators:
            if indicator == "RSI":
                value = await self.calculate_rsi(asset_id, timeframe)
                results["RSI"] = {
                    "value": value,
                    "signal": "oversold" if value < 30 else "overbought" if value > 70 else "neutral"
                }
            elif indicator in ["MA", "SMA"]:
                value = await self.calculate_moving_average(asset_id, timeframe, ma_type="SMA")
                results["SMA"] = {
                    "value": value,
                    "period": 20
                }
            elif indicator == "EMA":
                value = await self.calculate_exponential_moving_average(asset_id, timeframe)
                results["EMA"] = {
                    "value": value,
                    "period": 12
                }
        
        return results

    async def generate_trading_signals(
        self,
        asset_id: int,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """Generate trading signals based on technical indicators"""
        latest_indicators = await self.get_latest_for_asset(asset_id, timeframe)
        
        signals = []
        overall_signal = "hold"
        confidence = 0.5
        
        if "RSI" in latest_indicators:
            rsi = latest_indicators["RSI"]
            if rsi.value < 30:
                signals.append({"type": "buy", "reason": "RSI oversold", "strength": 0.7})
            elif rsi.value > 70:
                signals.append({"type": "sell", "reason": "RSI overbought", "strength": 0.7})
        
        if "SMA" in latest_indicators and "EMA" in latest_indicators:
            sma = latest_indicators["SMA"]
            ema = latest_indicators["EMA"]
            if ema.value > sma.value:
                signals.append({"type": "buy", "reason": "EMA above SMA", "strength": 0.6})
            elif ema.value < sma.value:
                signals.append({"type": "sell", "reason": "EMA below SMA", "strength": 0.6})
        
        # Determine overall signal
        buy_signals = [s for s in signals if s["type"] == "buy"]
        sell_signals = [s for s in signals if s["type"] == "sell"]
        
        if len(buy_signals) > len(sell_signals):
            overall_signal = "buy"
            confidence = sum(s["strength"] for s in buy_signals) / len(buy_signals)
        elif len(sell_signals) > len(buy_signals):
            overall_signal = "sell"
            confidence = sum(s["strength"] for s in sell_signals) / len(sell_signals)
        
        return {
            "signal": overall_signal,
            "confidence": round(confidence, 2),
            "individual_signals": signals,
            "indicators_used": list(latest_indicators.keys()),
            "generated_at": datetime.utcnow().isoformat()
        }

    async def cleanup_old_indicators(self, days_old: int = 30) -> int:
        """Delete indicators older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.db.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.calculated_at < cutoff_date)
        )
        old_indicators = result.scalars().all()
        
        deleted_count = 0
        for indicator in old_indicators:
            await self.db.delete(indicator)
            deleted_count += 1
        
        await self.db.commit()
        return deleted_count
