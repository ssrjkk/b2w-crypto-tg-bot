"""Airdrop eligibility rules engine."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RuleResult:
    passed: bool
    reason: str
    details: dict


class EligibilityRule:
    """Base class for eligibility rules."""

    def __init__(self, rule_id: str, description: str):
        self.rule_id = rule_id
        self.description = description

    async def check(self, user_data: dict) -> RuleResult:
        """Check if user meets the rule criteria."""
        raise NotImplementedError


class MinVolumeRule(EligibilityRule):
    """Check minimum trading volume."""

    def __init__(self, min_volume: float):
        super().__init__("min_volume", f"Minimum trading volume: {min_volume}")
        self.min_volume = min_volume

    async def check(self, user_data: dict) -> RuleResult:
        volume = user_data.get("total_volume", 0)
        if float(volume) >= self.min_volume:
            return RuleResult(
                passed=True,
                reason=f"Volume {volume} meets minimum {self.min_volume}",
                details={"volume": volume, "required": self.min_volume},
            )
        return RuleResult(
            passed=False,
            reason=f"Volume {volume} below minimum {self.min_volume}",
            details={"volume": volume, "required": self.min_volume},
        )


class MinTradesRule(EligibilityRule):
    """Check minimum number of trades."""

    def __init__(self, min_trades: int):
        super().__init__("min_trades", f"Minimum trades: {min_trades}")
        self.min_trades = min_trades

    async def check(self, user_data: dict) -> RuleResult:
        trades = user_data.get("total_trades", 0)
        if int(trades) >= self.min_trades:
            return RuleResult(
                passed=True,
                reason=f"Trades {trades} meets minimum {self.min_trades}",
                details={"trades": trades, "required": self.min_trades},
            )
        return RuleResult(
            passed=False,
            reason=f"Trades {trades} below minimum {self.min_trades}",
            details={"trades": trades, "required": self.min_trades},
        )


class NetworkActivityRule(EligibilityRule):
    """Check activity on specific network."""

    def __init__(self, network: str, min_activity: int):
        super().__init__("network_activity", f"Activity on {network}: {min_activity}")
        self.network = network
        self.min_activity = min_activity

    async def check(self, user_data: dict) -> RuleResult:
        activity = user_data.get(f"activity_{self.network}", 0)
        if int(activity) >= self.min_activity:
            return RuleResult(
                passed=True,
                reason=f"Network activity {activity} meets minimum {self.min_activity}",
                details={"network": self.network, "activity": activity},
            )
        return RuleResult(
            passed=False,
            reason=f"Network activity {activity} below minimum {self.min_activity}",
            details={"network": self.network, "activity": activity},
        )


class HoldingDurationRule(EligibilityRule):
    """Check token holding duration."""

    def __init__(self, token: str, min_days: int):
        super().__init__("holding_duration", f"Hold {token} for {min_days} days")
        self.token = token
        self.min_days = min_days

    async def check(self, user_data: dict) -> RuleResult:
        holding_days = user_data.get(f"holding_days_{self.token}", 0)
        if int(holding_days) >= self.min_days:
            return RuleResult(
                passed=True,
                reason=f"Holding duration {holding_days} days meets minimum {self.min_days}",
                details={"token": self.token, "days": holding_days},
            )
        return RuleResult(
            passed=False,
            reason=f"Holding duration {holding_days} days below minimum {self.min_days}",
            details={"token": self.token, "days": holding_days},
        )


class RulesEngine:
    """Engine for evaluating eligibility rules."""

    def __init__(self):
        self._rule_builders = {
            "min_volume": lambda params: MinVolumeRule(params["min_volume"]),
            "min_trades": lambda params: MinTradesRule(params["min_trades"]),
            "network_activity": lambda params: NetworkActivityRule(
                params["network"], params["min_activity"]
            ),
            "holding_duration": lambda params: HoldingDurationRule(
                params["token"], params["min_days"]
            ),
        }

    def create_rule(self, rule_type: str, parameters: dict) -> Optional[EligibilityRule]:
        """Create a rule from type and parameters."""
        builder = self._rule_builders.get(rule_type)
        if not builder:
            return None
        return builder(parameters)

    async def evaluate_rules(
        self,
        rules: list[dict],
        user_data: dict,
    ) -> tuple[bool, list[RuleResult]]:
        """Evaluate all rules and return results."""
        results = []
        all_passed = True

        for rule_config in rules:
            rule_type = rule_config.get("type")
            parameters = rule_config.get("parameters", {})

            rule = self.create_rule(rule_type, parameters)
            if not rule:
                continue

            result = await rule.check(user_data)
            results.append(result)

            if not result.passed and rule_config.get("required", True):
                all_passed = False

        return all_passed, results
