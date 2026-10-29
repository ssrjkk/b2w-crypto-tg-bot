"""Unit tests for SubscriptionService.

Заглушка повторяет реальный интерфейс сервиса: он ходит в AsyncSession
(`db.execute(...).scalar_one_or_none()`, `db.add`, `db.commit`, `db.refresh`),
поэтому мокается именно он, а не `fetchone` из raw-SQL версии."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError, SubscriptionError
from app.models.base import SubscriptionModel, SubscriptionStatus
from app.services.subscription_service import SubscriptionService


def _row(**kwargs) -> SubscriptionModel:
    row = SubscriptionModel(
        user_id=1,
        plan_name="premium",
        status=SubscriptionStatus.INACTIVE,
        start_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=30),
    )
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


def _session(*results):
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    responses = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=next_result)) for next_result in results
    ]
    db.execute = AsyncMock(side_effect=responses)
    return db


class TestSubscriptionService:
    @pytest.mark.asyncio
    async def test_create_subscription_success(self):
        db = _session(None)
        service = SubscriptionService(db)

        sub = await service.create_subscription(user_id=1, plan_name="premium", duration_days=30)

        assert sub.user_id == 1
        assert sub.plan_name == "premium"
        assert sub.status == SubscriptionStatus.PENDING
        db.add.assert_called_once_with(sub)
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(sub)

    @pytest.mark.asyncio
    async def test_create_subscription_already_active(self):
        db = _session(_row(status=SubscriptionStatus.ACTIVE))
        service = SubscriptionService(db)

        with pytest.raises(SubscriptionError):
            await service.create_subscription(user_id=1)

        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_subscription_success(self):
        db = _session(_row(status=SubscriptionStatus.PENDING))
        service = SubscriptionService(db)

        sub = await service.activate_subscription(1)

        assert sub.status == SubscriptionStatus.ACTIVE
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_activate_missing_subscription(self):
        service = SubscriptionService(_session(None))

        with pytest.raises(NotFoundError):
            await service.activate_subscription(99)

    @pytest.mark.asyncio
    async def test_check_access_active_subscription(self):
        row = _row(
            status=SubscriptionStatus.ACTIVE, expiry_date=datetime.utcnow() + timedelta(days=5)
        )
        service = SubscriptionService(_session(row))

        assert await service.check_access(1) is True

    @pytest.mark.asyncio
    async def test_check_access_expired_subscription(self):
        row = _row(
            status=SubscriptionStatus.ACTIVE,
            expiry_date=datetime.utcnow() - timedelta(days=1),
        )
        db = _session(row)
        service = SubscriptionService(db)

        assert await service.check_access(1) is False
        assert row.status == SubscriptionStatus.EXPIRED
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_access_no_subscription(self):
        service = SubscriptionService(_session(None))

        assert await service.check_access(1) is False
