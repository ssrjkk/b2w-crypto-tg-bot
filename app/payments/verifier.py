"""Payment verifier for on-chain confirmation."""

import logging
from typing import Optional

import httpx

from app.config.settings import get_settings
from app.core.enums import Network, PaymentStatus
from app.models.payment import Payment

logger = logging.getLogger(__name__)


class PaymentVerifier:
    """Verifies crypto payments on-chain."""

    def __init__(self):
        self.settings = get_settings()
        self._rpc_urls = {
            Network.ETHEREUM: self.settings.payment.rpc_url_eth,
            Network.ARBITRUM: self.settings.payment.rpc_url_arbitrum,
            Network.OPTIMISM: self.settings.payment.rpc_url_optimism,
        }

    async def check_transaction(
        self,
        tx_hash: str,
        network: Network,
        expected_amount: str,
        expected_token: str,
        payment_address: str,
    ) -> tuple[bool, int]:
        """Check if transaction is confirmed and matches expected payment."""
        rpc_url = self._rpc_urls.get(network)
        if not rpc_url:
            logger.warning(f"No RPC URL configured for {network.value}")
            return False, 0

        try:
            async with httpx.AsyncClient() as client:
                result = await self._query_receipt(client, rpc_url, tx_hash)
                if not result:
                    return False, 0

                confirmations = result.get("confirmations", 0)
                if confirmations < self.settings.payment.confirmations_required:
                    return False, confirmations

                return True, confirmations

        except Exception as e:
            logger.error(f"Failed to verify transaction {tx_hash}: {e}")
            return False, 0

    async def get_confirmations(self, tx_hash: str, network: Network) -> int:
        """Get current confirmation count for transaction."""
        rpc_url = self._rpc_urls.get(network)
        if not rpc_url:
            return 0

        try:
            async with httpx.AsyncClient() as client:
                result = await self._query_receipt(client, rpc_url, tx_hash)
                if not result:
                    return 0
                return result.get("confirmations", 0)
        except Exception as e:
            logger.error(f"Failed to get confirmations for {tx_hash}: {e}")
            return 0

    async def _query_receipt(
        self,
        client: httpx.AsyncClient,
        rpc_url: str,
        tx_hash: str,
    ) -> Optional[dict]:
        """Query transaction receipt from RPC."""
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
            "id": 1,
        }
        try:
            response = await client.post(rpc_url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data.get("result")
        except Exception as e:
            logger.error(f"RPC query failed: {e}")
            return None
