"""Wallet connection service stub."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WalletBalance:
    address: str
    token: str
    balance: str
    balance_usd: Optional[float] = None


@dataclass
class WalletInfo:
    address: str
    network: str
    connected: bool = True


class WalletConnector(ABC):
    """Base wallet connector interface."""

    @abstractmethod
    async def connect(self) -> Optional[WalletInfo]:
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        pass

    @abstractmethod
    async def get_balance(self, token: str) -> Optional[WalletBalance]:
        pass

    @abstractmethod
    async def get_balances(self) -> list[WalletBalance]:
        pass

    @abstractmethod
    async def sign_message(self, message: str) -> Optional[str]:
        pass

    @abstractmethod
    async def send_transaction(self, tx_params: dict) -> Optional[str]:
        pass


class MockWalletConnector(WalletConnector):
    """Mock wallet connector for development."""

    def __init__(self, address: str = "0x0000000000000000000000000000000000000000"):
        self._address = address
        self._connected = False

    async def connect(self) -> Optional[WalletInfo]:
        """Connect mock wallet."""
        self._connected = True
        logger.info(f"Mock wallet connected: {self._address}")
        return WalletInfo(address=self._address, network="ethereum", connected=True)

    async def disconnect(self) -> bool:
        """Disconnect mock wallet."""
        self._connected = False
        logger.info("Mock wallet disconnected")
        return True

    async def get_balance(self, token: str) -> Optional[WalletBalance]:
        """Get mock balance."""
        if not self._connected:
            return None
        return WalletBalance(
            address=self._address,
            token=token,
            balance="0.0",
            balance_usd=0.0,
        )

    async def get_balances(self) -> list[WalletBalance]:
        """Get all mock balances."""
        if not self._connected:
            return []
        return [
            WalletBalance(address=self._address, token="ETH", balance="1.5", balance_usd=3000.0),
            WalletBalance(address=self._address, token="USDC", balance="5000", balance_usd=5000.0),
        ]

    async def sign_message(self, message: str) -> Optional[str]:
        """Sign mock message."""
        if not self._connected:
            return None
        return f"0xsigned:{message[:20]}"

    async def send_transaction(self, tx_params: dict) -> Optional[str]:
        """Send mock transaction."""
        if not self._connected:
            return None
        return "0x" + "a" * 64


class WalletService:
    """Wallet connection service."""

    def __init__(self):
        self._connector: Optional[WalletConnector] = None

    def set_connector(self, connector: WalletConnector) -> None:
        """Set wallet connector."""
        self._connector = connector

    @property
    def connector(self) -> WalletConnector:
        if not self._connector:
            self._connector = MockWalletConnector()
        return self._connector

    async def connect_wallet(self) -> Optional[WalletInfo]:
        """Connect wallet."""
        return await self.connector.connect()

    async def disconnect_wallet(self) -> bool:
        """Disconnect wallet."""
        return await self.connector.disconnect()

    async def get_balance(self, token: str) -> Optional[WalletBalance]:
        """Get token balance."""
        return await self.connector.get_balance(token)

    async def get_all_balances(self) -> list[WalletBalance]:
        """Get all balances."""
        return await self.connector.get_balances()

    async def verify_ownership(self, address: str, challenge: str) -> Optional[str]:
        """Verify wallet ownership via signature."""
        signature = await self.connector.sign_message(challenge)
        if signature:
            return f"{address}:{signature}"
        return None


_wallet_service: Optional[WalletService] = None


def get_wallet_service() -> WalletService:
    """Get wallet service singleton."""
    global _wallet_service
    if _wallet_service is None:
        _wallet_service = WalletService()
    return _wallet_service
