"""
Assets router for Robot-Crypt API.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_user, get_current_active_superuser
from src.database.database import get_database
from src.schemas.asset import Asset, AssetCreate, AssetUpdate
from src.schemas.user import User
from src.services.asset_service import AssetService

router = APIRouter()


@router.get("/", response_model=List[Asset])
async def read_assets(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_monitored: Optional[bool] = Query(None, description="Filter by monitored status"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve assets with optional filters.
    """
    asset_service = AssetService(db)
    assets = await asset_service.get_multi(
        skip=skip,
        limit=limit,
        is_active=is_active,
        is_monitored=is_monitored,
        asset_type=asset_type
    )
    return assets


@router.post("/", response_model=Asset)
async def create_asset(
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new asset.
    """
    asset_service = AssetService(db)
    
    # Check if asset already exists
    existing_asset = await asset_service.get_by_symbol(asset_in.symbol)
    if existing_asset:
        raise HTTPException(
            status_code=400,
            detail="The asset with this symbol already exists in the system.",
        )
    
    asset = await asset_service.create(asset_in)
    return asset


@router.get("/monitored", response_model=List[Asset])
async def read_monitored_assets(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all monitored assets.
    """
    asset_service = AssetService(db)
    assets = await asset_service.get_monitored_assets()
    return assets


@router.get("/search", response_model=List[Asset])
async def search_assets(
    q: str = Query(..., description="Search query"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Search assets by symbol or name.
    """
    asset_service = AssetService(db)
    assets = await asset_service.search_assets(q)
    return assets


@router.get("/{asset_id}", response_model=Asset)
async def read_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get asset by ID.
    """
    asset_service = AssetService(db)
    asset = await asset_service.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=Asset)
async def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update an asset.
    """
    asset_service = AssetService(db)
    asset = await asset_service.update(asset_id, asset_in)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", response_model=Asset)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete an asset.
    """
    asset_service = AssetService(db)
    asset = await asset_service.delete(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{symbol}/price", response_model=Asset)
async def update_asset_price(
    symbol: str,
    price: float,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update asset price.
    """
    asset_service = AssetService(db)
    asset = await asset_service.update_price(symbol, price)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/symbol/{symbol}", response_model=Asset)
async def read_asset_by_symbol(
    symbol: str,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get asset by symbol.
    """
    asset_service = AssetService(db)
    asset = await asset_service.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
