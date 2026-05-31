"""Base DEX adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.core.enums import Network, OrderSide, OrderType


@dataclass
class QuoteResult:
    price: str
    price_impact: float
    estimated_gas: str
    slippage_actual: Optional[float] = None
    valid_until: Optional[str] = None


@dataclass
class ExecutionResult:
    success: bool
    transaction_hash: Optional[str] = None
    executed_price: Optional[str] = None
    error: Optional[str] = None


class BaseDexAdapter(ABC):
    """Base class for DEX adapters."""

    def __init__(self, network: Network):
        self.network = network

    @property
    @abstractmethod
    def name(self) -> str:
        """DEX name."""
        pass

    @abstractmethod
    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
    ) -> QuoteResult:
        """Get quote for a trade."""
        pass

    @abstractmethod
    async def execute_trade(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        side: OrderSide,
        max_slippage: float = 2.0,
    ) -> ExecutionResult:
        """Execute a trade."""
        pass

    @abstractmethod
    async def get_balance(self, token: str, address: str) -> str:
        """Get token balance for address."""
        pass

    @abstractmethod
    async def get_gas_price(self) -> str:
        """Get current gas price."""
        pass
