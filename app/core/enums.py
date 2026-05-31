"""Application enums."""

from enum import Enum


class SubscriptionStatus(str, Enum):
    INACTIVE = "inactive"
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    FAILED = "failed"


class ActionType(str, Enum):
    TRADE = "trade"
    SWAP = "swap"
    TRANSFER = "transfer"
    CLAIM = "claim"
    STAKE = "stake"
    MINT = "mint"


class ActionStatus(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class Network(str, Enum):
    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "bsc"


class DexName(str, Enum):
    GMX = "gmx"
    DYDX = "dydx"
    UNISWAP = "uniswap"


class RiskDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    KILL_SWITCH = "kill_switch"


class AirdropStatus(str, Enum):
    NOT_ELIGIBLE = "not_eligible"
    ELIGIBLE = "eligible"
    CLAIMABLE = "claimable"
    CLAIMED = "claimed"
