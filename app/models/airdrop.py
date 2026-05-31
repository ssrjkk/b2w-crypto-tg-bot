"""Airdrop models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import AirdropStatus


class AirdropCampaign(BaseModel):
    id: int
    name: str
    protocol: str
    description: str
    eligibility_rules: dict
    status: AirdropStatus = AirdropStatus.NOT_ELIGIBLE
    estimated_amount: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AirdropProgress(BaseModel):
    id: int
    user_id: int
    campaign_id: int
    status: AirdropStatus = AirdropStatus.NOT_ELIGIBLE
    progress_percent: float = 0.0
    tasks_completed: int = 0
    tasks_total: int = 0
    last_checked_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AirdropTask(BaseModel):
    id: int
    campaign_id: int
    name: str
    description: str
    action_type: str
    required: bool = True
    completed: bool = False
    completed_at: Optional[datetime] = None


class EligibilityRule(BaseModel):
    rule_id: str
    description: str
    check_function: str
    parameters: dict = Field(default_factory=dict)
