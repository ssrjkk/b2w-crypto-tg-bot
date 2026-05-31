"""Application configuration and settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    path: str = "data/platform.db"
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")


class TelegramSettings(BaseSettings):
    bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    mini_app_url: str = Field(default="", validation_alias="TELEGRAM_MINI_APP_URL")
    admin_ids: list[int] = Field(default_factory=list)


class PaymentSettings(BaseSettings):
    rpc_url_eth: str = Field(default="", validation_alias="RPC_URL_ETH")
    rpc_url_arbitrum: str = Field(default="", validation_alias="RPC_URL_ARBITRUM")
    rpc_url_optimism: str = Field(default="", validation_alias="RPC_URL_OPTIMISM")
    invoice_expiry_minutes: int = 30
    confirmations_required: int = 12


class TradingSettings(BaseSettings):
    max_position_size_percent: float = 10.0
    max_slippage_percent: float = 2.0
    max_trades_per_hour: int = 10
    daily_loss_limit_percent: float = 5.0
    action_cooldown_seconds: int = 5
    supported_networks: list[str] = Field(default_factory=lambda: ["arbitrum", "optimism"])
    supported_dexes: list[str] = Field(default_factory=lambda: ["gmx", "dydx"])


class AirdropSettings(BaseSettings):
    check_interval_hours: int = 24
    max_claims_per_day: int = 5


class CelerySettings(BaseSettings):
    broker_url: str = Field(default="redis://localhost:6379/0", validation_alias="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/1", validation_alias="CELERY_RESULT_BACKEND")


class SentrySettings(BaseSettings):
    dsn: str = Field(default="", validation_alias="SENTRY_DSN")
    environment: str = "development"


class Settings(BaseSettings):
    app_name: str = "Telegram Crypto Platform"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    payment: PaymentSettings = Field(default_factory=PaymentSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    airdrop: AirdropSettings = Field(default_factory=AirdropSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    sentry: SentrySettings = Field(default_factory=SentrySettings)

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache
def get_settings() -> Settings:
    return Settings()
