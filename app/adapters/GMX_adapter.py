"""GMX DEX real API adapter."""

import logging
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

import httpx

from app.adapters.base import BaseDexAdapter, ExecutionResult, QuoteResult
from app.core.enums import Network, OrderSide, OrderType
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class GMXMarket:
    token: str
    symbol: str
    index_price: str
    mark_price: str
    price_change_24h: float
    size: str
    max_size: str


@dataclass
class GMXOrderRequest:
    market: str
    side: str
    size: str
    limit_price: Optional[str] = None
    order_type: str = "market"
    trigger_price: Optional[str] = None


class GMXAPI:
    """GMX Real API client."""

    ARBITRUM_API = "https://arbitrum-api.gmx.io"
    AVALANCHE_API = "https://avalanche-api.gmx.io"

    def __init__(self, network: Network = Network.ARBITRUM):
        self.network = network
        self.api_url = self.ARBITRUM_API if network == Network.ARBITRUM else self.AVALANCHE_API
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_markets(self) -> list[GMXMarket]:
        """Get all available markets."""
        try:
            response = await self.client.get(f"{self.api_url}/tokens")
            if response.status_code == 200:
                data = response.json()
                return [GMXMarket(**m) for m in data.get("tokens", [])]
        except Exception as e:
            logger.error(f"GMX get markets error: {e}")
        return []

    async def get_market(self, token: str) -> Optional[GMXMarket]:
        """Get specific market."""
        try:
            response = await self.client.get(f"{self.api_url}/tokens/{token}")
            if response.status_code == 200:
                return GMXMarket(**response.json())
        except Exception as e:
            logger.error(f"GMX get market error: {e}")
        return None

    async def get_account(self, address: str) -> dict:
        """Get account information."""
        try:
            response = await self.client.get(
                f"{self.api_url}/wallet",
                params={"address": address},
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"GMX get account error: {e}")
        return {}

    async def get_position(self, address: str, market: str) -> dict:
        """Get position for market."""
        try:
            response = await self.client.get(
                f"{self.api_url}/positions/{address}/{market}",
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"GMX get position error: {e}")
        return {}

    async def create_order(self, address: str, order: GMXOrderRequest) -> dict:
        """Create trading order."""
        try:
            response = await self.client.post(
                f"{self.api_url}/orders",
                params={"address": address},
                json={
                    "market": order.market,
                    "side": order.side,
                    "size": order.size,
                    "order_type": order.order_type,
                    "trigger_price": order.trigger_price,
                },
            )
            if response.status_code in (200, 201):
                return response.json()
        except Exception as e:
            logger.error(f"GMX create order error: {e}")
        return {}

    async def cancel_order(self, address: str, order_id: str) -> dict:
        """Cancel order."""
        try:
            response = await self.client.delete(
                f"{self.api_url}/orders/{order_id}",
                params={"address": address},
            )
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            logger.error(f"GMX cancel order error: {e}")
            return {}

    async def get_gas_price(self) -> str:
        """Get current gas price."""
        try:
            response = await self.client.get(f"{self.api_url}/gas_price")
            if response.status_code == 200:
                data = response.json()
                return data.get("fast", "0")
        except Exception as e:
            logger.error(f"GMX gas price error: {e}")
        return "0"

    async def get_funding_rate(self, market: str) -> dict:
        """Get funding rate for market."""
        try:
            response = await self.client.get(f"{self.api_url}/funding/{market}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"GMX funding rate error: {e}")
        return {}

    async def getoi(self) -> dict:
        """Get open interest."""
        try:
            response = await self.client.get(f"{self.api_url}/open-interest")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"GMX OI error: {e}")
        return {}


class GMXAdapter(BaseDexAdapter):
    """GMX adapter using real API."""

    def __init__(self, network: Network = Network.ARBITRUM):
        super().__init__(network)
        self.api = GMXAPI(network)

    @property
    def name(self) -> str:
        return "gmx"

    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
    ) -> QuoteResult:
        """Get quote from GMX."""
        market = await self.api.get_market(to_token)

        if not market:
            return QuoteResult(
                price="0",
                price_impact=0,
                estimated_gas="0",
            )

        price = Decimal(market.mark_price)
        amount_dec = Decimal(amount)

        estimated_output = amount_dec * price
        price_impact = abs(market.price_change_24h)

        gas = await self.api.get_gas_price()
        gas_wei = int(gas) if gas else 0
        estimated_gas = str(gas_wei * 200000)

        return QuoteResult(
            price=str(price),
            price_impact=price_impact,
            estimated_gas=estimated_gas,
            slippage_actual=min(price_impact * 2, 2.0),
        )

    async def execute_trade(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        side: OrderSide,
        max_slippage: float = 2.0,
    ) -> ExecutionResult:
        """Execute trade on GMX."""
        try:
            market = await self.api.get_market(to_token)
            if not market:
                return ExecutionResult(
                    success=False,
                    error="Market not found",
                )

            order = GMXOrderRequest(
                market=to_token,
                side=side.value,
                size=amount,
                order_type="market",
            )

            result = await self.api.create_order(
                address="0x0000000000000000000000000000000000000000",
                order=order,
            )

            if result and result.get("orderId"):
                return ExecutionResult(
                    success=True,
                    transaction_hash=result.get("orderId"),
                    executed_price=market.mark_price,
                )

            return ExecutionResult(
                success=False,
                error="Order creation failed",
            )

        except Exception as e:
            logger.error(f"GMX execute trade error: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )

    async def get_balance(self, token: str, address: str) -> str:
        """Get token balance."""
        try:
            account = await self.api.get_account(address)
            if account:
                for t, balance in account.get("balances", {}).items():
                    if t.upper() == token.upper():
                        return balance
        except Exception as e:
            logger.error(f"GMX get balance error: {e}")
        return "0"

    async def get_gas_price(self) -> str:
        """Get current gas price."""
        return await self.api.get_gas_price()

    async def get_positions(self, address: str) -> list[dict]:
        """Get all positions."""
        markets = await self.api.get_markets()
        positions = []

        for market in markets:
            pos = await self.api.get_position(address, market.token)
            if pos:
                positions.append(pos)

        return positions

    async def get_funding(self, market: str) -> dict:
        """Get funding rate."""
        return await self.api.get_funding_rate(market)
