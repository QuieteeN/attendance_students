from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Discipline


class DisciplineRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_teacher(self, teacher_id: int):
        res = await self.session.execute(
            select(Discipline)
            .where(Discipline.teacher_id == teacher_id)
            .order_by(Discipline.name.asc())
        )
        return list(res.scalars().all())

    async def get(self, discipline_id: int):
        return await self.session.get(Discipline, discipline_id)

    async def get_by_name(self, teacher_id: int, name: str):
        res = await self.session.execute(
            select(Discipline)
            .where(
                Discipline.teacher_id == teacher_id, 
                Discipline.name == name
            )
        )
        return res.scalar_one_or_none()

    async def create_if_not_exists(self, teacher_id: int, name: str):
        d = await self.get_by_name(teacher_id, name)
        if d:
            return d
        d = Discipline(teacher_id=teacher_id, name=name)
        self.session.add(d)
        await self.session.flush()
        return d