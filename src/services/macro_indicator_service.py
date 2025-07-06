from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import asyncio

from src.models.macro_indicator import MacroIndicator
from src.schemas.macro_indicator import MacroIndicatorCreate, MacroIndicatorUpdate


class MacroIndicatorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, indicator_id: int) -> Optional[MacroIndicator]:
        """Get macro indicator by ID"""
        result = await self.db.execute(
            select(MacroIndicator).where(MacroIndicator.id == indicator_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        impact: Optional[str] = None
    ) -> List[MacroIndicator]:
        """Get multiple macro indicators with filters"""
        query = select(MacroIndicator)
        
        conditions = []
        if category:
            conditions.append(MacroIndicator.category == category)
        if impact:
            conditions.append(MacroIndicator.impact == impact)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(MacroIndicator.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, indicator_in: MacroIndicatorCreate) -> MacroIndicator:
        """Create new macro indicator"""
        db_indicator = MacroIndicator(
            name=indicator_in.name,
            category=indicator_in.category,
            value=indicator_in.value,
            description=indicator_in.description,
            source=indicator_in.source,
            impact=indicator_in.impact,
            event_date=indicator_in.event_date,
            metadata=indicator_in.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_indicator)
        await self.db.commit()
        await self.db.refresh(db_indicator)
        
        return db_indicator

    async def update(
        self, 
        indicator_id: int, 
        indicator_in: MacroIndicatorUpdate
    ) -> Optional[MacroIndicator]:
        """Update macro indicator"""
        result = await self.db.execute(
            select(MacroIndicator).where(MacroIndicator.id == indicator_id)
        )
        db_indicator = result.scalar_one_or_none()
        
        if not db_indicator:
            return None
        
        update_data = indicator_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_indicator, field, value)
        
        db_indicator.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(db_indicator)
        
        return db_indicator

    async def delete(self, indicator_id: int) -> Optional[MacroIndicator]:
        """Delete macro indicator"""
        result = await self.db.execute(
            select(MacroIndicator).where(MacroIndicator.id == indicator_id)
        )
        db_indicator = result.scalar_one_or_none()
        
        if not db_indicator:
            return None
        
        await self.db.delete(db_indicator)
        await self.db.commit()
        
        return db_indicator

    async def get_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[MacroIndicator]:
        """Get indicators by category"""
        query = select(MacroIndicator).where(
            MacroIndicator.category == category
        ).order_by(MacroIndicator.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_impact_level(
        self,
        impact: str,
        limit: int = 50
    ) -> List[MacroIndicator]:
        """Get indicators by impact level"""
        query = select(MacroIndicator).where(
            MacroIndicator.impact == impact
        ).order_by(MacroIndicator.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_events(
        self,
        days_ahead: int = 7
    ) -> List[MacroIndicator]:
        """Get upcoming economic events"""
        from datetime import timedelta
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)
        
        query = select(MacroIndicator).where(
            and_(
                MacroIndicator.event_date.isnot(None),
                MacroIndicator.event_date >= start_date,
                MacroIndicator.event_date <= end_date
            )
        ).order_by(MacroIndicator.event_date.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_events(
        self,
        days_back: int = 7
    ) -> List[MacroIndicator]:
        """Get recent economic events"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        end_date = datetime.utcnow()
        
        query = select(MacroIndicator).where(
            and_(
                MacroIndicator.event_date.isnot(None),
                MacroIndicator.event_date >= start_date,
                MacroIndicator.event_date <= end_date
            )
        ).order_by(MacroIndicator.event_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_fear_greed_index(self) -> Optional[MacroIndicator]:
        """Get latest Fear & Greed Index"""
        query = select(MacroIndicator).where(
            and_(
                MacroIndicator.category == "fear_greed",
                MacroIndicator.name == "Fear & Greed Index"
            )
        ).order_by(MacroIndicator.created_at.desc()).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_fear_greed_index(
        self,
        value: float,
        classification: str = None
    ) -> MacroIndicator:
        """Create or update Fear & Greed Index"""
        
        # Determine classification based on value
        if classification is None:
            if value <= 25:
                classification = "Extreme Fear"
            elif value <= 45:
                classification = "Fear"
            elif value <= 55:
                classification = "Neutral"
            elif value <= 75:
                classification = "Greed"
            else:
                classification = "Extreme Greed"
        
        indicator_in = MacroIndicatorCreate(
            name="Fear & Greed Index",
            category="fear_greed",
            value=value,
            description=f"Market sentiment indicator showing {classification}",
            source="Alternative.me",
            impact="medium",
            metadata={
                "classification": classification,
                "scale": "0-100",
                "interpretation": {
                    "0-25": "Extreme Fear",
                    "25-45": "Fear", 
                    "45-55": "Neutral",
                    "55-75": "Greed",
                    "75-100": "Extreme Greed"
                }
            }
        )
        
        return await self.create(indicator_in)

    async def create_economic_event(
        self,
        name: str,
        event_date: datetime,
        impact: str,
        description: str = None,
        value: float = None,
        source: str = None
    ) -> MacroIndicator:
        """Create economic event indicator"""
        
        indicator_in = MacroIndicatorCreate(
            name=name,
            category="economic_event",
            value=value,
            description=description or f"Economic event: {name}",
            source=source or "Economic Calendar",
            impact=impact,
            event_date=event_date,
            metadata={
                "event_type": "scheduled",
                "timezone": "UTC"
            }
        )
        
        return await self.create(indicator_in)

    async def create_market_index(
        self,
        name: str,
        value: float,
        change_percent: float = None,
        description: str = None
    ) -> MacroIndicator:
        """Create market index indicator"""
        
        metadata = {}
        if change_percent is not None:
            metadata["change_percent"] = change_percent
            metadata["direction"] = "up" if change_percent > 0 else "down" if change_percent < 0 else "flat"
        
        indicator_in = MacroIndicatorCreate(
            name=name,
            category="index",
            value=value,
            description=description or f"Market index: {name}",
            source="Market Data",
            impact="medium",
            metadata=metadata
        )
        
        return await self.create(indicator_in)

    async def get_market_sentiment_analysis(self) -> Dict[str, Any]:
        """Get comprehensive market sentiment analysis"""
        
        # Get Fear & Greed Index
        fear_greed = await self.get_fear_greed_index()
        
        # Get recent high impact events
        recent_events = await self.get_recent_events(days_back=7)
        high_impact_events = [e for e in recent_events if e.impact == "high"]
        
        # Get upcoming events
        upcoming_events = await self.get_upcoming_events(days_ahead=7)
        upcoming_high_impact = [e for e in upcoming_events if e.impact == "high"]
        
        # Get latest indices
        indices = await self.get_by_category("index", limit=10)
        
        sentiment_score = 50  # Neutral default
        sentiment_factors = []
        
        if fear_greed:
            sentiment_score = fear_greed.value
            sentiment_factors.append({
                "factor": "Fear & Greed Index",
                "impact": fear_greed.metadata.get("classification", "Unknown"),
                "weight": 0.4
            })
        
        # Analyze recent high impact events
        if high_impact_events:
            negative_events = sum(1 for e in high_impact_events if any(
                word in e.name.lower() for word in ["crisis", "recession", "crash", "decline", "fall"]
            ))
            positive_events = sum(1 for e in high_impact_events if any(
                word in e.name.lower() for word in ["growth", "rise", "bull", "recovery", "gain"]
            ))
            
            if negative_events > positive_events:
                sentiment_score -= 10
                sentiment_factors.append({
                    "factor": "Recent Negative Events",
                    "impact": "bearish",
                    "weight": 0.2
                })
            elif positive_events > negative_events:
                sentiment_score += 10
                sentiment_factors.append({
                    "factor": "Recent Positive Events",
                    "impact": "bullish",
                    "weight": 0.2
                })
        
        # Analyze market indices trends
        bullish_indices = sum(1 for idx in indices if 
                            idx.metadata.get("change_percent", 0) > 2)
        bearish_indices = sum(1 for idx in indices if 
                            idx.metadata.get("change_percent", 0) < -2)
        
        if bullish_indices > bearish_indices:
            sentiment_score += 5
            sentiment_factors.append({
                "factor": "Market Indices",
                "impact": "bullish",
                "weight": 0.3
            })
        elif bearish_indices > bullish_indices:
            sentiment_score -= 5
            sentiment_factors.append({
                "factor": "Market Indices",
                "impact": "bearish",
                "weight": 0.3
            })
        
        # Ensure sentiment score is within bounds
        sentiment_score = max(0, min(100, sentiment_score))
        
        # Determine overall sentiment
        if sentiment_score <= 25:
            overall_sentiment = "Very Bearish"
        elif sentiment_score <= 40:
            overall_sentiment = "Bearish"
        elif sentiment_score <= 60:
            overall_sentiment = "Neutral"
        elif sentiment_score <= 75:
            overall_sentiment = "Bullish"
        else:
            overall_sentiment = "Very Bullish"
        
        return {
            "sentiment_score": round(sentiment_score, 1),
            "overall_sentiment": overall_sentiment,
            "sentiment_factors": sentiment_factors,
            "fear_greed_index": {
                "value": fear_greed.value if fear_greed else None,
                "classification": fear_greed.metadata.get("classification") if fear_greed else None,
                "last_updated": fear_greed.created_at.isoformat() if fear_greed else None
            },
            "recent_events": [
                {
                    "name": event.name,
                    "impact": event.impact,
                    "date": event.event_date.isoformat() if event.event_date else None
                }
                for event in high_impact_events[:5]
            ],
            "upcoming_events": [
                {
                    "name": event.name,
                    "impact": event.impact,
                    "date": event.event_date.isoformat() if event.event_date else None
                }
                for event in upcoming_high_impact[:5]
            ],
            "market_indices": [
                {
                    "name": idx.name,
                    "value": idx.value,
                    "change_percent": idx.metadata.get("change_percent"),
                    "direction": idx.metadata.get("direction")
                }
                for idx in indices[:5]
            ],
            "analysis_date": datetime.utcnow().isoformat()
        }

    async def cleanup_old_indicators(self, days_old: int = 90) -> int:
        """Delete indicators older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.db.execute(
            select(MacroIndicator).where(MacroIndicator.created_at < cutoff_date)
        )
        old_indicators = result.scalars().all()
        
        deleted_count = 0
        for indicator in old_indicators:
            await self.db.delete(indicator)
            deleted_count += 1
        
        await self.db.commit()
        return deleted_count

    async def get_statistics(self) -> Dict[str, Any]:
        """Get macro indicators statistics"""
        
        # Total count
        total_result = await self.db.execute(select(MacroIndicator))
        total_count = len(total_result.scalars().all())
        
        # Count by category
        categories_result = await self.db.execute(
            select(MacroIndicator.category).distinct()
        )
        categories = categories_result.scalars().all()
        
        category_counts = {}
        for category in categories:
            cat_result = await self.db.execute(
                select(MacroIndicator).where(MacroIndicator.category == category)
            )
            category_counts[category] = len(cat_result.scalars().all())
        
        # Count by impact
        impacts_result = await self.db.execute(
            select(MacroIndicator.impact).distinct()
        )
        impacts = impacts_result.scalars().all()
        
        impact_counts = {}
        for impact in impacts:
            if impact:  # Skip None values
                impact_result = await self.db.execute(
                    select(MacroIndicator).where(MacroIndicator.impact == impact)
                )
                impact_counts[impact] = len(impact_result.scalars().all())
        
        return {
            "total_indicators": total_count,
            "categories": category_counts,
            "impact_levels": impact_counts
        }
