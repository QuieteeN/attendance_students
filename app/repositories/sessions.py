from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Discipline, LectureSession


class SessionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, session_id: int):
        return await self.session.get(LectureSession, session_id)

    async def create_if_not_exists(self, discipline_id: int, d: date):
        res = await self.session.execute(
            select(LectureSession).where(
                LectureSession.discipline_id == discipline_id,
                LectureSession.session_date == d,
            )
        )
        s = res.scalar_one_or_none()
        if s:
            return s
        s = LectureSession(discipline_id=discipline_id, session_date=d)
        self.session.add(s)
        await self.session.flush()
        return s

    async def list_by_discipline(self, discipline_id: int):
        res = await self.session.execute(
            select(LectureSession)
            .where(LectureSession.discipline_id == discipline_id)
            .order_by(LectureSession.session_date.asc())
        )
        return list(res.scalars().all())

    async def discipline_belongs_to_teacher(self, discipline_id: int, teacher_id: int):
        res = await self.session.execute(
            select(Discipline.id)
            .where(
                Discipline.id == discipline_id, 
                Discipline.teacher_id == teacher_id
            )
        )
        return res.first() is not None