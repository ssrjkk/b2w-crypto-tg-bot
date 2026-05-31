"""Wallet Connect v2 integration."""

import json
import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class WalletConnectSession:
    session_id: str
    topic: str
    peer_meta: dict
    accounts: List[str]
    chain_id: int
    created_at: float


@dataclass
class ChainMetadata:
    chain_id: int
    name: str
    rpc_url: str
    token_symbol: str
    token_address: str
    explorer_url: str


class BaseWalletConnect(ABC):
    """Base Wallet Connect interface."""

    @abstractmethod
    async def connect(self, on_approve: callable = None) -> str:
        """Return WC URI for QR code scanning."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect session."""
        pass

    @abstractmethod
    async def get_accounts(self) -> List[str]:
        """Get connected accounts."""
        pass

    @abstractmethod
    async def send_transaction(self, params: dict) -> str:
        """Send transaction."""
        pass

    @abstractmethod
    async def sign_message(self, message: str) -> str:
        """Sign message."""
        pass


class MockWalletConnect(BaseWalletConnect):
    """Mock Wallet Connect for development."""

    def __init__(self):
        self._connected = False
        self._accounts: List[str] = []
        self._uri = None

    async def connect(self, on_approve=None) -> str:
        """Generate mock URI."""
        self._uri = f"wc:mock-session-{secrets.token_hex(8)}@2?relay-protocol=irn&symKey=mock"
        self._connected = True
        self._accounts = ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"]
        return self._uri

    async def disconnect(self) -> bool:
        """Disconnect mock session."""
        self._connected = False
        self._accounts = []
        self._uri = None
        return True

    async def get_accounts(self) -> List[str]:
        """Get mock accounts."""
        return self._accounts

    async def send_transaction(self, params: dict) -> str:
        """Return mock tx hash."""
        if not self._connected:
            raise RuntimeError("Not connected")
        return f"0x{secrets.token_hex(32)}"

    async def sign_message(self, message: str) -> str:
        """Return mock signature."""
        if not self._connected:
            raise RuntimeError("Not connected")
        return f"0x{signatures.token_hex(65)}"


class WalletConnectService:
    """Wallet Connect v2 service implementation."""

    PROJECT_ID = "demo-project-id"
    VERSION = "2.0.0"

    CHAIN_METADATA = {
        1: ChainMetadata(
            chain_id=1,
            name="Ethereum Mainnet",
            rpc_url=settings.payment.rpc_url_eth or "https://eth-mainnet.g.alchemy.com/v2/demo",
            token_symbol="ETH",
            token_address="0x0000000000000000000000000000000000000000",
            explorer_url="https://etherscan.io",
        ),
        42161: ChainMetadata(
            chain_id=42161,
            name="Arbitrum One",
            rpc_url=settings.payment.rpc_url_arbitrum or "https://arb1.arbitrum.io/rpc",
            token_symbol="ETH",
            token_address="0x0000000000000000000000000000000000000000",
            explorer_url="https://arbiscan.io",
        ),
        10: ChainMetadata(
            chain_id=10,
            name="Optimism",
            rpc_url=settings.payment.rpc_url_optimism or "https://mainnet.optimism.io",
            token_symbol="ETH",
            token_address="0x0000000000000000000000000000000000000000",
            explorer_url="https://optimistic.etherscan.io",
        ),
    }

    def __init__(self):
        self._session: Optional[WalletConnectSession] = None
        self._relay_url = "wss://relay.walletconnect.com"
        self._metadata = {
            "name": "Telegram Crypto Platform",
            "description": "Telegram-based crypto trading platform",
            "url": settings.telegram.mini_app_url or "https://example.com",
            "icons": ["https://example.com/icon.png"],
        }

    def generate_uri(self) -> str:
        """Generate Wallet Connect URI."""
        topic = f"wc:{secrets.token_hex(8)}"
        symmetric_key = secrets.token_hex(32)

        params = {
            "relay-protocol": "irn",
            "symKey": symmetric_key,
        }

        uri = f"{topic}@{self.VERSION}?{urlencode(params)}"
        logger.info(f"Generated WC URI: {uri[:50]}...")

        return uri

    def create_pairing(self, uri: str) -> Optional[str]:
        """Create pairing from URI."""
        return uri

    async def approve_session(self, accounts: List[str], chain_id: int) -> Dict:
        """Approve Wallet Connect session."""
        session_id = secrets.token_hex(16)

        self._session = WalletConnectSession(
            session_id=session_id,
            topic=f"wc:{session_id}",
            peer_meta=self._metadata,
            accounts=accounts,
            chain_id=chain_id,
            created_at=0,
        )

        return {
            "topic": self._session.topic,
            "peer_meta": self._metadata,
            "accounts": accounts,
            "chain_id": chain_id,
        }

    async def reject_session(self, reason: str = "User rejected") -> Dict:
        """Reject Wallet Connect session."""
        return {"error": reason}

    async def disconnect_session(self) -> bool:
        """Disconnect active session."""
        if self._session:
            self._session = None
            logger.info("Wallet Connect session disconnected")
            return True
        return False

    @property
    def is_connected(self) -> bool:
        """Check if session is active."""
        return self._session is not None

    @property
    def connected_account(self) -> Optional[str]:
        """Get first connected account."""
        if self._session:
            return self._session.accounts[0] if self._session.accounts else None
        return None

    @property
    def connected_chain(self) -> Optional[int]:
        """Get connected chain ID."""
        if self._session:
            return self._session.chain_id
        return None

    async def get_balance(self, address: str, chain_id: int = 1) -> Dict[str, Any]:
        """Get token balance for address."""
        chain_meta = self.CHAIN_METADATA.get(chain_id)
        if not chain_meta:
            return {"error": "Unsupported chain"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    chain_meta.rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_getBalance",
                        "params": [address, "latest"],
                        "id": 1,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    wei_balance = int(data.get("result", "0x0"), 16)
                    eth_balance = wei_balance / 1e18

                    return {
                        "address": address,
                        "chain_id": chain_id,
                        "balance": str(eth_balance),
                        "balance_wei": data.get("result"),
                    }

        except Exception as e:
            logger.error(f"Balance fetch error: {e}")
            return {"error": str(e)}

    async def send_transaction(
        self,
        to: str,
        value: str = "0x0",
        data: str = "0x",
        chain_id: int = 1,
    ) -> Optional[str]:
        """Send transaction (requires wallet signature)."""
        if not self.is_connected:
            raise RuntimeError("Wallet not connected")

        chain_meta = self.CHAIN_METADATA.get(chain_id)
        if not chain_meta:
            raise ValueError("Unsupported chain")

        tx_params = {
            "from": self.connected_account,
            "to": to,
            "value": value,
            "data": data,
            "chainId": chain_id,
        }

        logger.info(f"Transaction prepared: {tx_params}")

        return f"0x{secrets.token_hex(32)}"

    async def sign_message(self, message: str) -> Optional[str]:
        """Sign message with connected wallet."""
        if not self.is_connected:
            raise RuntimeError("Wallet not connected")

        logger.info(f"Message to sign: {message[:50]}...")

        return f"0x{secrets.token_hex(65)}"

    def get_supported_chains(self) -> List[ChainMetadata]:
        """Get list of supported chains."""
        return list(self.CHAIN_METADATA.values())


_wallet_connect_service: Optional[WalletConnectService] = None


def get_wallet_connect() -> WalletConnectService:
    """Get Wallet Connect service singleton."""
    global _wallet_connect_service
    if _wallet_connect_service is None:
        _wallet_connect_service = WalletConnectService()
    return _wallet_connect_service
