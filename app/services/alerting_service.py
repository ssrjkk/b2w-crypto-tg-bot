"""Alerting service for Telegram notifications."""

import logging
from typing import Optional

from app.core.enums import ActionStatus, RiskDecision

logger = logging.getLogger(__name__)


class AlertingService:
    """Telegram alerting for user notifications."""

    def __init__(self, bot, chat_id: Optional[int] = None):
        self.bot = bot
        self.chat_id = chat_id
        self._admin_chat_ids: list[int] = []

    def set_admin_chat_ids(self, chat_ids: list[int]) -> None:
        """Set admin chat IDs for alerts."""
        self._admin_chat_ids = chat_ids

    async def notify_action_status(
        self,
        chat_id: int,
        action_type: str,
        status: ActionStatus,
        details: dict,
    ) -> None:
        """Notify user about action status."""
        if not self.bot:
            return

        status_emoji = {
            ActionStatus.QUEUED: "⏳",
            ActionStatus.VALIDATING: "🔍",
            ActionStatus.EXECUTING: "⚙️",
            ActionStatus.COMPLETED: "✅",
            ActionStatus.FAILED: "❌",
            ActionStatus.BLOCKED: "🛑",
        }

        emoji = status_emoji.get(status, "📋")
        message = f"{emoji} *Action Update*\n\n"
        message += f"*Type:* {action_type}\n"
        message += f"*Status:* {status.value}\n"

        if details.get("reason"):
            message += f"\n*Reason:* {details['reason']}"

        if details.get("amount"):
            message += f"\n*Amount:* {details['amount']}"

        try:
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def notify_risk_block(
        self,
        chat_id: int,
        action_type: str,
        reason: str,
        details: dict,
    ) -> None:
        """Notify user about blocked action."""
        if not self.bot:
            return

        message = f"🛑 *Action Blocked*\n\n"
        message += f"*Type:* {action_type}\n"
        message += f"*Reason:* {reason}\n"

        if details:
            message += f"\n*Details:*\n"
            for k, v in details.items():
                message += f"  - {k}: {v}\n"

        try:
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send risk block notification: {e}")

    async def notify_payment_received(
        self,
        chat_id: int,
        amount: str,
        token: str,
        tx_hash: str,
    ) -> None:
        """Notify about received payment."""
        if not self.bot:
            return

        message = f"💰 *Payment Received*\n\n"
        message += f"*Amount:* {amount} {token}\n"
        message += f"*Tx:* `{tx_hash[:16]}...`\n\n"
        message += f"Processing activation..."

        try:
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send payment notification: {e}")

    async def notify_subscription_activated(
        self,
        chat_id: int,
        expiry_date: str,
    ) -> None:
        """Notify about activated subscription."""
        if not self.bot:
            return

        message = f"🎉 *Subscription Activated*\n\n"
        message += f"Your premium subscription is now active!\n"
        message += f"*Expires:* {expiry_date}\n\n"
        message += f"Use /help to see available commands."

        try:
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send subscription activation notification: {e}")

    async def notify_error(
        self,
        chat_id: int,
        error_message: str,
        action_type: Optional[str] = None,
    ) -> None:
        """Notify about an error."""
        if not self.bot:
            return

        message = f"⚠️ *Error*\n\n"
        message += f"_{error_message}_\n"
        if action_type:
            message += f"\n*Action:* {action_type}"

        try:
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    async def notify_admin(self, message: str) -> None:
        """Send notification to all admins."""
        for chat_id in self._admin_chat_ids:
            try:
                await self.bot.send_message(chat_id, message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")
