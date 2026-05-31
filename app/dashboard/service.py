"""Dashboard event logging service - SQLAlchemy version."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ActionStatus, ActionType, RiskDecision
from app.models.base import DashboardEventModel
from app.models.dashboard import DashboardEvent, DashboardSummary, EventCreate

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for logging and retrieving dashboard events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, event: EventCreate) -> DashboardEvent:
        """Log a new dashboard event."""
        db_event = DashboardEventModel(
            user_id=event.user_id,
            action_type=event.action_type,
            status=event.status,
            risk_decision=event.risk_decision,
            description=event.description,
            reason=event.reason,
            result=event.result,
            event_metadata=event.metadata,
        )
        self.db.add(db_event)
        await self.db.commit()
        await self.db.refresh(db_event)

        return DashboardEvent(
            id=db_event.id,
            user_id=db_event.user_id,
            action_type=db_event.action_type,
            status=db_event.status,
            risk_decision=db_event.risk_decision,
            description=db_event.description,
            reason=db_event.reason,
            result=db_event.result,
            event_metadata=db_event.event_metadata or {},
            created_at=db_event.created_at,
        )

    async def get_events(
        self,
        user_id: Optional[int] = None,
        action_type: Optional[ActionType] = None,
        status: Optional[ActionStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[DashboardEvent]:
        """Get filtered dashboard events."""
        query = select(DashboardEventModel)

        if user_id:
            query = query.where(DashboardEventModel.user_id == user_id)
        if action_type:
            query = query.where(DashboardEventModel.action_type == action_type)
        if status:
            query = query.where(DashboardEventModel.status == status)
        if from_date:
            query = query.where(DashboardEventModel.created_at >= from_date)
        if to_date:
            query = query.where(DashboardEventModel.created_at <= to_date)

        query = query.order_by(DashboardEventModel.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        events = result.scalars().all()

        return [
            DashboardEvent(
                id=e.id,
                user_id=e.user_id,
                action_type=e.action_type,
                status=e.status,
                risk_decision=e.risk_decision,
                description=e.description,
                reason=e.reason,
                result=e.result,
                event_metadata=e.event_metadata or {},
                created_at=e.created_at,
            )
            for e in events
        ]

    async def get_summary(self, user_id: int) -> DashboardSummary:
        """Get dashboard summary for user."""
        total_result = await self.db.execute(
            select(func.count(DashboardEventModel.id))
            .where(DashboardEventModel.user_id == user_id)
        )
        total_actions = total_result.scalar() or 0

        completed_result = await self.db.execute(
            select(func.count(DashboardEventModel.id))
            .where(DashboardEventModel.user_id == user_id)
            .where(DashboardEventModel.status == ActionStatus.COMPLETED)
        )
        completed_actions = completed_result.scalar() or 0

        failed_result = await self.db.execute(
            select(func.count(DashboardEventModel.id))
            .where(DashboardEventModel.user_id == user_id)
            .where(DashboardEventModel.status == ActionStatus.FAILED)
        )
        failed_actions = failed_result.scalar() or 0

        blocked_result = await self.db.execute(
            select(func.count(DashboardEventModel.id))
            .where(DashboardEventModel.user_id == user_id)
            .where(DashboardEventModel.status == ActionStatus.BLOCKED)
        )
        blocked_actions = blocked_result.scalar() or 0

        recent_events = await self.get_events(user_id=user_id, limit=10)

        return DashboardSummary(
            total_actions=total_actions,
            completed_actions=completed_actions,
            failed_actions=failed_actions,
            blocked_actions=blocked_actions,
            recent_events=recent_events,
        )

    async def get_event_by_id(self, event_id: int) -> Optional[DashboardEvent]:
        """Get specific event by ID."""
        result = await self.db.execute(
            select(DashboardEventModel).where(DashboardEventModel.id == event_id)
        )
        e = result.scalar_one_or_none()

        if not e:
            return None

        return DashboardEvent(
            id=e.id,
            user_id=e.user_id,
            action_type=e.action_type,
            status=e.status,
            risk_decision=e.risk_decision,
            description=e.description,
            reason=e.reason,
            result=e.result,
            event_metadata=e.event_metadata or {},
            created_at=e.created_at,
        )
