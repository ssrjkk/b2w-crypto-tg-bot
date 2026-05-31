"""Payment models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import Network, PaymentStatus


class Payment(BaseModel):
    id: int
    user_id: int
    amount: str
    token: str
    network: Network
    status: PaymentStatus = PaymentStatus.PENDING
    invoice_address: str = ""
    transaction_hash: Optional[str] = None
    confirmations: int = 0
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class Invoice(BaseModel):
    id: int
    user_id: int
    amount: str
    token: str
    network: Network
    address: str
    qr_code: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_payment(cls, payment: Payment) -> "Invoice":
        return cls(
            id=payment.id,
            user_id=payment.user_id,
            amount=payment.amount,
            token=payment.token,
            network=payment.network,
            address=payment.invoice_address,
            status=payment.status,
            expires_at=payment.expires_at,
        )


class PaymentVerifyRequest(BaseModel):
    transaction_hash: str
    user_id: int
    expected_amount: str
    token: str
    network: Network
