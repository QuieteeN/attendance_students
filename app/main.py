from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import load_config
from app.db import init_db, make_engine, make_sessionmaker
from app.handlers import get_root_router
from app.middlewares import DbSessionMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    cfg = load_config()
    engine = make_engine(cfg)
    sessionmaker = make_sessionmaker(engine)
    await init_db(engine)

    bot = Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp["config"] = cfg

    dp.update.middleware(DbSessionMiddleware(sessionmaker))
    dp.include_router(get_root_router())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())