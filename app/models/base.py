"""SQLAlchemy base and models with optimized indexes."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

from app.core.enums import (
    SubscriptionStatus,
    PaymentStatus,
    Network,
    ActionType,
    ActionStatus,
    AirdropStatus,
    RiskDecision,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index('ix_users_telegram_id', 'telegram_id'),
        Index('ix_users_username', 'username'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    wallet_address = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index('ix_subscriptions_user_id', 'user_id'),
        Index('ix_subscriptions_status', 'status'),
        Index('ix_subscriptions_expiry', 'expiry_date'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    plan_name = Column(String(50), default="premium")
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE)
    start_date = Column(DateTime)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index('ix_payments_user_id', 'user_id'),
        Index('ix_payments_status', 'status'),
        Index('ix_payments_expires', 'expires_at'),
        Index('ix_payments_tx_hash', 'transaction_hash'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(String(50), nullable=False)
    token = Column(String(20), nullable=False)
    network = Column(SQLEnum(Network), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    invoice_address = Column(String(200))
    transaction_hash = Column(String(200))
    confirmations = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TradeModel(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index('ix_trades_user_id', 'user_id'),
        Index('ix_trades_status', 'status'),
        Index('ix_trades_created', 'created_at'),
        Index('ix_trades_dex_network', 'dex', 'network'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    dex = Column(String(20), nullable=False)
    network = Column(String(20), nullable=False)
    from_token = Column(String(20), nullable=False)
    to_token = Column(String(20), nullable=False)
    amount = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(10), default="market")
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.QUEUED)
    risk_decision = Column(String(50))
    transaction_hash = Column(String(200))
    executed_price = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)


class ActionQueueModel(Base):
    __tablename__ = "action_queue"
    __table_args__ = (
        Index('ix_action_queue_user_id', 'user_id'),
        Index('ix_action_queue_status', 'status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.QUEUED)
    payload = Column(JSON)
    risk_decision = Column(String(50))
    result = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AirdropCampaignModel(Base):
    __tablename__ = "airdrop_campaigns"
    __table_args__ = (
        Index('ix_airdrop_campaigns_status', 'status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    protocol = Column(String(50), nullable=False)
    description = Column(Text)
    eligibility_rules = Column(JSON)
    status = Column(SQLEnum(AirdropStatus), default=AirdropStatus.NOT_ELIGIBLE)
    estimated_amount = Column(String(50))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())


class AirdropProgressModel(Base):
    __tablename__ = "airdrop_progress"
    __table_args__ = (
        Index('ix_airdrop_progress_user_campaign', 'user_id', 'campaign_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    campaign_id = Column(Integer, nullable=False)
    status = Column(SQLEnum(AirdropStatus), default=AirdropStatus.NOT_ELIGIBLE)
    progress_percent = Column(Float, default=0.0)
    tasks_completed = Column(Integer, default=0)
    tasks_total = Column(Integer, default=0)
    last_checked_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class DashboardEventModel(Base):
    __tablename__ = "dashboard_events"
    __table_args__ = (
        Index('ix_dashboard_events_user_id', 'user_id'),
        Index('ix_dashboard_events_created', 'created_at'),
        Index('ix_dashboard_events_action_status', 'action_type', 'status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    status = Column(SQLEnum(ActionStatus), nullable=False)
    risk_decision = Column(String(50))
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    result = Column(JSON)
    event_metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())


class RiskLimitModel(Base):
    __tablename__ = "risk_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    value = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())