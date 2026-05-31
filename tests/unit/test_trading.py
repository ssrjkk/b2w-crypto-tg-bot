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


class TestTradingOrchestrator:
    """Tests for TradingOrchestrator."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))
        db.fetchone = AsyncMock(return_value=None)
        db.fetchall = AsyncMock(return_value=[])
        return db

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
    async def test_execute_trade_rejected_by_risk(self, orchestrator, mock_db):
        """Test trade execution rejected by risk service."""
        mock_db.execute = AsyncMock(return_value=MagicMock(lastrowid=1))
        mock_db.fetchone = AsyncMock(return_value={"count": 10})

        from app.models.trading import TradeRequest

        result = await orchestrator.execute_trade(
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
