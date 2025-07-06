from typing import List, Optional, Union, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Remove direct import to avoid circular dependency
# from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


class UserService:
    """User service for async database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get multiple users with pagination."""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, user_in: UserCreate) -> User:
        """Create a new user."""
        from src.core.security import get_password_hash  # Delayed import
        
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
            preferences=user_in.preferences or {}
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
    
    async def update(self, user_id: int, user_in: Union[UserUpdate, Dict[str, Any]]) -> Optional[User]:
        """Update a user."""
        db_user = await self.get(user_id)
        if not db_user:
            return None
        
        # Convert to dict if it's a Pydantic model
        update_data = user_in if isinstance(user_in, dict) else user_in.model_dump(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data and update_data["password"]:
            from src.core.security import get_password_hash  # Delayed import
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        # Update user attributes
        for field, value in update_data.items():
            if hasattr(db_user, field) and field != "id":
                setattr(db_user, field, value)
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
    
    async def delete(self, user_id: int) -> Optional[User]:
        """Delete a user."""
        db_user = await self.get(user_id)
        if not db_user:
            return None
        
        await self.db.delete(db_user)
        await self.db.commit()
        return db_user
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = await self.get_by_email(email)
        if not user:
            return None
        
        from src.core.security import verify_password  # Delayed import
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
