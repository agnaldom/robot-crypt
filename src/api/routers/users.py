"""
Users router for Robot-Crypt API.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_superuser, get_current_active_user
from src.database.database import get_database
from src.schemas.user import User, UserCreate, UserUpdate
from src.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    user_service = UserService(db)
    users = await user_service.get_multi(skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user_service = UserService(db)
    
    # Check if user already exists
    user = await user_service.get_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    user = await user_service.create(user_in)
    return user


@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    user_service = UserService(db)
    user = await user_service.update(current_user.id, user_in)
    return user


@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/{user_id}", response_model=User)
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database),
) -> Any:
    """
    Get a specific user by id.
    """
    user_service = UserService(db)
    user = await user_service.get(user_id)
    
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_database),
) -> Any:
    """
    Update a user.
    """
    user_service = UserService(db)
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = await user_service.update(user_id, user_in)
    return user
