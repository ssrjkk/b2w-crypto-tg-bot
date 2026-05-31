"""Celery configuration and background tasks."""

import logging
from typing import Optional

from celery import Celery
from celery.schedules import crontab

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "telegram_crypto_platform",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "app.tasks.payment_tasks",
        "app.tasks.airdrop_tasks",
        "app.tasks.risk_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=270,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

celery_app.conf.beat_schedule = {
    "check-expired-payments": {
        "task": "app.tasks.payment_tasks.check_expired_payments",
        "schedule": crontab(minute="*/5"),
    },
    "update-airdrop-progress": {
        "task": "app.tasks.airdrop_tasks.update_airdrop_progress",
        "schedule": crontab(hour="*/6"),
    },
    "check-risk-limits": {
        "task": "app.tasks.risk_tasks.check_daily_loss_limits",
        "schedule": crontab(hour="*"),
    },
    "cleanup-old-events": {
        "task": "app.tasks.dashboard_tasks.cleanup_old_events",
        "schedule": crontab(hour=2, minute=0),
    },
}
