"""Optimized database manager with connection pooling and caching."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_database_url() -> str:
    """Get database URL from settings."""
    db_path = settings.database.path
    if db_path.startswith("postgresql"):
        return db_path
    if db_path.endswith(".db"):
        return f"sqlite+aiosqlite:///{db_path}"
    return f"sqlite+aiosqlite:///{db_path}"


class DatabaseManager:
    """Optimized async database manager with connection pooling."""

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._engine = None
        self._session_factory = None
        self._initialized = False

    def _create_engine(self):
        """Create optimized engine with connection pooling."""
        url = get_database_url()
        echo = settings.debug

        if url.startswith("sqlite"):
            engine = create_async_engine(
                url,
                echo=echo,
                poolclass=NullPool,
                connect_args={"check_same_thread": False},
            )
        else:
            engine = create_async_engine(
                url,
                echo=echo,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30,
            )

        return engine

    @property
    def engine(self):
        if not self._engine:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_factory(self):
        if not self._session_factory:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory

    async def init(self) -> None:
        """Initialize database engine and create tables."""
        if self._initialized:
            return

        from app.models.base import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self._initialized = True
        logger.info("Database initialized with connection pooling")

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get optimized database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get transaction context for batch operations."""
        async with self.session() as session:
            async with session.begin():
                yield session

    async def execute_bulk(self, operations: list) -> int:
        """Execute multiple operations in single transaction."""
        async with self.transaction() as session:
            for op in operations:
                await session.execute(op)
            return len(operations)


_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get database manager singleton."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with get_db_manager().session() as session:
        yield session