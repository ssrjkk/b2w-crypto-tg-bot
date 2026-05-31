"""Background airdrop tasks."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_airdrop_progress(self) -> dict:
    """Update user progress for all airdrop campaigns."""
    from app.database.manager import get_db_manager
    from app.models.base import AirdropCampaignModel, AirdropProgressModel, AirdropStatus
    from sqlalchemy import select, update

    db = get_db_manager()

    try:
        async with db.session() as session:
            campaigns_result = await session.execute(
                select(AirdropCampaignModel)
            )
            campaigns = campaigns_result.scalars().all()

            updated_count = 0

            for campaign in campaigns:
                progress_result = await session.execute(
                    select(AirdropProgressModel).where(
                        AirdropProgressModel.campaign_id == campaign.id
                    )
                )
                progress_records = progress_result.scalars().all()

                for progress in progress_records:
                    if progress.status == AirdropStatus.CLAIMABLE:
                        progress.last_checked_at = datetime.utcnow()
                        updated_count += 1

            return {
                "campaigns_checked": len(campaigns),
                "progress_updated": updated_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error updating airdrop progress: {e}")
        self.retry(countdown=300)


@shared_task(bind=True)
def check_airdrop_eligibility(
    user_id: int,
    campaign_id: int,
    user_data: dict,
) -> dict:
    """Check eligibility for specific airdrop."""
    from app.airdrop.engine import AirdropEngine
    from app.database.manager import get_db_manager

    db = get_db_manager()

    try:
        engine = AirdropEngine(db)
        status, results = engine.check_eligibility(user_id, campaign_id, user_data)

        return {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "status": status.value,
            "results": [
                {"rule_id": r.rule_id, "passed": r.passed, "reason": r.reason}
                for r in results
            ],
        }
    except Exception as e:
        logger.error(f"Error checking eligibility: {e}")
        return {"error": str(e)}


@shared_task(bind=True)
def process_claim_transaction(
    user_id: int,
    campaign_id: int,
    tx_params: dict,
) -> dict:
    """Process airdrop claim transaction."""
    logger.info(f"Processing claim for user {user_id}, campaign {campaign_id}")

    return {
        "status": "pending",
        "user_id": user_id,
        "campaign_id": campaign_id,
    }
