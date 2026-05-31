"""Health check endpoints."""

import time
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.database.manager import get_db_manager, DatabaseManager
from app.config.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    checks: dict[str, Any]


class ComponentHealth(BaseModel):
    name: str
    status: str
    details: Optional[dict] = None


_start_time = time.time()
settings = get_settings()


@router.get("", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Basic health check endpoint."""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime_seconds=time.time() - _start_time,
        checks={},
    )


@router.get("/live")
async def liveness() -> dict:
    """Liveness probe - is the service running?"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready", response_model=HealthStatus)
async def readiness(db_manager: DatabaseManager = Depends(get_db_manager)) -> HealthStatus:
    """Readiness probe - is the service ready to accept traffic?"""
    checks = {}
    overall_status = "healthy"

    try:
        async with db_manager.session() as session:
            await session.execute("SELECT 1")
        checks["database"] = ComponentHealth(name="database", status="healthy")
    except Exception as e:
        checks["database"] = ComponentHealth(
            name="database", status="unhealthy", details={"error": str(e)}
        )
        overall_status = "degraded"

    if settings.telegram.bot_token:
        checks["telegram"] = ComponentHealth(name="telegram", status="configured")
    else:
        checks["telegram"] = ComponentHealth(name="telegram", status="not_configured")

    rpc_configured = any([
        settings.payment.rpc_url_eth,
        settings.payment.rpc_url_arbitrum,
        settings.payment.rpc_url_optimism,
    ])
    checks["rpc"] = ComponentHealth(name="rpc", status="configured" if rpc_configured else "not_configured")

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime_seconds=time.time() - _start_time,
        checks=checks,
    )


@router.get("/metrics")
async def metrics() -> dict:
    """Basic metrics endpoint."""
    from app.database.manager import get_db_manager
    from sqlalchemy import text

    db_manager = get_db_manager()
    metrics_data = {"uptime_seconds": time.time() - _start_time}

    try:
        async with db_manager.session() as session:
            result = await session.execute(text("SELECT COUNT(*) as count FROM users"))
            metrics_data["total_users"] = result.scalar()

            result = await session.execute(text("SELECT COUNT(*) as count FROM subscriptions WHERE status = 'active'"))
            metrics_data["active_subscriptions"] = result.scalar()

            result = await session.execute(text("SELECT COUNT(*) as count FROM trades WHERE created_at > NOW() - INTERVAL '24 hours'"))
            metrics_data["trades_24h"] = result.scalar()
    except Exception:
        pass

    return metrics_data
