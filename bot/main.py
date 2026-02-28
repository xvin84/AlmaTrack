"""
AlmaTrack bot entry point.

Run with:
    uv run python bot/main.py
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from bot.config import get_settings
from bot.handlers import all_routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    cfg = get_settings()

    # --- Storage ---
    # RedisStorage is used for FSM persistence across restarts.
    # Fallback: use MemoryStorage() if Redis is unavailable (dev only).
    try:
        storage = RedisStorage.from_url(cfg.redis_url)
        logger.info("FSM storage: Redis (%s)", cfg.redis_url)
    except Exception as exc:
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        logger.warning("Redis unavailable (%s), falling back to MemoryStorage", exc)

    # --- Bot & Dispatcher ---
    bot = Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # --- Register middlewares ---
    from bot.middlewares.auth import PendingUserMiddleware
    pending_mw = PendingUserMiddleware()
    dp.message.middleware(pending_mw)
    dp.callback_query.middleware(pending_mw)

    # --- Register routers ---
    for router in all_routers:
        dp.include_router(router)

    # --- DB init ---
    # initialise database on startup
    from db.base import init_db
    await init_db()

    # --- Setup Bot Commands ---
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="🏠 Главное меню / Регистрация"),
        BotCommand(command="stats", description="📊 Статистика факультета"),
        BotCommand(command="help", description="❓ Помощь"),
    ]
    await bot.set_my_commands(commands)

    logger.info("Starting AlmaTrack bot…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())


def run() -> None:
    """Sync entry point for pyproject.toml scripts."""
    asyncio.run(main())
