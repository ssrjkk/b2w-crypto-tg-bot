"""Unit tests for payment service.

Мок повторяет реальный интерфейс: сервис работает через AsyncSession
(`db.execute(...).scalar_one_or_none()`, `db.add`, `db.commit`, `db.refresh`),
а `verify_payment` принимает раздельные аргументы, не request-модель."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.enums import Network, PaymentStatus
from app.models.base import PaymentModel
from app.payments.invoice import PaymentService


def _payment(**kwargs) -> PaymentModel:
    row = PaymentModel(
        user_id=1,
        amount="0.01",
        token="ETH",
        network=Network.ARBITRUM,
        status=PaymentStatus.PENDING,
        invoice_address="0xabc",
        transaction_hash="0x123",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


def _session(*rows):
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[MagicMock(scalar_one_or_none=MagicMock(return_value=row)) for row in rows]
    )
    return db


class TestPaymentService:
    """Tests for PaymentService."""

    @pytest.mark.asyncio
    async def test_create_invoice(self):
        db = _session()
        service = PaymentService(db)

        invoice = await service.create_invoice(
            user_id=1, amount="0.01", token="ETH", network=Network.ARBITRUM
        )

        assert invoice.user_id == 1
        assert invoice.amount == "0.01"
        assert invoice.token == "ETH"
        assert invoice.network == Network.ARBITRUM
        assert invoice.status == PaymentStatus.PENDING
        db.add.assert_called_once_with(invoice)
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(invoice)

    @pytest.mark.asyncio
    async def test_verify_payment_success(self):
        stored = _payment(id=1)
        service = PaymentService(_session(stored))

        payment = await service.verify_payment(
            transaction_hash="0x123",
            user_id=1,
            expected_amount="0.01",
            token="ETH",
            network=Network.ARBITRUM,
        )

        assert payment.status == PaymentStatus.PAID

    @pytest.mark.asyncio
    async def test_verify_payment_expired(self):
        stored = _payment(id=1, expires_at=datetime.utcnow() - timedelta(minutes=1))
        service = PaymentService(_session(stored))

        with pytest.raises(Exception):
            await service.verify_payment(
                transaction_hash="0x123",
                user_id=1,
                expected_amount="0.01",
                token="ETH",
                network=Network.ARBITRUM,
            )

        assert stored.status == PaymentStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_verify_payment_wrong_hash(self):
        stored = _payment(id=1, transaction_hash="0xother")
        service = PaymentService(_session(stored))

        with pytest.raises(Exception):
            await service.verify_payment(
                transaction_hash="0x123",
                user_id=1,
                expected_amount="0.01",
                token="ETH",
                network=Network.ARBITRUM,
            )

        assert stored.status == PaymentStatus.PENDING

    @pytest.mark.asyncio
    async def test_confirm_payment_success(self):
        stored = _payment(id=1, status=PaymentStatus.PAID)
        service = PaymentService(_session(stored))

        payment = await service.confirm_payment(1)

        assert payment.status == PaymentStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_confirm_payment_rejects_unpaid(self):
        service = PaymentService(_session(_payment(id=1, status=PaymentStatus.PENDING)))

        with pytest.raises(Exception):
            await service.confirm_payment(1)
