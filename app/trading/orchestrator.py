"""Trading orchestrator - SQLAlchemy version."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseDexAdapter, ExecutionResult, QuoteResult
from app.config.settings import get_settings
from app.core.enums import ActionStatus, DexName, Network, OrderSide, OrderType, RiskDecision
from app.core.exceptions import QuoteError
from app.models.base import TradeModel
from app.models.trading import Quote, QuoteRequest, Trade, TradeRequest
from app.services.risk_service import RiskCheckResult, RiskService

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    success: bool
    trade_id: int
    transaction_hash: Optional[str] = None
    executed_price: Optional[str] = None
    error: Optional[str] = None
    risk_decision: Optional[RiskDecision] = None


class TradingOrchestrator:
    """Orchestrates the quote -> validate -> execute flow."""

    def __init__(self, db: AsyncSession, risk_service: RiskService):
        self.db = db
        self.risk_service = risk_service
        self.settings = get_settings()
        self._adapters: dict[str, dict[Network, BaseDexAdapter]] = {}

    def register_adapter(self, dex: DexName, network: Network, adapter: BaseDexAdapter) -> None:
        """Register a DEX adapter."""
        if dex.value not in self._adapters:
            self._adapters[dex.value] = {}
        self._adapters[dex.value][network] = adapter
        logger.info(f"Registered adapter: {dex.value} on {network.value}")

    def get_adapter(self, dex: DexName, network: Network) -> Optional[BaseDexAdapter]:
        """Get adapter for DEX and network."""
        return self._adapters.get(dex.value, {}).get(network)

    async def get_quote(self, request: QuoteRequest) -> Quote:
        """Get quote from DEX."""
        adapter = self.get_adapter(request.dex, request.network)
        if not adapter:
            raise QuoteError()

        quote_result = await adapter.get_quote(
            request.from_token,
            request.to_token,
            request.amount,
            request.side,
            request.order_type,
        )

        if quote_result.price == "0":
            raise QuoteError()

        valid_until = datetime.utcnow() + timedelta(minutes=5)

        return Quote(
            request=request,
            price=quote_result.price,
            price_impact=quote_result.price_impact,
            estimated_gas=quote_result.estimated_gas,
            slippage_actual=quote_result.slippage_actual,
            valid_until=valid_until,
        )

    async def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Execute trade with quote validation and risk check."""
        try:
            quote = await self.get_quote(
                QuoteRequest(
                    user_id=request.user_id,
                    dex=request.dex,
                    network=request.network,
                    from_token=request.from_token,
                    to_token=request.to_token,
                    amount=request.amount,
                    side=request.side,
                    order_type=request.order_type,
                )
            )
        except QuoteError:
            return TradeResult(
                success=False,
                trade_id=0,
                error="Failed to get quote",
            )

        risk_result = await self.risk_service.validate_trade(
            user_id=request.user_id,
            amount=request.amount,
            network=request.network,
            dex_name=request.dex.value,
            balance="10000",
        )

        trade = await self._create_trade_record(
            user_id=request.user_id,
            quote_request=quote.request,
            risk_decision=risk_result.decision,
        )

        if risk_result.decision != RiskDecision.APPROVED:
            await self._update_trade_status(
                trade.id,
                ActionStatus.BLOCKED,
                error_message=risk_result.reason,
            )
            return TradeResult(
                success=False,
                trade_id=trade.id,
                error=risk_result.reason,
                risk_decision=risk_result.decision,
            )

        await self._update_trade_status(trade.id, ActionStatus.EXECUTING)

        adapter = self.get_adapter(request.dex, request.network)
        if not adapter:
            await self._update_trade_status(
                trade.id,
                ActionStatus.FAILED,
                error_message="No adapter available",
            )
            return TradeResult(
                success=False,
                trade_id=trade.id,
                error="No adapter available",
                risk_decision=risk_result.decision,
            )

        execution_result = await adapter.execute_trade(
            request.from_token,
            request.to_token,
            request.amount,
            request.side,
            request.max_slippage,
        )

        if execution_result.success:
            await self._update_trade_status(
                trade.id,
                ActionStatus.COMPLETED,
                tx_hash=execution_result.transaction_hash,
                executed_price=execution_result.executed_price,
            )
            return TradeResult(
                success=True,
                trade_id=trade.id,
                transaction_hash=execution_result.transaction_hash,
                executed_price=execution_result.executed_price,
                risk_decision=risk_result.decision,
            )
        else:
            await self._update_trade_status(
                trade.id,
                ActionStatus.FAILED,
                error_message=execution_result.error,
            )
            return TradeResult(
                success=False,
                trade_id=trade.id,
                error=execution_result.error,
                risk_decision=risk_result.decision,
            )

    async def get_trade_history(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[TradeModel]:
        """Get trade history for user."""
        result = await self.db.execute(
            select(TradeModel)
            .where(TradeModel.user_id == user_id)
            .order_by(TradeModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _create_trade_record(
        self,
        user_id: int,
        quote_request: QuoteRequest,
        risk_decision: RiskDecision,
    ) -> TradeModel:
        """Create trade record in database."""
        trade = TradeModel(
            user_id=user_id,
            dex=quote_request.dex.value,
            network=quote_request.network.value,
            from_token=quote_request.from_token,
            to_token=quote_request.to_token,
            amount=quote_request.amount,
            side=quote_request.side.value,
            order_type=quote_request.order_type.value,
            status=ActionStatus.QUEUED,
            risk_decision=risk_decision.value,
        )
        self.db.add(trade)
        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def _update_trade_status(
        self,
        trade_id: int,
        status: ActionStatus,
        tx_hash: Optional[str] = None,
        executed_price: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update trade status in database."""
        result = await self.db.execute(
            select(TradeModel).where(TradeModel.id == trade_id)
        )
        trade = result.scalar_one_or_none()

        if trade:
            trade.status = status
            if tx_hash:
                trade.transaction_hash = tx_hash
            if executed_price:
                trade.executed_price = executed_price
            if error_message:
                trade.error_message = error_message
            if status == ActionStatus.COMPLETED:
                trade.completed_at = datetime.utcnow()
            await self.db.commit()
