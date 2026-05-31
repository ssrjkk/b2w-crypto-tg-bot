"""Background payment tasks."""

import logging
from datetime import datetime

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_expired_payments(self) -> dict:
    """Check and expire pending payments."""
    from app.database.manager import get_db_manager
    from app.models.base import PaymentModel, PaymentStatus
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession

    db = get_db_manager()

    try:
        async with db.session() as session:
            now = datetime.utcnow()
            stmt = (
                update(PaymentModel)
                .where(PaymentModel.status == PaymentStatus.PENDING)
                .where(PaymentModel.expires_at < now)
                .values(status=PaymentStatus.EXPIRED)
            )
            result = await session.execute(stmt)

            return {
                "expired": result.rowcount,
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error checking expired payments: {e}")
        self.retry(countdown=60)


@shared_task(bind=True, max_retries=3)
def confirm_payment(self, payment_id: int) -> dict:
    """Confirm payment after required confirmations."""
    from app.database.manager import get_db_manager
    from app.models.base import PaymentModel, PaymentStatus
    from sqlalchemy import select

    db = get_db_manager()

    try:
        async with db.session() as session:
            result = await session.execute(
                select(PaymentModel).where(PaymentModel.id == payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                return {"error": "Payment not found"}

            if payment.confirmations >= 12:
                payment.status = PaymentStatus.CONFIRMED
                await session.commit()
                return {"status": "confirmed", "payment_id": payment_id}

            return {"status": "pending_confirmations", "payment_id": payment_id}
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        self.retry(countdown=30)


@shared_task
def activate_subscription_on_payment(user_id: int, payment_id: int) -> dict:
    """Activate subscription after payment confirmation."""
    from app.database.manager import get_db_manager
    from app.models.base import SubscriptionModel, SubscriptionStatus
    from sqlalchemy import select, update

    db = get_db_manager()

    try:
        async with db.session() as session:
            stmt = (
                update(SubscriptionModel)
                .where(SubscriptionModel.user_id == user_id)
                .where(SubscriptionModel.status == SubscriptionStatus.PENDING)
                .values(status=SubscriptionStatus.ACTIVE)
            )
            result = await session.execute(stmt)

            return {
                "activated": result.rowcount > 0,
                "user_id": user_id,
                "payment_id": payment_id,
            }
    except Exception as e:
        logger.error(f"Error activating subscription: {e}")
        return {"error": str(e)}
