"""Airdrop engine - SQLAlchemy version."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.airdrop.rules import RulesEngine, RuleResult
from app.config.settings import get_settings
from app.core.enums import AirdropStatus
from app.models.base import AirdropCampaignModel, AirdropProgressModel
from app.models.airdrop import AirdropCampaign, AirdropProgress

logger = logging.getLogger(__name__)


class AirdropEngine:
    """Engine for managing airdrop campaigns and eligibility."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.rules_engine = RulesEngine()

    async def check_eligibility(
        self,
        user_id: int,
        campaign_id: int,
        user_data: dict,
    ) -> tuple[AirdropStatus, list[RuleResult]]:
        """Check user eligibility for a campaign."""
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            return AirdropStatus.NOT_ELIGIBLE, []

        eligibility_rules = campaign.eligibility_rules.get("rules", [])

        passed, results = await self.rules_engine.evaluate_rules(
            eligibility_rules, user_data
        )

        if passed:
            return AirdropStatus.ELIGIBLE, results
        return AirdropStatus.NOT_ELIGIBLE, results

    async def update_progress(
        self,
        user_id: int,
        campaign_id: int,
        status: AirdropStatus,
        progress_percent: float,
        tasks_completed: int,
        tasks_total: int,
    ) -> AirdropProgressModel:
        """Update user progress for a campaign."""
        progress = await self._get_progress(user_id, campaign_id)

        if progress:
            progress.status = status
            progress.progress_percent = progress_percent
            progress.tasks_completed = tasks_completed
            progress.tasks_total = tasks_total
            progress.last_checked_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(progress)
        else:
            progress = await self._create_progress(
                user_id, campaign_id, status, progress_percent, tasks_completed, tasks_total
            )

        return progress

    async def get_user_campaigns(
        self,
        user_id: int,
    ) -> list[dict]:
        """Get all campaigns for a user with progress."""
        campaigns = await self._get_all_campaigns()
        result = []

        for campaign in campaigns:
            progress = await self._get_progress(user_id, campaign.id)
            result.append({
                "campaign": campaign,
                "progress": progress,
            })

        return result

    async def get_campaign_tasks(
        self,
        campaign_id: int,
    ) -> list[dict]:
        """Get tasks for a campaign."""
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            return []

        tasks = campaign.eligibility_rules.get("tasks", [])
        return tasks

    async def _get_campaign(self, campaign_id: int) -> Optional[AirdropCampaignModel]:
        """Get campaign by ID."""
        result = await self.db.execute(
            select(AirdropCampaignModel).where(AirdropCampaignModel.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def _get_all_campaigns(self) -> list[AirdropCampaignModel]:
        """Get all campaigns."""
        result = await self.db.execute(select(AirdropCampaignModel))
        return list(result.scalars().all())

    async def _get_progress(
        self,
        user_id: int,
        campaign_id: int,
    ) -> Optional[AirdropProgressModel]:
        """Get user progress for a campaign."""
        result = await self.db.execute(
            select(AirdropProgressModel)
            .where(AirdropProgressModel.user_id == user_id)
            .where(AirdropProgressModel.campaign_id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def _create_progress(
        self,
        user_id: int,
        campaign_id: int,
        status: AirdropStatus,
        progress_percent: float,
        tasks_completed: int,
        tasks_total: int,
    ) -> AirdropProgressModel:
        """Create progress record."""
        progress = AirdropProgressModel(
            user_id=user_id,
            campaign_id=campaign_id,
            status=status,
            progress_percent=progress_percent,
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            last_checked_at=datetime.utcnow(),
        )
        self.db.add(progress)
        await self.db.commit()
        await self.db.refresh(progress)
        return progress
