"""Real-time price feed service."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

import httpx

from app.cache.manager import get_cache

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    token: str
    price_usd: Decimal
    change_24h: float
    volume_24h: float
    timestamp: float


class PriceFeed(ABC):
    """Base price feed interface."""

    @abstractmethod
    async def get_price(self, token: str) -> Optional[PriceData]:
        pass

    @abstractmethod
    async def get_prices(self, tokens: list[str]) -> dict[str, PriceData]:
        pass


class CoinGeckoPriceFeed(PriceFeed):
    """CoinGecko price feed implementation."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    TOKEN_MAPPING = {
        "ETH": "ethereum",
        "BTC": "bitcoin",
        "USDC": "usd-coin",
        "USDT": "tether",
        "GMX": "gmx",
        "ARB": "arbitrum",
        "OP": "optimism",
        "DYP": "dydx",
        "WETH": "weth",
    }

    async def get_price(self, token: str) -> Optional[PriceData]:
        """Get price for single token."""
        cache = get_cache()
        cache_key = f"price:{token}"

        cached = await cache.get(cache_key)
        if cached:
            return PriceData(**cached)

        token_id = self.TOKEN_MAPPING.get(token.upper(), token.lower())

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/simple/price",
                params={
                    "ids": token_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                },
            )

            if response.status_code == 200:
                data = response.json()
                if token_id in data:
                    price_data = data[token_id]
                    result = PriceData(
                        token=token,
                        price_usd=Decimal(str(price_data.get("usd", 0))),
                        change_24h=price_data.get("usd_24h_change", 0),
                        volume_24h=price_data.get("usd_24h_vol", 0),
                        timestamp=response.headers.get("date", ""),
                    )
                    await cache.set(cache_key, {
                        "token": result.token,
                        "price_usd": str(result.price_usd),
                        "change_24h": result.change_24h,
                        "volume_24h": result.volume_24h,
                        "timestamp": result.timestamp,
                    }, ttl=60)
                    return result

        except Exception as e:
            logger.error(f"CoinGecko price fetch error for {token}: {e}")

        return None

    async def get_prices(self, tokens: list[str]) -> dict[str, PriceData]:
        """Get prices for multiple tokens."""
        token_ids = [self.TOKEN_MAPPING.get(t.upper(), t.lower()) for t in tokens]

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/simple/price",
                params={
                    "ids": ",".join(token_ids),
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                },
            )

            if response.status_code == 200:
                data = response.json()
                result = {}
                for token, token_id in zip(tokens, token_ids):
                    if token_id in data:
                        price_data = data[token_id]
                        result[token] = PriceData(
                            token=token,
                            price_usd=Decimal(str(price_data.get("usd", 0))),
                            change_24h=price_data.get("usd_24h_change", 0),
                            volume_24h=price_data.get("usd_24h_vol", 0),
                            timestamp=0,
                        )
                return result

        except Exception as e:
            logger.error(f"CoinGecko batch price fetch error: {e}")

        return {}


class PriceFeedService:
    """Unified price feed service with caching."""

    def __init__(self):
        self._feed: Optional[PriceFeed] = None

    @property
    def feed(self) -> PriceFeed:
        if not self._feed:
            self._feed = CoinGeckoPriceFeed()
        return self._feed

    async def get_price(self, token: str) -> Optional[PriceData]:
        """Get price for token."""
        return await self.feed.get_price(token)

    async def get_prices(self, tokens: list[str]) -> dict[str, PriceData]:
        """Get prices for multiple tokens."""
        return await self.feed.get_prices(tokens)

    async def get_quote_for_trade(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
    ) -> Optional[dict]:
        """Get quote for trade with price impact calculation."""
        from_price = await self.get_price(from_token)
        to_price = await self.get_price(to_token)

        if not from_price or not to_price:
            return None

        from_amount_usd = amount * from_price.price_usd
        expected_output = from_amount_usd / to_price.price_usd

        price_impact = abs(from_price.change_24h - to_price.change_24h) / 2

        return {
            "from_token": from_token,
            "to_token": to_token,
            "from_amount": str(amount),
            "expected_output": str(expected_output),
            "price_impact": price_impact,
            "from_price_usd": str(from_price.price_usd),
            "to_price_usd": str(to_price.price_usd),
        }


_price_feed_service: Optional[PriceFeedService] = None


def get_price_feed() -> PriceFeedService:
    """Get price feed service singleton."""
    global _price_feed_service
    if _price_feed_service is None:
        _price_feed_service = PriceFeedService()
    return _price_feed_service
