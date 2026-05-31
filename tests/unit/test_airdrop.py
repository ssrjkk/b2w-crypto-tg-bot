"""Unit tests for airdrop rules engine."""

import pytest

from app.airdrop.rules import (
    RulesEngine,
    MinVolumeRule,
    MinTradesRule,
    NetworkActivityRule,
    HoldingDurationRule,
    RuleResult,
)


class TestEligibilityRules:
    """Tests for eligibility rules."""

    @pytest.mark.asyncio
    async def test_min_volume_rule_pass(self):
        """Test min volume rule when volume meets requirement."""
        rule = MinVolumeRule(1000)
        user_data = {"total_volume": 1500}

        result = await rule.check(user_data)

        assert result.passed is True
        assert result.reason.startswith("Volume 1500 meets")

    @pytest.mark.asyncio
    async def test_min_volume_rule_fail(self):
        """Test min volume rule when volume doesn't meet requirement."""
        rule = MinVolumeRule(1000)
        user_data = {"total_volume": 500}

        result = await rule.check(user_data)

        assert result.passed is False
        assert result.reason.startswith("Volume 500 below")

    @pytest.mark.asyncio
    async def test_min_trades_rule_pass(self):
        """Test min trades rule when trades meet requirement."""
        rule = MinTradesRule(10)
        user_data = {"total_trades": 15}

        result = await rule.check(user_data)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_min_trades_rule_fail(self):
        """Test min trades rule when trades don't meet requirement."""
        rule = MinTradesRule(10)
        user_data = {"total_trades": 5}

        result = await rule.check(user_data)

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_network_activity_rule_pass(self):
        """Test network activity rule when activity meets requirement."""
        rule = NetworkActivityRule("arbitrum", 5)
        user_data = {"activity_arbitrum": 10}

        result = await rule.check(user_data)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_holding_duration_rule_pass(self):
        """Test holding duration rule when duration meets requirement."""
        rule = HoldingDurationRule("ETH", 30)
        user_data = {"holding_days_ETH": 45}

        result = await rule.check(user_data)

        assert result.passed is True


class TestRulesEngine:
    """Tests for RulesEngine."""

    @pytest.fixture
    def rules_engine(self):
        return RulesEngine()

    @pytest.mark.asyncio
    async def test_evaluate_rules_all_passed(self, rules_engine):
        """Test evaluating rules when all pass."""
        rules = [
            {"type": "min_volume", "parameters": {"min_volume": 1000}, "required": True},
            {"type": "min_trades", "parameters": {"min_trades": 10}, "required": True},
        ]
        user_data = {"total_volume": 1500, "total_trades": 15}

        passed, results = await rules_engine.evaluate_rules(rules, user_data)

        assert passed is True
        assert len(results) == 2
        assert all(r.passed for r in results)

    @pytest.mark.asyncio
    async def test_evaluate_rules_some_failed(self, rules_engine):
        """Test evaluating rules when some fail."""
        rules = [
            {"type": "min_volume", "parameters": {"min_volume": 1000}, "required": True},
            {"type": "min_trades", "parameters": {"min_trades": 10}, "required": True},
        ]
        user_data = {"total_volume": 500, "total_trades": 15}

        passed, results = await rules_engine.evaluate_rules(rules, user_data)

        assert passed is False
        assert results[0].passed is False
        assert results[1].passed is True

    @pytest.mark.asyncio
    async def test_evaluate_rules_non_required_failed(self, rules_engine):
        """Test evaluating rules with non-required rule failed."""
        rules = [
            {"type": "min_volume", "parameters": {"min_volume": 1000}, "required": False},
            {"type": "min_trades", "parameters": {"min_trades": 10}, "required": True},
        ]
        user_data = {"total_volume": 500, "total_trades": 15}

        passed, results = await rules_engine.evaluate_rules(rules, user_data)

        assert passed is True

    @pytest.mark.asyncio
    async def test_create_rule_unknown_type(self, rules_engine):
        """Test creating rule with unknown type."""
        rule = rules_engine.create_rule("unknown_type", {})
        assert rule is None
