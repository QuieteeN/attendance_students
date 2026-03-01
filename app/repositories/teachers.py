from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Teacher


class TeacherRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tg_user_id(self, tg_user_id: int):
        res = await self.session.execute(select(Teacher)
                        .where(Teacher.tg_user_id == tg_user_id))
        return res.scalar_one_or_none()

    async def ensure_teacher(self, tg_user_id: int, display_name: str):
        t = await self.get_by_tg_user_id(tg_user_id)
        if t:
            t.display_name = display_name
            await self.session.flush()
            return t
        t = Teacher(tg_user_id=tg_user_id, display_name=display_name)
        self.session.add(t)
        await self.session.flush()
        return t