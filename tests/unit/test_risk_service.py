"""Unit tests for risk service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.risk_service import RiskService, RiskCheckResult
from app.core.enums import Network, RiskDecision


class TestRiskService:
    """Tests for RiskService."""

    @pytest.fixture
    def risk_service(self, mock_db):
        return RiskService(mock_db)

    @pytest.mark.asyncio
    async def test_validate_trade_approved(self, risk_service, mock_db):
        """Test trade validation when all checks pass."""
        mock_db.fetchone = AsyncMock(return_value={"count": 0})

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
    async def test_validate_trade_max_trades_exceeded(self, risk_service, mock_db):
        """Test trade validation when max trades per hour exceeded."""
        mock_db.fetchone = AsyncMock(return_value={"count": 10})

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
    async def test_kill_switch_deactivation(self, risk_service):
        """Test kill switch deactivation."""
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
