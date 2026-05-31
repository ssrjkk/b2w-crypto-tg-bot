"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))
    db.fetchone = AsyncMock(return_value=None)
    db.fetchall = AsyncMock(return_value=[])
    return db


@pytest.fixture
def sample_user():
    """Create a sample user."""
    return {
        "id": 1,
        "telegram_id": 123456,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
def sample_subscription():
    """Create a sample subscription."""
    return {
        "id": 1,
        "user_id": 1,
        "plan_name": "premium",
        "status": "active",
        "start_date": "2024-01-01T00:00:00",
        "expiry_date": "2024-01-31T00:00:00",
    }


@pytest.fixture
def sample_payment():
    """Create a sample payment."""
    return {
        "id": 1,
        "user_id": 1,
        "amount": "0.01",
        "token": "ETH",
        "network": "arbitrum",
        "status": "pending",
        "invoice_address": "0xabc123",
        "transaction_hash": None,
        "expires_at": "2024-01-01T00:30:00",
    }


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
