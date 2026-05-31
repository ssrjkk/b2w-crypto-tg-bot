"""Trading API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.manager import get_db_session
from app.core.enums import DexName, Network, OrderSide, OrderType

router = APIRouter(prefix="/trading", tags=["trading"])


class QuoteRequestDTO(BaseModel):
    user_id: int
    dex: DexName
    network: Network
    from_token: str
    to_token: str
    amount: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET


class TradeRequestDTO(BaseModel):
    user_id: int
    dex: DexName
    network: Network
    from_token: str
    to_token: str
    amount: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    max_slippage: float = 2.0


@router.post("/quote")
async def get_quote(
    request: QuoteRequestDTO,
    db: AsyncSession = Depends(get_db_session),
):
    """Get quote for a trade."""
    from app.trading.orchestrator import TradingOrchestrator
    from app.services.risk_service import RiskService

    risk_service = RiskService(db)
    orchestrator = TradingOrchestrator(db, risk_service)

    try:
        from app.models.trading import QuoteRequest
        quote = await orchestrator.get_quote(
            QuoteRequest(
                user_id=request.user_id,
                dex=request.dex,
                network=request.network,
                from_token=request.from_token,
                to_token=request.to_token,
                amount=request.amount,
                side=request.side,
                order_type=request.order_type,
            )
        )
        return {
            "price": quote.price,
            "price_impact": quote.price_impact,
            "estimated_gas": quote.estimated_gas,
            "slippage_actual": quote.slippage_actual,
            "valid_until": quote.valid_until.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute")
async def execute_trade(
    request: TradeRequestDTO,
    db: AsyncSession = Depends(get_db_session),
):
    """Execute a trade."""
    from app.trading.orchestrator import TradingOrchestrator
    from app.services.risk_service import RiskService

    risk_service = RiskService(db)
    orchestrator = TradingOrchestrator(db, risk_service)

    try:
        from app.models.trading import TradeRequest
        result = await orchestrator.execute_trade(
            TradeRequest(
                user_id=request.user_id,
                dex=request.dex,
                network=request.network,
                from_token=request.from_token,
                to_token=request.to_token,
                amount=request.amount,
                side=request.side,
                order_type=request.order_type,
                max_slippage=request.max_slippage,
            )
        )
        return {
            "success": result.success,
            "trade_id": result.trade_id,
            "transaction_hash": result.transaction_hash,
            "executed_price": result.executed_price,
            "error": result.error,
            "risk_decision": result.risk_decision.value if result.risk_decision else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{user_id}")
async def get_trade_history(
    user_id: int,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """Get trade history for user."""
    from app.trading.orchestrator import TradingOrchestrator
    from app.services.risk_service import RiskService

    risk_service = RiskService(db)
    orchestrator = TradingOrchestrator(db, risk_service)

    try:
        trades = await orchestrator.get_trade_history(user_id, limit)
        return {
            "trades": [
                {
                    "id": t.id,
                    "dex": t.dex,
                    "network": t.network,
                    "from_token": t.from_token,
                    "to_token": t.to_token,
                    "amount": t.amount,
                    "side": t.side,
                    "status": t.status.value if t.status else None,
                    "executed_price": t.executed_price,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in trades
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
