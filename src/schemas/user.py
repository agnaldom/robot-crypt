from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# Shared properties
class UserBase(BaseModel):
    """Base user schema."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    full_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a user."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for updating a user."""
    password: Optional[str] = Field(None, min_length=8)
    
    @field_validator("preferences")
    def validate_preferences(cls, v):
        if v is None:
            return {}
        return v


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    """Base schema for user in database."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return via API
class User(UserInDBBase):
    """Schema for user returned in API responses."""
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    """Schema for user with hashed password."""
    hashed_password: str
