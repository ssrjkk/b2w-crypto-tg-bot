"""Trading models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import ActionStatus, ActionType, DexName, Network, OrderSide, OrderType, RiskDecision


class QuoteRequest(BaseModel):
    user_id: int
    dex: DexName
    network: Network
    from_token: str
    to_token: str
    amount: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET


class Quote(BaseModel):
    request: QuoteRequest
    price: str
    price_impact: float
    estimated_gas: str
    slippage_actual: Optional[float] = None
    valid_until: datetime


class TradeRequest(BaseModel):
    user_id: int
    dex: DexName
    network: Network
    from_token: str
    to_token: str
    amount: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    max_slippage: float = 2.0


class Trade(BaseModel):
    id: int
    user_id: int
    quote_request: QuoteRequest
    status: ActionStatus = ActionStatus.QUEUED
    risk_decision: Optional[RiskDecision] = None
    transaction_hash: Optional[str] = None
    executed_price: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Position(BaseModel):
    id: int
    user_id: int
    dex: DexName
    network: Network
    token: str
    size: str
    entry_price: str
    current_price: Optional[str] = None
    pnl: Optional[str] = None
    is_long: bool = True
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
