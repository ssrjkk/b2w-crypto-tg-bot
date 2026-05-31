"""Telegram bot keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard"),
        InlineKeyboardButton(text="💳 Subscribe", callback_data="subscribe"),
    )
    builder.add(
        InlineKeyboardButton(text="📈 Trade", callback_data="trade"),
        InlineKeyboardButton(text="🎁 Airdrops", callback_data="airdrops"),
    )
    builder.add(
        InlineKeyboardButton(text="⚙️ Settings", callback_data="settings"),
    )
    return builder.as_markup()


def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    """Subscription options keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="ETH", callback_data="subscribe_ETH"),
        InlineKeyboardButton(text="USDT", callback_data="subscribe_USDT"),
    )
    builder.add(
        InlineKeyboardButton(text="↩️ Back", callback_data="back_main"),
    )
    return builder.as_markup()


def get_network_keyboard() -> InlineKeyboardMarkup:
    """Network selection keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Arbitrum", callback_data="network_arbitrum"),
        InlineKeyboardButton(text="Optimism", callback_data="network_optimism"),
    )
    builder.add(
        InlineKeyboardButton(text="↩️ Back", callback_data="back_main"),
    )
    return builder.as_markup()


def get_trade_keyboard() -> InlineKeyboardMarkup:
    """Trade action keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔄 Swap", callback_data="trade_swap"),
        InlineKeyboardButton(text="📊 Position", callback_data="trade_position"),
    )
    builder.add(
        InlineKeyboardButton(text="↩️ Back", callback_data="back_main"),
    )
    return builder.as_markup()


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm_{action}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_{action}"),
    )
    return builder.as_markup()


def get_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Dashboard navigation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📋 History", callback_data="dash_history"),
        InlineKeyboardButton(text="📊 Summary", callback_data="dash_summary"),
    )
    builder.add(
        InlineKeyboardButton(text="↩️ Back", callback_data="back_main"),
    )
    return builder.as_markup()


def get_airdrop_keyboard() -> InlineKeyboardMarkup:
    """Airdrop list keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Check Eligibility", callback_data="airdrop_check"),
        InlineKeyboardButton(text="My Progress", callback_data="airdrop_progress"),
    )
    builder.add(
        InlineKeyboardButton(text="↩️ Back", callback_data="back_main"),
    )
    return builder.as_markup()
