"""Action queue service for managing queued actions."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from app.core.enums import ActionStatus, ActionType, RiskDecision
from app.core.exceptions import TradingError

logger = logging.getLogger(__name__)


@dataclass
class QueuedAction:
    id: int
    user_id: int
    action_type: ActionType
    status: ActionStatus
    payload: dict
    risk_decision: Optional[RiskDecision] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ActionQueueService:
    """Queue-based action execution service."""

    def __init__(self, db):
        self.db = db
        self._processing = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._handlers: dict[ActionType, Callable] = {}

    def register_handler(self, action_type: ActionType, handler: Callable) -> None:
        """Register a handler for an action type."""
        self._handlers[action_type] = handler
        logger.info(f"Registered handler for {action_type.value}")

    async def enqueue(
        self,
        user_id: int,
        action_type: ActionType,
        payload: dict,
    ) -> int:
        """Add action to queue."""
        result = await self.db.execute(
            """
            INSERT INTO action_queue (user_id, action_type, status, payload)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, action_type.value, ActionStatus.QUEUED.value, str(payload)),
        )
        action_id = result.lastrowid

        await self._queue.put(action_id)
        logger.info(f"Enqueued action {action_id} for user {user_id}: {action_type.value}")

        if not self._processing:
            asyncio.create_task(self._process_queue())

        return action_id

    async def get_status(self, action_id: int) -> Optional[QueuedAction]:
        """Get action status."""
        row = await self.db.fetchone(
            "SELECT * FROM action_queue WHERE id = ?", (action_id,)
        )
        if not row:
            return None

        return QueuedAction(
            id=row["id"],
            user_id=row["user_id"],
            action_type=ActionType(row["action_type"]),
            status=ActionStatus(row["status"]),
            payload=eval(row["payload"]),
            risk_decision=RiskDecision(row["risk_decision"]) if row.get("risk_decision") else None,
            error_message=row.get("error_message"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
        )

    async def get_user_actions(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[QueuedAction]:
        """Get user's action history."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM action_queue 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [
            QueuedAction(
                id=row["id"],
                user_id=row["user_id"],
                action_type=ActionType(row["action_type"]),
                status=ActionStatus(row["status"]),
                payload=eval(row["payload"]),
                risk_decision=RiskDecision(row["risk_decision"]) if row.get("risk_decision") else None,
                error_message=row.get("error_message"),
                created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
                started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
                completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
            )
            for row in rows
        ]

    async def cancel_action(self, action_id: int, user_id: int) -> bool:
        """Cancel a queued action."""
        action = await self.get_status(action_id)
        if not action or action.user_id != user_id:
            return False

        if action.status != ActionStatus.QUEUED:
            return False

        await self.db.execute(
            """
            UPDATE action_queue 
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (ActionStatus.FAILED.value, datetime.utcnow().isoformat(), action_id),
        )
        logger.info(f"Cancelled action {action_id}")
        return True

    async def _process_queue(self) -> None:
        """Process queued actions."""
        if self._processing:
            return

        self._processing = True
        logger.info("Starting action queue processing")

        try:
            while not self._queue.empty():
                action_id = await self._queue.get()
                await self._execute_action(action_id)
        finally:
            self._processing = False
            logger.info("Action queue processing stopped")

    async def _execute_action(self, action_id: int) -> None:
        """Execute a single action."""
        action = await self.get_status(action_id)
        if not action:
            logger.warning(f"Action {action_id} not found")
            return

        if action.status != ActionStatus.QUEUED:
            logger.info(f"Action {action_id} already processed")
            return

        await self._update_status(action_id, ActionStatus.EXECUTING)

        handler = self._handlers.get(action.action_type)
        if not handler:
            await self._update_status(
                action_id,
                ActionStatus.FAILED,
                error="No handler registered for action type",
            )
            return

        try:
            result = await handler(action.payload)
            await self._update_status(
                action_id,
                ActionStatus.COMPLETED,
                result=result,
            )
            logger.info(f"Executed action {action_id}: {action.action_type.value}")
        except Exception as e:
            await self._update_status(
                action_id,
                ActionStatus.FAILED,
                error=str(e),
            )
            logger.error(f"Failed to execute action {action_id}: {e}")

    async def _update_status(
        self,
        action_id: int,
        status: ActionStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update action status in database."""
        now = datetime.utcnow().isoformat()
        await self.db.execute(
            f"""
            UPDATE action_queue 
            SET status = ?, {f'result = ?, ' if result else ''}{f'error_message = ?, ' if error else ''}updated_at = ?
            WHERE id = ?
            """,
            [s for s in [status.value, str(result) if result else None, error, now, action_id] if s is not None],
        )
