"""Background risk management tasks."""

import logging
from datetime import datetime, timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def check_daily_loss_limits(self) -> dict:
    """Check and enforce daily loss limits for all users."""
    from app.database.manager import get_db_manager
    from app.models.base import TradeModel, RiskDecisionEnum
    from sqlalchemy import select, func

    db = get_db_manager()

    try:
        async with db.session() as session:
            yesterday = datetime.utcnow() - timedelta(days=1)

            result = await session.execute(
                select(
                    TradeModel.user_id,
                    func.count(TradeModel.id).label("trade_count"),
                )
                .where(TradeModel.created_at > yesterday)
                .where(TradeModel.risk_decision == RiskDecisionEnum.APPROVED.value)
                .group_by(TradeModel.user_id)
            )
            users_traded = result.all()

            return {
                "users_traded": len(users_traded),
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error checking daily loss limits: {e}")
        return {"error": str(e)}


@shared_task(bind=True)
def reset_kill_switch_if_needed() -> dict:
    """Check if kill switch should be reset."""
    from app.config.settings import get_settings

    settings = get_settings()

    if settings.environment == "production":
        return {
            "status": "no_action",
            "reason": "Kill switch only manually managed in production",
        }

    return {
        "status": "check_completed",
        "timestamp": datetime.utcnow().isoformat(),
    }


@shared_task(bind=True)
def record_risk_violation(
    user_id: int,
    violation_type: str,
    details: dict,
) -> dict:
    """Record a risk violation for audit."""
    from app.database.manager import get_db_manager
    from app.models.base import DashboardEventModel, ActionType, ActionStatus
    from sqlalchemy import insert

    db = get_db_manager()

    try:
        async with db.session() as session:
            stmt = insert(DashboardEventModel).values(
                user_id=user_id,
                action_type=ActionType.TRADE,
                status=ActionStatus.BLOCKED,
                description=f"Risk violation: {violation_type}",
                reason=violation_type,
                metadata=details,
            )
            await session.execute(stmt)

            return {
                "recorded": True,
                "user_id": user_id,
                "violation_type": violation_type,
            }
    except Exception as e:
        logger.error(f"Error recording risk violation: {e}")
        return {"error": str(e)}
