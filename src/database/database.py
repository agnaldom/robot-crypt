"""
Database configuration and session management for Robot-Crypt.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

# Create declarative base
Base = declarative_base()

# Async database engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Async session maker
async_session_maker = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


# Dependency to get database session
async def get_database() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# For synchronous operations (migrations, etc.)
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""),
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Sync session maker
sync_session_maker = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def get_sync_database():
    """Get synchronous database session."""
    db = sync_session_maker()
    try:
        yield db
    finally:
        db.close()
