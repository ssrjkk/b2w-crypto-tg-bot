"""Telegram bot application."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import callbacks, commands
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class BotApplication:
    """Telegram bot application."""

    def __init__(self):
        self.settings = get_settings()
        self.bot = None
        self.dp = None

    async def start(self) -> None:
        """Start the bot."""
        if not self.settings.telegram.bot_token:
            logger.warning("No bot token configured - bot will not start")
            return

        self.bot = Bot(token=self.settings.telegram.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())

        commands.register_commands(self.dp)
        callbacks.register_callbacks(self.dp)

        logger.info("Bot started successfully")

    async def stop(self) -> None:
        """Stop the bot."""
        if self.bot:
            await self.bot.session.close()
            logger.info("Bot stopped")

    def run(self) -> None:
        """Run the bot (blocking)."""
        if not self.bot:
            logger.warning("Bot not initialized")
            return

        import asyncio
        asyncio.run(self._run_polling())

    async def _run_polling(self) -> None:
        """Run bot polling."""
        if not self.dp or not self.bot:
            return

        logger.info("Starting bot polling...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
        finally:
            await self.stop()


async def create_bot() -> tuple[Bot, Dispatcher]:
    """Create and configure bot instance."""
    settings = get_settings()
    bot = Bot(token=settings.telegram.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    commands.register_commands(dp)
    callbacks.register_callbacks(dp)

    return bot, dp
