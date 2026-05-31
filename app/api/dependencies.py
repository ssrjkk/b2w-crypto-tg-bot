"""FastAPI application dependencies."""

from typing import Optional

from app.config.settings import get_settings


class Database:
    """Simple async database wrapper for SQLite."""

    def __init__(self, path: str = "data/platform.db"):
        import aiosqlite
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Initialize database connection."""
        import aiosqlite
        self._conn = await aiosqlite.connect(self.path)
        await self._create_tables()

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()

    async def execute(self, query: str, params: tuple = ()):
        """Execute a query."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return await self._conn.execute(query, params)

    async def fetchone(self, query: str, params: tuple = ()):
        """Fetch one row."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        cursor = await self._conn.execute(query, params)
        row = await cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    async def fetchall(self, query: str, params: tuple = ()):
        """Fetch all rows."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()
        if rows:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []

    async def commit(self) -> None:
        """Commit transaction."""
        if self._conn:
            await self._conn.commit()

    async def _create_tables(self) -> None:
        """Create database tables."""
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_active INTEGER DEFAULT 1,
                is_admin INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_name TEXT,
                status TEXT,
                start_date TEXT,
                expiry_date TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount TEXT,
                token TEXT,
                network TEXT,
                status TEXT,
                invoice_address TEXT,
                transaction_hash TEXT,
                confirmations INTEGER DEFAULT 0,
                expires_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dex TEXT,
                network TEXT,
                from_token TEXT,
                to_token TEXT,
                amount TEXT,
                side TEXT,
                order_type TEXT,
                status TEXT,
                risk_decision TEXT,
                transaction_hash TEXT,
                executed_price TEXT,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS action_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                status TEXT,
                payload TEXT,
                risk_decision TEXT,
                result TEXT,
                error_message TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                updated_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS airdrop_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                protocol TEXT,
                description TEXT,
                eligibility_rules TEXT,
                status TEXT,
                estimated_amount TEXT,
                start_date TEXT,
                end_date TEXT,
                created_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS airdrop_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                campaign_id INTEGER,
                status TEXT,
                progress_percent REAL,
                tasks_completed INTEGER,
                tasks_total INTEGER,
                last_checked_at TEXT,
                created_at TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                status TEXT,
                risk_decision TEXT,
                description TEXT,
                reason TEXT,
                result TEXT,
                metadata TEXT,
                created_at TEXT
            )
        """)

        await self._conn.commit()


_db_instance: Optional[Database] = None


async def get_database() -> Database:
    """Get database instance."""
    global _db_instance
    if _db_instance is None:
        settings = get_settings()
        _db_instance = Database(settings.database.path)
        await _db_instance.connect()
    return _db_instance
