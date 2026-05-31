"""Subscription models."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import SubscriptionStatus


class Subscription(BaseModel):
    id: int
    user_id: int
    plan_name: str = "premium"
    status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    start_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    user_id: int
    plan_name: str = "premium"
    duration_days: int = 30


class SubscriptionResponse(BaseModel):
    id: int
    status: SubscriptionStatus
    start_date: Optional[datetime]
    expiry_date: Optional[datetime]
    days_remaining: Optional[int]

    @classmethod
    def from_subscription(cls, sub: Subscription) -> "SubscriptionResponse":
        days_remaining = None
        if sub.expiry_date:
            delta = sub.expiry_date - datetime.utcnow()
            days_remaining = max(0, delta.days)
        return cls(
            id=sub.id,
            status=sub.status,
            start_date=sub.start_date,
            expiry_date=sub.expiry_date,
            days_remaining=days_remaining,
        )
