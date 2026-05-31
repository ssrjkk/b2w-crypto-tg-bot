"""Subscription API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.manager import get_db_session
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscription", tags=["subscription"])


class SubscriptionCreateRequest(BaseModel):
    user_id: int
    plan_name: str = "premium"
    duration_days: int = 30


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_name: str
    status: str
    start_date: str | None
    expiry_date: str | None
    days_remaining: int | None

    class Config:
        from_attributes = True


class SubscriptionActivateRequest(BaseModel):
    subscription_id: int


@router.post("/create", response_model=dict)
async def create_subscription(
    request: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new subscription."""
    service = SubscriptionService(db)
    try:
        sub = await service.create_subscription(
            user_id=request.user_id,
            plan_name=request.plan_name,
            duration_days=request.duration_days,
        )
        return {
            "id": sub.id,
            "status": sub.status.value,
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "expiry_date": sub.expiry_date.isoformat() if sub.expiry_date else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{user_id}", response_model=dict)
async def get_subscription_status(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get user subscription status."""
    service = SubscriptionService(db)
    sub = await service.get_user_subscription(user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    days_remaining = None
    if sub.expiry_date:
        from datetime import datetime
        delta = sub.expiry_date - datetime.utcnow()
        days_remaining = max(0, delta.days)
    
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "plan_name": sub.plan_name,
        "status": sub.status.value,
        "start_date": sub.start_date.isoformat() if sub.start_date else None,
        "expiry_date": sub.expiry_date.isoformat() if sub.expiry_date else None,
        "days_remaining": days_remaining,
    }


@router.post("/activate")
async def activate_subscription(
    request: SubscriptionActivateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Activate subscription after payment."""
    service = SubscriptionService(db)
    try:
        sub = await service.activate_subscription(request.subscription_id)
        return {"status": "activated", "subscription_id": sub.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check-access/{user_id}")
async def check_access(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Check if user has access."""
    service = SubscriptionService(db)
    has_access = await service.check_access(user_id)
    return {"has_access": has_access}
