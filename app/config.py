from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """ Config """
    bot_token: str
    database_url: str


def load_config() -> Config:
    """ Load Config """
    load_dotenv()
    token = getenv("BOT_TOKEN", "").strip()
    db_url = getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./attendance.sqlite3"
    ).strip()

    if not token:
        raise RuntimeError("BOT_TOKEN is empty. Put it into .env")

    return Config(bot_token=token, database_url=db_url)