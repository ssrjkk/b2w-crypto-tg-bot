"""Telegram bot command handlers."""

import logging

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)


async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    welcome_text = (
        "👋 Welcome to Crypto Platform!\n\n"
        "Your gateway to crypto trading and airdrops.\n\n"
        "Use the menu below or commands to navigate:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = (
        "📖 *Available Commands:*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/dashboard - View your activity\n"
        "/subscribe - Subscribe to premium\n"
        "/trade - Open trading menu\n"
        "/airdrops - View airdrop campaigns\n"
        "/settings - Bot settings\n\n"
        "All actions are user-initiated and audited."
    )
    await message.answer(help_text, parse_mode="Markdown")


async def cmd_dashboard(message: Message) -> None:
    """Handle /dashboard command."""
    from app.bot.handlers.messages import handle_dashboard
    await handle_dashboard(message)


async def cmd_subscribe(message: Message) -> None:
    """Handle /subscribe command."""
    from app.bot.handlers.messages import handle_subscribe
    await handle_subscribe(message)


async def cmd_trade(message: Message) -> None:
    """Handle /trade command."""
    from app.bot.handlers.messages import handle_trade_menu
    await handle_trade_menu(message)


async def cmd_airdrops(message: Message) -> None:
    """Handle /airdrops command."""
    from app.bot.handlers.messages import handle_airdrops_menu
    await handle_airdrops_menu(message)


def register_commands(dp: Dispatcher) -> None:
    """Register all command handlers."""
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_help, Command(commands=["help"]))
    dp.message.register(cmd_dashboard, Command(commands=["dashboard"]))
    dp.message.register(cmd_subscribe, Command(commands=["subscribe"]))
    dp.message.register(cmd_trade, Command(commands=["trade"]))
    dp.message.register(cmd_airdrops, Command(commands=["airdrops"]))
    logger.info("Command handlers registered")
