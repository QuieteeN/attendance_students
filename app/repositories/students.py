from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Student


class StudentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_teacher(self, teacher_id: int):
        res = await self.session.execute(
            select(Student)
            .where(Student.teacher_id == teacher_id)
            .order_by(Student.full_name.asc())
        )
        return list(res.scalars().all())

    async def get(self, student_id: int):
        return await self.session.get(Student, student_id)

    async def get_by_full_name(self, teacher_id: int, full_name: str):
        res = await self.session.execute(
            select(Student)
            .where(
                Student.teacher_id == teacher_id, 
                Student.full_name == full_name
            )
        )
        return res.scalar_one_or_none()

    async def bulk_create_if_not_exists(self, teacher_id: int, full_names: list[str]):
        created, skipped = 0, 0
        for name in full_names:
            name = name.strip()
            if not name:
                continue
            existing = await self.get_by_full_name(teacher_id, name)
            if existing:
                skipped += 1
                continue
            self.session.add(
                Student(teacher_id=teacher_id, full_name=name)
            )
            created += 1
        await self.session.flush()
        return created, skipped