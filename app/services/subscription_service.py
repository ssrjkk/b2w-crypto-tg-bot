"""Subscription service - SQLAlchemy version."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import SubscriptionModel, SubscriptionStatus
from app.core.exceptions import NotFoundError, SubscriptionError

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Manages user subscription lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(
        self,
        user_id: int,
        plan_name: str = "premium",
        duration_days: int = 30,
    ) -> SubscriptionModel:
        """Create a new subscription for user."""
        existing = await self._get_active_subscription(user_id)
        if existing:
            raise SubscriptionError("User already has active subscription")

        now = datetime.utcnow()
        expiry = now + timedelta(days=duration_days)

        sub = SubscriptionModel(
            user_id=user_id,
            plan_name=plan_name,
            status=SubscriptionStatus.PENDING,
            start_date=now,
            expiry_date=expiry,
        )
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)

        logger.info(f"Created subscription {sub.id} for user {user_id}")
        return sub

    async def activate_subscription(self, subscription_id: int) -> SubscriptionModel:
        """Activate a pending subscription after payment confirmation."""
        sub = await self._get_subscription(subscription_id)
        if not sub:
            raise NotFoundError("Subscription")

        if sub.status != SubscriptionStatus.PENDING:
            raise SubscriptionError(f"Cannot activate subscription with status {sub.status}")

        sub.status = SubscriptionStatus.ACTIVE
        await self.db.commit()
        await self.db.refresh(sub)

        logger.info(f"Activated subscription {subscription_id}")
        return sub

    async def expire_subscription(self, subscription_id: int) -> SubscriptionModel:
        """Mark subscription as expired."""
        sub = await self._get_subscription(subscription_id)
        if not sub:
            raise NotFoundError("Subscription")

        sub.status = SubscriptionStatus.EXPIRED
        await self.db.commit()
        await self.db.refresh(sub)

        logger.info(f"Expired subscription {subscription_id}")
        return sub

    async def get_subscription(self, subscription_id: int) -> SubscriptionModel:
        """Get subscription by ID."""
        sub = await self._get_subscription(subscription_id)
        if not sub:
            raise NotFoundError("Subscription")
        return sub

    async def get_user_subscription(self, user_id: int) -> Optional[SubscriptionModel]:
        """Get active subscription for user."""
        return await self._get_active_subscription(user_id)

    async def check_access(self, user_id: int) -> bool:
        """Check if user has active subscription."""
        sub = await self._get_active_subscription(user_id)
        if not sub:
            return False
        if sub.status != SubscriptionStatus.ACTIVE:
            return False
        if sub.expiry_date and sub.expiry_date < datetime.utcnow():
            sub.status = SubscriptionStatus.EXPIRED
            await self.db.commit()
            return False
        return True

    async def _get_subscription(self, subscription_id: int) -> Optional[SubscriptionModel]:
        """Internal method to get subscription by ID."""
        result = await self.db.execute(
            select(SubscriptionModel).where(SubscriptionModel.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def _get_active_subscription(self, user_id: int) -> Optional[SubscriptionModel]:
        """Internal method to get active subscription for user."""
        result = await self.db.execute(
            select(SubscriptionModel)
            .where(SubscriptionModel.user_id == user_id)
            .where(SubscriptionModel.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalar_one_or_none()
