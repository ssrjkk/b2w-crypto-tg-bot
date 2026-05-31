"""Airdrop API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.manager import get_db_session

router = APIRouter(prefix="/airdrop", tags=["airdrop"])


class EligibilityCheckRequest(BaseModel):
    user_id: int
    campaign_id: int
    total_volume: float = 0
    total_trades: int = 0
    activity_arbitrum: int = 0
    activity_optimism: int = 0
    holding_days_eth: int = 0


@router.post("/check-eligibility")
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Check user eligibility for a campaign."""
    from app.airdrop.engine import AirdropEngine

    engine = AirdropEngine(db)

    user_data = {
        "total_volume": request.total_volume,
        "total_trades": request.total_trades,
        "activity_arbitrum": request.activity_arbitrum,
        "activity_optimism": request.activity_optimism,
        "holding_days_eth": request.holding_days_eth,
    }

    try:
        status, results = await engine.check_eligibility(
            request.user_id,
            request.campaign_id,
            user_data,
        )
        return {
            "status": status.value,
            "results": [
                {
                    "rule_id": r.rule_id,
                    "passed": r.passed,
                    "reason": r.reason,
                }
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns/{user_id}")
async def get_user_campaigns(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get all campaigns for a user."""
    from app.airdrop.engine import AirdropEngine

    engine = AirdropEngine(db)

    try:
        campaigns = await engine.get_user_campaigns(user_id)
        return {
            "campaigns": [
                {
                    "id": c["campaign"].id,
                    "name": c["campaign"].name,
                    "protocol": c["campaign"].protocol,
                    "status": c["campaign"].status.value,
                    "progress": {
                        "status": c["progress"].status.value if c.get("progress") else None,
                        "percent": c["progress"].progress_percent if c.get("progress") else 0,
                    }
                    if c.get("progress") else None,
                }
                for c in campaigns
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{campaign_id}")
async def get_campaign_tasks(
    campaign_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get tasks for a campaign."""
    from app.airdrop.engine import AirdropEngine

    engine = AirdropEngine(db)

    try:
        tasks = await engine.get_campaign_tasks(campaign_id)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
