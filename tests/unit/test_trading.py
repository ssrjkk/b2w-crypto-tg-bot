"""Unit tests for trading orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.trading.orchestrator import TradingOrchestrator
from app.services.risk_service import RiskService
from app.core.enums import DexName, Network, OrderSide, OrderType, RiskDecision


class MockDexAdapter:
    """Mock DEX adapter for testing."""

    def __init__(self):
        self.name = "mock"

    async def get_quote(self, from_token, to_token, amount, side, order_type=None):
        return MagicMock(price="100", price_impact=0.1, estimated_gas="1000", slippage_actual=0.5)

    async def execute_trade(self, from_token, to_token, amount, side, max_slippage=2.0):
        return MagicMock(success=True, transaction_hash="0x123", executed_price="100")

    async def get_balance(self, token, address):
        return "1000"

    async def get_gas_price(self):
        return "10"


def _db(trades_in_hour: int = 0):
    """Risk-сервис оркестратора читает счётчик через `db.execute(...).scalar()`,
    а запись о сделке пишется через add/commit/refresh той же сессии."""
    result = MagicMock()
    result.scalar = MagicMock(return_value=trades_in_hour)
    result.scalar_one_or_none = MagicMock(return_value=None)
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestTradingOrchestrator:
    """Tests for TradingOrchestrator."""

    @pytest.fixture
    def mock_db(self):
        return _db()

    @pytest.fixture
    def risk_service(self, mock_db):
        return RiskService(mock_db)

    @pytest.fixture
    def orchestrator(self, mock_db, risk_service):
        orch = TradingOrchestrator(mock_db, risk_service)
        orch.register_adapter(DexName.GMX, Network.ARBITRUM, MockDexAdapter())
        return orch

    def test_register_adapter(self, orchestrator):
        """Test registering a DEX adapter."""
        adapter = orchestrator.get_adapter(DexName.GMX, Network.ARBITRUM)
        assert adapter is not None
        assert adapter.name == "mock"

    def test_get_adapter_not_found(self, orchestrator):
        """Test getting non-existent adapter."""
        adapter = orchestrator.get_adapter(DexName.DYDX, Network.ETHEREUM)
        assert adapter is None

    @pytest.mark.asyncio
    async def test_execute_trade_rejected_by_risk(self):
        """Test trade execution rejected by risk service."""
        db = _db(trades_in_hour=10)
        orch = TradingOrchestrator(db, RiskService(db))
        orch.register_adapter(DexName.GMX, Network.ARBITRUM, MockDexAdapter())

        from app.models.trading import TradeRequest

        result = await orch.execute_trade(
            TradeRequest(
                user_id=1,
                dex=DexName.GMX,
                network=Network.ARBITRUM,
                from_token="ETH",
                to_token="USDC",
                amount="100",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
            )
        )

        assert result.success is False
        assert result.risk_decision != RiskDecision.APPROVED
