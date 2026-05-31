"""Payment service - SQLAlchemy version."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.enums import Network
from app.models.base import PaymentModel, PaymentStatus
from app.core.exceptions import (
    InsufficientPaymentError,
    NotFoundError,
    PaymentExpiredError,
    PaymentError,
)

logger = logging.getLogger(__name__)


class PaymentService:
    """Handles crypto payment invoicing and verification."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_invoice(
        self,
        user_id: int,
        amount: str,
        token: str,
        network: Network,
    ) -> PaymentModel:
        """Create a payment invoice."""
        settings = get_settings()
        expiry = datetime.utcnow() + timedelta(
            minutes=settings.payment.invoice_expiry_minutes
        )

        address = self._generate_crypto_address(network)

        payment = PaymentModel(
            user_id=user_id,
            amount=amount,
            token=token,
            network=network,
            status=PaymentStatus.PENDING,
            invoice_address=address,
            expires_at=expiry,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Created invoice {payment.id} for user {user_id}: {amount} {token} on {network.value}")
        return payment

    async def verify_payment(
        self,
        transaction_hash: str,
        user_id: int,
        expected_amount: str,
        token: str,
        network: Network,
    ) -> PaymentModel:
        """Verify a payment transaction."""
        payment = await self._get_payment_by_user(user_id)
        if not payment:
            raise NotFoundError("Payment")

        if payment.status != PaymentStatus.PENDING:
            return payment

        if datetime.utcnow() > payment.expires_at:
            payment.status = PaymentStatus.EXPIRED
            await self.db.commit()
            raise PaymentExpiredError()

        if transaction_hash != payment.transaction_hash:
            raise PaymentError("Transaction hash mismatch")

        if expected_amount != payment.amount:
            raise InsufficientPaymentError()

        payment.status = PaymentStatus.PAID
        payment.transaction_hash = transaction_hash
        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Payment {payment.id} marked as paid")
        return payment

    async def confirm_payment(self, payment_id: int) -> PaymentModel:
        """Confirm payment after required confirmations."""
        payment = await self._get_payment(payment_id)
        if not payment:
            raise NotFoundError("Payment")

        if payment.status != PaymentStatus.PAID:
            raise PaymentError(f"Cannot confirm payment with status {payment.status}")

        payment.status = PaymentStatus.CONFIRMED
        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Payment {payment.id} confirmed")
        return payment

    async def get_invoice(self, invoice_id: int) -> Optional[PaymentModel]:
        """Get invoice by ID."""
        return await self._get_payment(invoice_id)

    async def check_payment_status(self, user_id: int) -> Optional[PaymentModel]:
        """Check pending payment for user."""
        return await self._get_payment_by_user(user_id)

    async def _get_payment(self, payment_id: int) -> Optional[PaymentModel]:
        """Internal method to get payment by ID."""
        result = await self.db.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def _get_payment_by_user(self, user_id: int) -> Optional[PaymentModel]:
        """Internal method to get pending payment for user."""
        result = await self.db.execute(
            select(PaymentModel)
            .where(PaymentModel.user_id == user_id)
            .where(PaymentModel.status == PaymentStatus.PENDING)
        )
        return result.scalar_one_or_none()

    def _generate_crypto_address(self, network: Network) -> str:
        """Generate a unique payment address."""
        prefix = network.value[:3]
        random_part = secrets.token_hex(20)
        return f"0x{prefix}{random_part}"
