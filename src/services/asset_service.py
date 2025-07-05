"""
Asset service for Robot-Crypt API.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.models.asset import Asset
from src.schemas.asset import AssetCreate, AssetUpdate


class AssetService:
    """Asset service for async database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, asset_id: int) -> Optional[Asset]:
        """Get an asset by ID."""
        result = await self.db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get an asset by symbol."""
        result = await self.db.execute(
            select(Asset).where(Asset.symbol == symbol)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_monitored: Optional[bool] = None,
        asset_type: Optional[str] = None
    ) -> List[Asset]:
        """Get multiple assets with optional filters."""
        query = select(Asset)
        
        if is_active is not None:
            query = query.where(Asset.is_active == is_active)
        
        if is_monitored is not None:
            query = query.where(Asset.is_monitored == is_monitored)
        
        if asset_type:
            query = query.where(Asset.type == asset_type)
        
        query = query.offset(skip).limit(limit).order_by(Asset.symbol)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, asset_in: AssetCreate) -> Asset:
        """Create a new asset."""
        db_asset = Asset(
            symbol=asset_in.symbol,
            name=asset_in.name,
            type=asset_in.type,
            current_price=asset_in.current_price,
            market_cap=asset_in.market_cap,
            volume_24h=asset_in.volume_24h,
            is_active=asset_in.is_active,
            is_monitored=asset_in.is_monitored,
            metadata=asset_in.metadata or {}
        )
        self.db.add(db_asset)
        await self.db.commit()
        await self.db.refresh(db_asset)
        return db_asset
    
    async def update(self, asset_id: int, asset_in: AssetUpdate) -> Optional[Asset]:
        """Update an asset."""
        db_asset = await self.get(asset_id)
        if not db_asset:
            return None
        
        update_data = asset_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_asset, field):
                setattr(db_asset, field, value)
        
        self.db.add(db_asset)
        await self.db.commit()
        await self.db.refresh(db_asset)
        return db_asset
    
    async def delete(self, asset_id: int) -> Optional[Asset]:
        """Delete an asset."""
        db_asset = await self.get(asset_id)
        if not db_asset:
            return None
        
        await self.db.delete(db_asset)
        await self.db.commit()
        return db_asset
    
    async def update_price(self, symbol: str, price: float) -> Optional[Asset]:
        """Update asset current price."""
        db_asset = await self.get_by_symbol(symbol)
        if not db_asset:
            return None
        
        db_asset.current_price = price
        self.db.add(db_asset)
        await self.db.commit()
        await self.db.refresh(db_asset)
        return db_asset
    
    async def get_monitored_assets(self) -> List[Asset]:
        """Get all monitored assets."""
        result = await self.db.execute(
            select(Asset).where(
                Asset.is_monitored == True,
                Asset.is_active == True
            ).order_by(Asset.symbol)
        )
        return result.scalars().all()
    
    async def search_assets(self, query: str) -> List[Asset]:
        """Search assets by symbol or name."""
        search_query = f"%{query}%"
        result = await self.db.execute(
            select(Asset).where(
                (Asset.symbol.ilike(search_query)) |
                (Asset.name.ilike(search_query))
            ).limit(10)
        )
        return result.scalars().all()
