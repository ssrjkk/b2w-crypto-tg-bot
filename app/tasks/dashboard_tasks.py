"""Background dashboard tasks."""

import logging
from datetime import datetime, timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def cleanup_old_events(days_to_keep: int = 90) -> dict:
    """Clean up old dashboard events."""
    from app.database.manager import get_db_manager
    from app.models.base import DashboardEventModel
    from sqlalchemy import delete

    db = get_db_manager()

    try:
        async with db.session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
            stmt = delete(DashboardEventModel).where(
                DashboardEventModel.created_at < cutoff
            )
            result = await session.execute(stmt)

            return {
                "deleted": result.rowcount,
                "cutoff_date": cutoff.isoformat(),
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error cleaning up events: {e}")
        return {"error": str(e)}


@shared_task(bind=True)
def generate_daily_report() -> dict:
    """Generate daily activity report."""
    from app.database.manager import get_db_manager
    from app.models.base import DashboardEventModel, TradeModel
    from sqlalchemy import select, func

    db = get_db_manager()

    try:
        async with db.session() as session:
            yesterday = datetime.utcnow() - timedelta(days=1)

            events_result = await session.execute(
                select(func.count(DashboardEventModel.id))
                .where(DashboardEventModel.created_at > yesterday)
            )
            total_events = events_result.scalar()

            trades_result = await session.execute(
                select(func.count(TradeModel.id))
                .where(TradeModel.created_at > yesterday)
            )
            total_trades = trades_result.scalar()

            return {
                "date": yesterday.date().isoformat(),
                "total_events": total_events,
                "total_trades": total_trades,
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {"error": str(e)}
