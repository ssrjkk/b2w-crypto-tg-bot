"""Integration tests for database operations."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.base import Base, UserModel, SubscriptionModel, SubscriptionStatus
from app.database.manager import DatabaseManager


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


class TestDatabaseModels:
    """Integration tests for database models."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test creating a user."""
        user = UserModel(
            telegram_id="123456",
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        db_session.add(user)
        await db_session.commit()

        assert user.id is not None
        assert user.telegram_id == "123456"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_subscription(self, db_session):
        """Test creating a subscription."""
        user = UserModel(telegram_id="123456", username="test")
        db_session.add(user)
        await db_session.flush()

        subscription = SubscriptionModel(
            user_id=user.id,
            plan_name="premium",
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(subscription)
        await db_session.commit()

        assert subscription.id is not None
        assert subscription.user_id == user.id
        assert subscription.status == SubscriptionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_user_subscription_relationship(self, db_session):
        """Test user-subscription relationship."""
        user = UserModel(telegram_id="123456", username="test")
        db_session.add(user)
        await db_session.flush()

        subscription = SubscriptionModel(
            user_id=user.id,
            plan_name="premium",
            status=SubscriptionStatus.PENDING,
        )
        db_session.add(subscription)
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(UserModel).where(UserModel.telegram_id == "123456")
        )
        found_user = result.scalar_one()

        assert found_user.telegram_id == "123456"
