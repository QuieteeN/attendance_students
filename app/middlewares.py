from aiogram import BaseMiddleware


class DbSessionMiddleware(BaseMiddleware):
    """
    - На КАЖДЫЙ апдейт создаём DB сессию.
    - Кладём её в data["db"].
    - Хендлер выполняется.
    - Потом commit().

    В итоге: не надо открывать БД вручную в каждом обработчике.
    """
    def __init__(self, sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler,
        event,
        data,
    ):
        async with self.sessionmaker() as session:
            data["db"] = session
            result = await handler(event, data)
            await session.commit()
            return result