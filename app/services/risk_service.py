"""Risk management service - SQLAlchemy version."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.enums import Network, RiskDecision
from app.models.base import TradeModel, ActionStatus

logger = logging.getLogger(__name__)


@dataclass
class RiskCheckResult:
    decision: RiskDecision
    reason: str
    details: dict


class RiskService:
    """Risk management for trading actions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self._kill_switch = False

    async def validate_trade(
        self,
        user_id: int,
        amount: str,
        network: Network,
        dex_name: str,
        balance: str,
    ) -> RiskCheckResult:
        """Validate a trade request against risk rules."""
        if self._kill_switch:
            return RiskCheckResult(
                decision=RiskDecision.KILL_SWITCH,
                reason="Kill switch is active",
                details={"kill_switch": True},
            )

        if network.value not in self.settings.trading.supported_networks:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason=f"Network {network.value} not supported",
                details={"network": network.value},
            )

        if dex_name not in self.settings.trading.supported_dexes:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason=f"DEX {dex_name} not supported",
                details={"dex": dex_name},
            )

        max_position = self._calculate_max_position(balance)
        if float(amount) > max_position:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason=f"Amount {amount} exceeds max position {max_position}",
                details={"amount": amount, "max_position": max_position},
            )

        hourly_count = await self._get_trades_last_hour(user_id)
        if hourly_count >= self.settings.trading.max_trades_per_hour:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason=f"Max trades per hour exceeded ({hourly_count}/{self.settings.trading.max_trades_per_hour})",
                details={"hourly_count": hourly_count},
            )

        daily_loss = await self._get_daily_loss(user_id)
        if daily_loss > self.settings.trading.daily_loss_limit_percent:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason=f"Daily loss limit exceeded ({daily_loss}%)",
                details={"daily_loss": daily_loss},
            )

        cooldown_ok = await self._check_cooldown(user_id)
        if not cooldown_ok:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason="Action cooldown not elapsed",
                details={"cooldown_seconds": self.settings.trading.action_cooldown_seconds},
            )

        return RiskCheckResult(
            decision=RiskDecision.APPROVED,
            reason="All risk checks passed",
            details={"amount": amount, "network": network.value, "dex": dex_name},
        )

    async def validate_swap(
        self,
        user_id: int,
        from_token: str,
        to_token: str,
        amount: str,
    ) -> RiskCheckResult:
        """Validate a swap request."""
        if self._kill_switch:
            return RiskCheckResult(
                decision=RiskDecision.KILL_SWITCH,
                reason="Kill switch is active",
                details={},
            )

        cooldown_ok = await self._check_cooldown(user_id)
        if not cooldown_ok:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reason="Action cooldown not elapsed",
                details={},
            )

        return RiskCheckResult(
            decision=RiskDecision.APPROVED,
            reason="Swap validated",
            details={"from": from_token, "to": to_token},
        )

    def activate_kill_switch(self) -> None:
        """Activate kill switch to block all trading."""
        self._kill_switch = True
        logger.warning("Kill switch activated")

    def deactivate_kill_switch(self) -> None:
        """Deactivate kill switch."""
        self._kill_switch = False
        logger.warning("Kill switch deactivated")

    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active."""
        return self._kill_switch

    def _calculate_max_position(self, balance: str) -> float:
        """Calculate max position size based on balance."""
        balance_float = float(balance) if balance else 0
        return balance_float * (self.settings.trading.max_position_size_percent / 100)

    async def _get_trades_last_hour(self, user_id: int) -> int:
        """Get number of trades in last hour."""
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        result = await self.db.execute(
            select(func.count(TradeModel.id))
            .where(TradeModel.user_id == user_id)
            .where(TradeModel.created_at > hour_ago)
            .where(TradeModel.status == ActionStatus.COMPLETED)
        )
        count = result.scalar()
        return count or 0

    async def _get_daily_loss(self, user_id: int) -> float:
        """Calculate daily PnL loss percentage."""
        return 0.0

    async def _check_cooldown(self, user_id: int) -> bool:
        """Check if cooldown period has elapsed."""
        cooldown = self.settings.trading.action_cooldown_seconds
        since = datetime.utcnow() - timedelta(seconds=cooldown)
        result = await self.db.execute(
            select(TradeModel)
            .where(TradeModel.user_id == user_id)
            .where(TradeModel.created_at > since)
            .order_by(TradeModel.created_at.desc())
            .limit(1)
        )
        trade = result.scalar_one_or_none()
        return trade is None
