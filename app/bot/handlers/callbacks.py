"""Telegram bot callback handlers."""

import logging

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from app.bot.keyboards import (
    get_airdrop_keyboard,
    get_confirm_keyboard,
    get_dashboard_keyboard,
    get_main_keyboard,
    get_network_keyboard,
    get_subscribe_keyboard,
    get_trade_keyboard,
)

logger = logging.getLogger(__name__)


async def cb_dashboard(callback: CallbackQuery) -> None:
    """Handle dashboard callback."""
    from app.bot.handlers.messages import handle_dashboard
    await callback.message.answer("Loading dashboard...")
    await handle_dashboard(callback.message)
    await callback.answer()


async def cb_subscribe(callback: CallbackQuery) -> None:
    """Handle subscribe callback."""
    from app.bot.handlers.messages import handle_subscribe
    await handle_subscribe(callback.message)
    await callback.answer()


async def cb_trade(callback: CallbackQuery) -> None:
    """Handle trade callback."""
    from app.bot.handlers.messages import handle_trade_menu
    await handle_trade_menu(callback.message)
    await callback.answer()


async def cb_airdrops(callback: CallbackQuery) -> None:
    """Handle airdrops callback."""
    from app.bot.handlers.messages import handle_airdrops_menu
    await handle_airdrops_menu(callback.message)
    await callback.answer()


async def cb_settings(callback: CallbackQuery) -> None:
    """Handle settings callback."""
    text = "⚙️ *Settings*\n\n"
    text += "Network: Arbitrum\n"
    text += "Max slippage: 2%\n"
    text += "Notifications: Enabled"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


async def cb_back_main(callback: CallbackQuery) -> None:
    """Handle back to main menu."""
    text = "👋 Back to main menu"
    await callback.message.answer(text, reply_markup=get_main_keyboard())
    await callback.answer()


async def cb_subscribe_token(callback: CallbackQuery) -> None:
    """Handle token selection for subscription."""
    token = callback.data.replace("subscribe_", "")
    try:
        from app.main import get_services
        from app.payments.invoice import PaymentService

        payment_service = get_services()["payment"]
        user_id = callback.from_user.id

        invoice = await payment_service.create_invoice(
            user_id=user_id,
            amount="0.01",
            token=token,
            network="arbitrum",
        )

        text = f"💳 *Payment Invoice*\n\n"
        text += f"Amount: {invoice.amount} {invoice.token}\n"
        text += f"Network: {invoice.network.value}\n"
        text += f"Address: `{invoice.address}`\n\n"
        text += f"Expires: {invoice.expires_at.strftime('%H:%M')}\n\n"
        text += "Please send the exact amount to the address above."

        await callback.message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Subscribe token error: {e}")
        await callback.message.answer("Error creating invoice. Please try again.")

    await callback.answer()


async def cb_confirm_action(callback: CallbackQuery) -> None:
    """Handle action confirmation."""
    action = callback.data.replace("confirm_", "")
    text = f"✅ Action confirmed: {action}"
    await callback.message.answer(text)
    await callback.answer()


async def cb_cancel_action(callback: CallbackQuery) -> None:
    """Handle action cancellation."""
    action = callback.data.replace("cancel_", "")
    text = f"❌ Action cancelled: {action}"
    await callback.message.answer(text)
    await callback.answer()


async def cb_network_select(callback: CallbackQuery) -> None:
    """Handle network selection."""
    network = callback.data.replace("network_", "")
    text = f"🌐 Network selected: {network}"
    await callback.message.answer(text)
    await callback.answer()


def register_callbacks(dp: Dispatcher) -> None:
    """Register all callback handlers."""
    dp.callback_query.register(cb_dashboard, lambda c: c.data == "dashboard")
    dp.callback_query.register(cb_subscribe, lambda c: c.data == "subscribe")
    dp.callback_query.register(cb_trade, lambda c: c.data == "trade")
    dp.callback_query.register(cb_airdrops, lambda c: c.data == "airdrops")
    dp.callback_query.register(cb_settings, lambda c: c.data == "settings")
    dp.callback_query.register(cb_back_main, lambda c: c.data == "back_main")
    dp.callback_query.register(cb_subscribe_token, lambda c: c.data.startswith("subscribe_"))
    dp.callback_query.register(cb_confirm_action, lambda c: c.data.startswith("confirm_"))
    dp.callback_query.register(cb_cancel_action, lambda c: c.data.startswith("cancel_"))
    dp.callback_query.register(cb_network_select, lambda c: c.data.startswith("network_"))
    logger.info("Callback handlers registered")
