from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")


class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = Field(None, description="Username from token")
    user_id: Optional[int] = Field(None, description="User ID from token")


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[int] = None
    exp: Optional[int] = None


class RefreshToken(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")
