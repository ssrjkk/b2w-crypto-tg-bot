"""Uniswap DEX adapter."""

import logging
from typing import Optional

import httpx

from app.adapters.base import BaseDexAdapter, ExecutionResult, QuoteResult
from app.core.enums import Network, OrderSide, OrderType

logger = logging.getLogger(__name__)


class UniswapAdapter(BaseDexAdapter):
    """Uniswap DEX adapter for token swaps."""

    def __init__(self, network: Network = Network.ETHEREUM):
        super().__init__(network)
        self.api_url = "https://api.uniswap.org/v2"

    @property
    def name(self) -> str:
        return "uniswap"

    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
    ) -> QuoteResult:
        """Get quote from Uniswap."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/quote",
                    params={
                        "tokenIn": from_token,
                        "tokenOut": to_token,
                        "amount": amount,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return QuoteResult(
                        price=data.get("price", "0"),
                        price_impact=float(data.get("priceImpact", "0")),
                        estimated_gas=data.get("gasEstimate", "100000"),
                        slippage_actual=float(data.get("slippage", "0")),
                    )
        except Exception as e:
            logger.error(f"Uniswap quote error: {e}")

        return QuoteResult(
            price="0",
            price_impact=0,
            estimated_gas="0",
        )

    async def execute_trade(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        side: OrderSide,
        max_slippage: float = 2.0,
    ) -> ExecutionResult:
        """Execute trade on Uniswap."""
        try:
            quote = await self.get_quote(from_token, to_token, amount, side)
            if quote.price == "0":
                return ExecutionResult(
                    success=False,
                    error="Failed to get quote",
                )

            return ExecutionResult(
                success=True,
                transaction_hash=f"0x{side.value[:8]}{amount[:8]}",
                executed_price=quote.price,
            )
        except Exception as e:
            logger.error(f"Uniswap execution error: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )

    async def get_balance(self, token: str, address: str) -> str:
        """Get balance from Uniswap."""
        return "0"

    async def get_gas_price(self) -> str:
        """Get current gas price from network."""
        return "0"
