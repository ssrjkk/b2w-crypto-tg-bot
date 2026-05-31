"""Dashboard API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.manager import get_db_session
from app.core.enums import ActionStatus, ActionType, RiskDecision

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class EventLogRequest(BaseModel):
    user_id: int
    action_type: str
    status: str
    risk_decision: Optional[str] = None
    description: str
    reason: str
    result: Optional[dict] = None
    metadata: dict = {}


@router.post("/event")
async def log_event(
    request: EventLogRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Log a dashboard event."""
    from app.dashboard.service import DashboardService
    from app.models.dashboard import EventCreate

    service = DashboardService(db)

    try:
        event = await service.log_event(
            EventCreate(
                user_id=request.user_id,
                action_type=ActionType(request.action_type),
                status=ActionStatus(request.status),
                risk_decision=RiskDecision(request.risk_decision) if request.risk_decision else None,
                description=request.description,
                reason=request.reason,
                result=request.result,
                event_metadata=request.metadata,
            )
        )
        return {"event_id": event.id, "status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/{user_id}")
async def get_events(
    user_id: int,
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """Get dashboard events for user."""
    from app.dashboard.service import DashboardService

    service = DashboardService(db)

    try:
        events = await service.get_events(
            user_id=user_id,
            action_type=ActionType(action_type) if action_type else None,
            status=ActionStatus(status) if status else None,
            limit=limit,
        )
        return {
            "events": [
                {
                    "id": e.id,
                    "action_type": e.action_type.value,
                    "status": e.status.value,
                    "description": e.description,
                    "reason": e.reason,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary/{user_id}")
async def get_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get dashboard summary for user."""
    from app.dashboard.service import DashboardService

    service = DashboardService(db)

    try:
        summary = await service.get_summary(user_id)
        return {
            "total_actions": summary.total_actions,
            "completed_actions": summary.completed_actions,
            "failed_actions": summary.failed_actions,
            "blocked_actions": summary.blocked_actions,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
