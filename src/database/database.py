"""
Database configuration and session management for Robot-Crypt.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.core.config import settings

# Create declarative base
class Base(DeclarativeBase):
    pass

# Async database engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_reset_on_return='commit',
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


# Safe database context manager that handles connection cleanup properly
class SafeDatabaseSession:
    """Context manager for safe database operations"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = async_session_maker()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type:
                    await self.session.rollback()
                else:
                    await self.session.commit()
            except Exception:
                await self.session.rollback()
            finally:
                await self.session.close()
                self.session = None


async def get_safe_database_session():
    """Get a safe database session that properly handles cleanup"""
    return SafeDatabaseSession()


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


async def cleanup_database_connections():
    """Cleanup database connections gracefully"""
    try:
        await async_engine.dispose()
        print("Database connections cleaned up successfully")
    except Exception as e:
        print(f"Error during database cleanup: {e}")


def cleanup_sync_database_connections():
    """Cleanup synchronous database connections"""
    try:
        sync_engine.dispose()
        print("Sync database connections cleaned up successfully")
    except Exception as e:
        print(f"Error during sync database cleanup: {e}")
