"""
Core database module providing async session dependency.
This module provides a consistent interface for database sessions across the application.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.database import get_database


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.
    
    This function provides an async database session for dependency injection
    in FastAPI routes. It wraps the existing get_database function to maintain
    consistency with the expected interface.
    
    Yields:
        AsyncSession: An async SQLAlchemy session
    """
    async for session in get_database():
        yield session


# Alias for backward compatibility with websocket endpoints
get_db = get_async_session
