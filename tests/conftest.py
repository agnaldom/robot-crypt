"""
Test configuration and fixtures for Robot-Crypt API tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database.database import Base, get_database
from src.core.config import settings
from src.core.security import create_access_token, get_password_hash
from src.models.user import User
from src.schemas.user import UserCreate
from src.services.user_service import UserService


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        import src.models  # This will import all models from __init__.py
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create test session factory."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_db(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override only (no auth override)."""
    from httpx import ASGITransport
    
    async def override_get_database():
        yield test_db
    
    app.dependency_overrides[get_database] = override_get_database
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(test_db, mock_current_user) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with both database and auth dependency overrides."""
    from httpx import ASGITransport
    from src.core.security import get_current_user
    
    async def override_get_database():
        yield test_db
    
    async def override_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> TestClient:
    """Create synchronous test client for simple tests."""
    return TestClient(app)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "telegram_id": "123456789"
    }


@pytest.fixture
def sample_asset_data():
    """Sample asset data for testing."""
    return {
        "symbol": "BTCUSDT",
        "name": "Bitcoin",
        "price": 45000.00,
        "volume_24h": 1234567.89,
        "market_cap": 850000000000.0,
        "price_change_24h": 2.5,
        "last_updated": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_indicator_data():
    """Sample technical indicator data for testing."""
    return {
        "asset_id": 1,
        "indicator_type": "RSI",
        "timeframe": "1h",
        "value": 65.5,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "asset_id": 1,
        "trade_type": "BUY",
        "quantity": 0.1,
        "price": 45000.00,
        "status": "PENDING",
        "strategy": "RSI_STRATEGY"
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data for testing."""
    return {
        "asset_id": 1,
        "alert_type": "PRICE_ALERT",
        "condition": "ABOVE",
        "threshold": 50000.00,
        "message": "Bitcoin price alert",
        "is_active": True
    }


@pytest.fixture
def mock_current_user():
    """Mock current user for testing."""
    from src.schemas.user import User
    from datetime import datetime
    return User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        preferences={}
    )


@pytest.fixture
def auth_headers():
    """Create a proper authentication header for testing."""
    # Create a test token with test user data
    test_token = create_access_token(data={"sub": "test@example.com"})
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def mock_user_id():
    """Mock user ID for testing."""
    return 1


# Test data cleanup fixtures
@pytest_asyncio.fixture
async def cleanup_db(test_db):
    """Clean up database after each test."""
    yield
    
    # Clean up all tables in reverse order to handle foreign key constraints
    for table in reversed(Base.metadata.sorted_tables):
        await test_db.execute(table.delete())
    await test_db.commit()
