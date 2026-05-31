"""Unit tests for subscription service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.subscription_service import SubscriptionService
from app.models.subscription import Subscription
from app.core.enums import SubscriptionStatus


class TestSubscriptionService:
    """Tests for SubscriptionService."""

    @pytest.fixture
    def subscription_service(self, mock_db):
        return SubscriptionService(mock_db)

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, subscription_service, mock_db):
        """Test creating a new subscription."""
        mock_db.fetchone = AsyncMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))

        sub = await subscription_service.create_subscription(
            user_id=1,
            plan_name="premium",
            duration_days=30,
        )

        assert sub.user_id == 1
        assert sub.plan_name == "premium"
        assert sub.status == SubscriptionStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_subscription_already_active(self, subscription_service, mock_db):
        """Test creating subscription when user already has one."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "plan_name": "premium",
                "status": "active",
                "start_date": "2024-01-01",
                "expiry_date": "2024-01-31",
            }
        )

        with pytest.raises(Exception):
            await subscription_service.create_subscription(user_id=1)

    @pytest.mark.asyncio
    async def test_activate_subscription_success(self, subscription_service, mock_db):
        """Test activating a pending subscription."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "plan_name": "premium",
                "status": "pending",
                "start_date": "2024-01-01",
                "expiry_date": "2024-01-31",
            }
        )
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))

        sub = await subscription_service.activate_subscription(1)

        assert sub.status == SubscriptionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_check_access_active_subscription(self, subscription_service, mock_db):
        """Test checking access with active subscription."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "plan_name": "premium",
                "status": "active",
                "start_date": "2024-01-01",
                "expiry_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            }
        )

        has_access = await subscription_service.check_access(1)

        assert has_access is True

    @pytest.mark.asyncio
    async def test_check_access_expired_subscription(self, subscription_service, mock_db):
        """Test checking access with expired subscription."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "plan_name": "premium",
                "status": "active",
                "start_date": "2024-01-01",
                "expiry_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            }
        )

        has_access = await subscription_service.check_access(1)

        assert has_access is False

    @pytest.mark.asyncio
    async def test_check_access_no_subscription(self, subscription_service, mock_db):
        """Test checking access with no subscription."""
        mock_db.fetchone = AsyncMock(return_value=None)

        has_access = await subscription_service.check_access(1)

        assert has_access is False
