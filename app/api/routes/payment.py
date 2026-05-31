"""Payment API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.manager import get_db_session
from app.payments.invoice import PaymentService
from app.core.enums import Network

router = APIRouter(prefix="/payment", tags=["payment"])


class InvoiceCreateRequest(BaseModel):
    user_id: int
    amount: str
    token: str
    network: Network


class PaymentVerifyRequest(BaseModel):
    transaction_hash: str
    user_id: int
    expected_amount: str
    token: str
    network: Network


@router.post("/invoice")
async def create_invoice(
    request: InvoiceCreateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a payment invoice."""
    service = PaymentService(db)
    try:
        payment = await service.create_invoice(
            user_id=request.user_id,
            amount=request.amount,
            token=request.token,
            network=request.network,
        )
        return {
            "id": payment.id,
            "amount": payment.amount,
            "token": payment.token,
            "network": payment.network.value,
            "address": payment.invoice_address,
            "expires_at": payment.expires_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
async def verify_payment(
    request: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Verify a payment transaction."""
    service = PaymentService(db)
    try:
        payment = await service.verify_payment(
            transaction_hash=request.transaction_hash,
            user_id=request.user_id,
            expected_amount=request.expected_amount,
            token=request.token,
            network=request.network,
        )
        return {"status": payment.status.value, "payment_id": payment.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm/{payment_id}")
async def confirm_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Confirm payment after required confirmations."""
    service = PaymentService(db)
    try:
        payment = await service.confirm_payment(payment_id)
        return {"status": payment.status.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{user_id}")
async def get_payment_status(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Check pending payment for user."""
    service = PaymentService(db)
    payment = await service.check_payment_status(user_id)
    if not payment:
        return {"status": "none"}
    return {
        "id": payment.id,
        "amount": payment.amount,
        "token": payment.token,
        "status": payment.status.value,
    }
