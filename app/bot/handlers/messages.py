"""Telegram bot message handlers."""

import logging
from datetime import datetime

from aiogram.types import Message

from app.bot.keyboards import (
    get_airdrop_keyboard,
    get_dashboard_keyboard,
    get_main_keyboard,
    get_network_keyboard,
    get_subscribe_keyboard,
    get_trade_keyboard,
)
from app.core.enums import ActionStatus, ActionType, RiskDecision
from app.models.dashboard import EventCreate

logger = logging.getLogger(__name__)


async def handle_dashboard(message: Message) -> None:
    """Handle dashboard view."""
    try:
        from app.main import get_services
        dashboard_service = get_services()["dashboard"]

        user_id = message.from_user.id
        summary = await dashboard_service.get_summary(user_id)

        text = (
            f"📊 *Dashboard Summary*\n\n"
            f"*Total Actions:* {summary.total_actions}\n"
            f"✅ *Completed:* {summary.completed_actions}\n"
            f"❌ *Failed:* {summary.failed_actions}\n"
            f"🛑 *Blocked:* {summary.blocked_actions}\n\n"
        )

        if summary.recent_events:
            text += "*Recent Activity:*\n"
            for event in summary.recent_events[:5]:
                text += f"• {event.action_type.value}: {event.status.value} ({event.created_at.strftime('%H:%M')})\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=get_dashboard_keyboard())
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        await message.answer("Error loading dashboard. Please try again.")


async def handle_subscribe(message: Message) -> None:
    """Handle subscription menu."""
    try:
        from app.main import get_services
        subscription_service = get_services()["subscription"]
        user_id = message.from_user.id

        has_access = await subscription_service.check_access(user_id)

        if has_access:
            sub = await subscription_service.get_user_subscription(user_id)
            text = (
                f"🎉 *Subscription Active*\n\n"
                f"Status: {sub.status.value}\n"
                f"Expires: {sub.expiry_date.strftime('%Y-%m-%d') if sub.expiry_date else 'N/A'}\n"
                f"Days remaining: {sub.days_remaining}"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            text = "💳 *Subscribe to Premium*\n\n"
            text += "Choose your payment token:\n"
            await message.answer(text, parse_mode="Markdown", reply_markup=get_subscribe_keyboard())
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        await message.answer("Error loading subscription. Please try again.")


async def handle_trade_menu(message: Message) -> None:
    """Handle trade menu."""
    try:
        from app.main import get_services
        subscription_service = get_services()["subscription"]
        user_id = message.from_user.id

        has_access = await subscription_service.check_access(user_id)

        if not has_access:
            await message.answer(
                "❌ Subscription required for trading.\nUse /subscribe to get started.",
                reply_markup=get_main_keyboard(),
            )
            return

        text = "📈 *Trading Menu*\n\n"
        text += "Select an action:"
        await message.answer(text, parse_mode="Markdown", reply_markup=get_trade_keyboard())
    except Exception as e:
        logger.error(f"Trade menu error: {e}")
        await message.answer("Error loading trade menu. Please try again.")


async def handle_airdrops_menu(message: Message) -> None:
    """Handle airdrops menu."""
    try:
        from app.main import get_services
        airdrop_engine = get_services()["airdrop"]
        user_id = message.from_user.id

        campaigns = await airdrop_engine.get_user_campaigns(user_id)

        if not campaigns:
            await message.answer(
                "🎁 *Airdrops*\n\nNo active campaigns at the moment.",
                parse_mode="Markdown",
            )
            return

        text = "🎁 *Airdrop Campaigns*\n\n"
        for item in campaigns[:5]:
            campaign = item["campaign"]
            progress = item.get("progress")
            status_emoji = "🟢" if progress and progress.status.value == "eligible" else "⚪"
            text += f"{status_emoji} *{campaign.name}*\n"
            text += f"   {campaign.protocol}\n\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=get_airdrop_keyboard())
    except Exception as e:
        logger.error(f"Airdrops error: {e}")
        await message.answer("Error loading airdrops. Please try again.")


async def handle_payment_confirm(message: Message) -> None:
    """Handle payment confirmation."""
    try:
        from app.main import get_services
        from app.payments.invoice import PaymentService

        payment_service = get_services()["payment"]
        subscription_service = get_services()["subscription"]
        dashboard_service = get_services()["dashboard"]
        alerting_service = get_services()["alerting"]

        user_id = message.from_user.id

        payment = await payment_service.check_payment_status(user_id)
        if not payment:
            await message.answer("No pending payment found.")
            return

        if payment.status.value == "paid" or payment.status.value == "confirmed":
            sub = await subscription_service.get_user_subscription(user_id)
            if sub:
                text = f"✅ Payment confirmed!\n\nYour subscription expires: {sub.expiry_date.strftime('%Y-%m-%d')}"
                await message.answer(text)

                if alerting_service:
                    await alerting_service.notify_subscription_activated(
                        message.chat.id,
                        sub.expiry_date.strftime('%Y-%m-%d'),
                    )
            else:
                await message.answer("Payment confirmed! Activating subscription...")
        else:
            await message.answer(f"Payment status: {payment.status.value}")

    except Exception as e:
        logger.error(f"Payment confirm error: {e}")
        await message.answer("Error processing payment. Please try again.")
