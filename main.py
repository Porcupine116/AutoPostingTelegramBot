from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.handlers import (
    autopost_router,
    cta_router,
    generate_router,
    menu_router,
    reels_router,
    rewrite_router,
    script_router,
    settings_router,
    start_router,
    titles_router,
)
from bot.handlers.autopost import set_autopost_manager
from config.settings import get_settings
from services.ai_service import AIService
from services.autoposting import AutopostContext, AutoPostManager
from services.history_service import HistoryService
from services.prompt_service import PromptService
from services.scheduled_posts_service import ScheduledPostService
from utils.logger import setup_logging


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(generate_router)
    dp.include_router(rewrite_router)
    dp.include_router(titles_router)
    dp.include_router(cta_router)
    dp.include_router(reels_router)
    dp.include_router(script_router)
    dp.include_router(settings_router)
    dp.include_router(autopost_router)

    history_service = HistoryService(settings.database_path)
    scheduled_posts = ScheduledPostService(settings.database_path)
    autopost_manager = AutoPostManager(
        AutoPostContext(
            bot=bot,
            ai_service=AIService(),
            prompt_service=PromptService(),
            history_service=history_service,
            scheduled_posts=scheduled_posts,
        )
    )
    set_autopost_manager(autopost_manager)

    scheduler_task = autopost_manager.start()
    try:
        await dp.start_polling(bot)
    finally:
        await autopost_manager.stop()
        if scheduler_task and not scheduler_task.done():
            scheduler_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
