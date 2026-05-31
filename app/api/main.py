"""FastAPI main application."""

import logging
import time

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.api.routes import airdrop, dashboard, payment, subscription, trading
from app.api.health import router as health_router
from app.api.websocket import ws_router
from app.database.manager import get_db_manager

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    setup_logging()

    app = FastAPI(
        title="Telegram Crypto Platform API",
        description="API for Telegram Crypto Access & Trading Platform",
        version=settings.app_version,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [settings.telegram.mini_app_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Add process time header."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add request ID for tracing."""
        request_id = request.headers.get("X-Request-ID")
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id or ""
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler with logging."""
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
        )

    app.include_router(health_router)
    app.include_router(ws_router, tags=["websocket"])
    app.include_router(subscription.router, prefix="/api")
    app.include_router(payment.router, prefix="/api")
    app.include_router(trading.router, prefix="/api")
    app.include_router(airdrop.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")

    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info("API server starting", version=settings.app_version)

        db_manager = get_db_manager()
        await db_manager.init()
        logger.info("Database initialized")

        if settings.sentry.dsn:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry.dsn,
                environment=settings.environment,
                release=settings.app_version,
            )
            logger.info("Sentry initialized")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("API server shutting down")

        from app.database.manager import get_db_manager
        await get_db_manager().close()

        from app.cache.manager import get_cache
        await get_cache().close()

    return app


app = create_app()
