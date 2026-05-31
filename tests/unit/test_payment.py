"""Unit tests for payment service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.payments.invoice import PaymentService
from app.models.payment import Payment
from app.core.enums import Network, PaymentStatus


class TestPaymentService:
    """Tests for PaymentService."""

    @pytest.fixture
    def payment_service(self, mock_db):
        return PaymentService(mock_db)

    @pytest.mark.asyncio
    async def test_create_invoice(self, payment_service, mock_db):
        """Test creating a payment invoice."""
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))

        invoice = await payment_service.create_invoice(
            user_id=1,
            amount="0.01",
            token="ETH",
            network=Network.ARBITRUM,
        )

        assert invoice.user_id == 1
        assert invoice.amount == "0.01"
        assert invoice.token == "ETH"
        assert invoice.network == Network.ARBITRUM
        assert invoice.status == PaymentStatus.PENDING

    @pytest.mark.asyncio
    async def test_verify_payment_success(self, payment_service, mock_db):
        """Test verifying a payment."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "amount": "0.01",
                "token": "ETH",
                "network": "arbitrum",
                "status": "pending",
                "invoice_address": "0xabc",
                "transaction_hash": "0x123",
                "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            }
        )
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))

        from app.models.payment import PaymentVerifyRequest
        request = PaymentVerifyRequest(
            transaction_hash="0x123",
            user_id=1,
            expected_amount="0.01",
            token="ETH",
            network=Network.ARBITRUM,
        )

        payment = await payment_service.verify_payment(request)

        assert payment.status == PaymentStatus.PAID

    @pytest.mark.asyncio
    async def test_verify_payment_expired(self, payment_service, mock_db):
        """Test verifying an expired payment."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "amount": "0.01",
                "token": "ETH",
                "network": "arbitrum",
                "status": "pending",
                "invoice_address": "0xabc",
                "transaction_hash": "0x123",
                "expires_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
            }
        )
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))

        from app.models.payment import PaymentVerifyRequest
        request = PaymentVerifyRequest(
            transaction_hash="0x123",
            user_id=1,
            expected_amount="0.01",
            token="ETH",
            network=Network.ARBITRUM,
        )

        with pytest.raises(Exception):
            await payment_service.verify_payment(request)

    @pytest.mark.asyncio
    async def test_confirm_payment_success(self, payment_service, mock_db):
        """Test confirming a paid payment."""
        mock_db.fetchone = AsyncMock(
            return_value={
                "id": 1,
                "user_id": 1,
                "amount": "0.01",
                "token": "ETH",
                "network": "arbitrum",
                "status": "paid",
                "invoice_address": "0xabc",
                "transaction_hash": "0x123",
                "expires_at": "2024-01-01T00:30:00",
            }
        )
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))

        payment = await payment_service.confirm_payment(1)

        assert payment.status == PaymentStatus.CONFIRMED
