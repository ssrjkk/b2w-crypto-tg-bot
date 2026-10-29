"""Unit tests for risk service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.enums import Network, RiskDecision
from app.services.risk_service import RiskService


def _db(trades_in_hour: int = 0, last_trade=None) -> MagicMock:
    """Сервис считает сделки через `db.execute(select(func.count(...))).scalar()`
    и кулдаун через `.scalar_one_or_none()` — мок повторяет этот порядок."""
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=trades_in_hour)
    cooldown_result = MagicMock()
    cooldown_result.scalar_one_or_none = MagicMock(return_value=last_trade)

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[count_result, cooldown_result])
    return db


class TestRiskService:
    """Tests for RiskService."""

    @pytest.fixture
    def risk_service(self, mock_db):
        return RiskService(mock_db)

    @pytest.mark.asyncio
    async def test_validate_trade_approved(self):
        """Test trade validation when all checks pass."""
        risk_service = RiskService(_db(trades_in_hour=0))

        result = await risk_service.validate_trade(
            user_id=1,
            amount="100",
            network=Network.ARBITRUM,
            dex_name="gmx",
            balance="1000",
        )

        assert result.decision == RiskDecision.APPROVED
        assert result.reason == "All risk checks passed"

    @pytest.mark.asyncio
    async def test_validate_trade_unsupported_network(self, risk_service):
        """Test trade validation with unsupported network."""
        result = await risk_service.validate_trade(
            user_id=1,
            amount="100",
            network=Network.BSC,
            dex_name="gmx",
            balance="1000",
        )

        assert result.decision == RiskDecision.REJECTED
        assert "not supported" in result.reason

    @pytest.mark.asyncio
    async def test_validate_trade_unsupported_dex(self, risk_service):
        """Test trade validation with unsupported DEX."""
        result = await risk_service.validate_trade(
            user_id=1,
            amount="100",
            network=Network.ARBITRUM,
            dex_name="unknown_dex",
            balance="1000",
        )

        assert result.decision == RiskDecision.REJECTED
        assert "not supported" in result.reason

    @pytest.mark.asyncio
    async def test_validate_trade_exceeds_max_position(self, risk_service):
        """Test trade validation when amount exceeds max position."""
        result = await risk_service.validate_trade(
            user_id=1,
            amount="500",
            network=Network.ARBITRUM,
            dex_name="gmx",
            balance="1000",
        )

        assert result.decision == RiskDecision.REJECTED
        assert "exceeds max position" in result.reason

    @pytest.mark.asyncio
    async def test_validate_trade_max_trades_exceeded(self):
        """Test trade validation when max trades per hour exceeded."""
        risk_service = RiskService(_db(trades_in_hour=10))

        result = await risk_service.validate_trade(
            user_id=1,
            amount="100",
            network=Network.ARBITRUM,
            dex_name="gmx",
            balance="1000",
        )

        assert result.decision == RiskDecision.REJECTED
        assert "Max trades per hour" in result.reason

    @pytest.mark.asyncio
    async def test_kill_switch_activation(self, risk_service):
        """Test kill switch activation."""
        risk_service.activate_kill_switch()

        result = await risk_service.validate_trade(
            user_id=1,
            amount="100",
            network=Network.ARBITRUM,
            dex_name="gmx",
            balance="1000",
        )

        assert result.decision == RiskDecision.KILL_SWITCH

    @pytest.mark.asyncio
    async def test_kill_switch_deactivation(self):
        """Test kill switch deactivation."""
        risk_service = RiskService(_db(trades_in_hour=0))
        risk_service.activate_kill_switch()
        risk_service.deactivate_kill_switch()

        result = await risk_service.validate_trade(
            user_id=1,
            amount="100",
            network=Network.ARBITRUM,
            dex_name="gmx",
            balance="1000",
        )

        assert result.decision == RiskDecision.APPROVED

    def test_calculate_max_position(self, risk_service):
        """Test max position calculation."""
        max_pos = risk_service._calculate_max_position("1000")
        assert max_pos == 100.0

        max_pos = risk_service._calculate_max_position("0")
        assert max_pos == 0.0
