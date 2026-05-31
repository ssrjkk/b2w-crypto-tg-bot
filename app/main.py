"""Main application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from app.adapters.GMX_adapter import GMXAdapter
from app.adapters.Uniswap_adapter import UniswapAdapter
from app.adapters.dYdX_adapter import DyDxAdapter
from app.api.dependencies import Database, get_database
from app.config.settings import get_settings
from app.core.enums import DexName, Network
from app.services.subscription_service import SubscriptionService
from app.payments.invoice import PaymentService
from app.services.risk_service import RiskService
from app.services.action_queue_service import ActionQueueService
from app.services.alerting_service import AlertingService
from app.trading.orchestrator import TradingOrchestrator
from app.airdrop.engine import AirdropEngine
from app.dashboard.service import DashboardService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

_services: Optional[dict] = None


def get_services() -> dict:
    """Get application services."""
    global _services
    if _services is None:
        raise RuntimeError("Services not initialized. Call init_services first.")
    return _services


async def init_services(db: Database) -> dict:
    """Initialize all application services."""
    global _services

    subscription_service = SubscriptionService(db)
    payment_service = PaymentService(db)
    risk_service = RiskService(db)
    action_queue_service = ActionQueueService(db)
    alerting_service = AlertingService(None)
    dashboard_service = DashboardService(db)
    airdrop_engine = AirdropEngine(db)

    trading_orchestrator = TradingOrchestrator(db, risk_service)

    trading_orchestrator.register_adapter(
        DexName.GMX, Network.ARBITRUM, GMXAdapter(Network.ARBITRUM)
    )
    trading_orchestrator.register_adapter(
        DexName.DYDX, Network.ETHEREUM, DyDxAdapter(Network.ETHEREUM)
    )
    trading_orchestrator.register_adapter(
        DexName.UNISWAP, Network.ETHEREUM, UniswapAdapter(Network.ETHEREUM)
    )

    _services = {
        "subscription": subscription_service,
        "payment": payment_service,
        "risk": risk_service,
        "action_queue": action_queue_service,
        "alerting": alerting_service,
        "dashboard": dashboard_service,
        "airdrop": airdrop_engine,
        "trading": trading_orchestrator,
    }

    logger.info("Services initialized")
    return _services


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    logger.info("Starting application...")

    db = await get_database()
    await init_services(db)

    yield

    await db.disconnect()
    logger.info("Application shutdown complete")


async def main():
    """Main entry point."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    db = await get_database()
    await init_services(db)

    from app.api.main import app as fastapi_app
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
