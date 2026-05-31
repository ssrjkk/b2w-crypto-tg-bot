"""Dashboard models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.enums import ActionStatus, ActionType, RiskDecision


class DashboardEvent(BaseModel):
    id: int
    user_id: int
    action_type: ActionType
    status: ActionStatus
    risk_decision: Optional[RiskDecision] = None
    description: str
    reason: str
    result: Optional[dict] = None
    event_metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    user_id: int
    action_type: ActionType
    status: ActionStatus
    risk_decision: Optional[RiskDecision] = None
    description: str
    reason: str
    result: Optional[dict] = None
    event_metadata: dict = Field(default_factory=dict)


class DashboardSummary(BaseModel):
    total_actions: int
    completed_actions: int
    failed_actions: int
    blocked_actions: int
    recent_events: list[DashboardEvent]


class ActivityFilter(BaseModel):
    user_id: Optional[int] = None
    action_type: Optional[ActionType] = None
    status: Optional[ActionStatus] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 50
