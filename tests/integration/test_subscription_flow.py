"""Integration tests for subscription flow."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.subscription_service import SubscriptionService
from app.models.base import SubscriptionModel, SubscriptionStatus


class TestSubscriptionFlow:
    """Integration tests for subscription flow."""

    @pytest.mark.asyncio
    async def test_create_subscription_with_db(self, db_session):
        """Test full subscription creation flow."""
        user_id = 1
        now = datetime.utcnow()
        expiry = now + timedelta(days=30)

        sub = SubscriptionModel(
            user_id=user_id,
            plan_name="premium",
            status=SubscriptionStatus.PENDING,
            start_date=now,
            expiry_date=expiry,
        )
        db_session.add(sub)
        await db_session.commit()

        result = await db_session.get(SubscriptionModel, sub.id)
        assert result is not None
        assert result.plan_name == "premium"
        assert result.status == SubscriptionStatus.PENDING

    @pytest.mark.asyncio
    async def test_activate_subscription_flow(self, db_session):
        """Test subscription activation flow."""
        user_id = 1
        sub = SubscriptionModel(
            user_id=user_id,
            plan_name="premium",
            status=SubscriptionStatus.PENDING,
            start_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(sub)
        await db_session.commit()

        sub.status = SubscriptionStatus.ACTIVE
        await db_session.commit()

        result = await db_session.get(SubscriptionModel, sub.id)
        assert result.status == SubscriptionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_expire_subscription_flow(self, db_session):
        """Test subscription expiration."""
        user_id = 1
        sub = SubscriptionModel(
            user_id=user_id,
            plan_name="premium",
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow() - timedelta(days=35),
            expiry_date=datetime.utcnow() - timedelta(days=5),
        )
        db_session.add(sub)
        await db_session.commit()

        assert sub.expiry_date < datetime.utcnow()
        sub.status = SubscriptionStatus.EXPIRED
        await db_session.commit()

        result = await db_session.get(SubscriptionModel, sub.id)
        assert result.status == SubscriptionStatus.EXPIRED
