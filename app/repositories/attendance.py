from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attendance, Discipline, LectureSession, Student


class AttendanceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_present(self, session_id: int, student_id: int):
        res = await self.session.execute(
            select(Attendance.id)
            .where(
                Attendance.session_id == session_id, 
                Attendance.student_id == student_id
            )
        )
        return res.first() is not None

    async def set_present(self, session_id: int, student_id: int, present: bool):
        if present:
            exists = await self.is_present(session_id, student_id)
            if not exists:
                self.session.add(
                    Attendance(
                        session_id=session_id, 
                        student_id=student_id
                    )
                )
                await self.session.flush()
        else:
            await self.session.execute(
                delete(Attendance)
                .where(
                    Attendance.session_id == session_id, 
                    Attendance.student_id == student_id
                )
            )

    async def list_present_student_ids(self, session_id: int):
        res = await self.session.execute(
            select(Attendance.student_id)
            .where(Attendance.session_id == session_id)
        )
        return set(res.scalars().all())

    async def stats_for_discipline(self, teacher_id: int, discipline_id: int):
        ok = await self.session.execute(
            select(Discipline.id)
            .where(
                Discipline.id == discipline_id, 
                Discipline.teacher_id == teacher_id
            )
        )
        if ok.first() is None:
            return {
                "total_sessions": 0, 
                "total_students": 0, 
                "per_student": [], 
                "avg_percent": 0.0, 
                "by_date": []
            }

        total_students = await self.session.scalar(
            select(func.count(Student.id))
            .where(Student.teacher_id == teacher_id)
        )
        total_students = int(total_students or 0)

        total_sessions = await self.session.scalar(
            select(func.count(LectureSession.id))
            .where(LectureSession.discipline_id == discipline_id)
        )
        total_sessions = int(total_sessions or 0)

        res = await self.session.execute(
            select(
                Student.id,
                Student.full_name,
                func.count(Attendance.id).label("present_count"),
            )
            .select_from(Student)
            .join(
                Attendance, 
                Attendance.student_id == Student.id, 
                isouter=True
            )
            .join(
                LectureSession, 
                LectureSession.id == Attendance.session_id, 
                isouter=True
            )
            .where(Student.teacher_id == teacher_id)
            .where(
                (LectureSession.discipline_id == discipline_id) | 
                (LectureSession.discipline_id.is_(None))
            )
            .group_by(Student.id)
            .order_by(Student.full_name.asc())
        )
        rows = res.all()

        per_student = []
        total_percent_sum = 0.0
        for sid, full_name, present_cnt in rows:
            present_cnt = int(present_cnt or 0)
            percent = (present_cnt / total_sessions * 100.0) if total_sessions > 0 else 0.0
            total_percent_sum += percent
            per_student.append(
                {
                    "student_id": int(sid), 
                    "full_name": str(full_name), 
                    "present": present_cnt, 
                    "percent": percent
                }
            )

        avg_percent = (total_percent_sum / len(per_student)) if per_student else 0.0

        res2 = await self.session.execute(
            select(
                LectureSession.session_date,
                func.count(Attendance.id).label("present_count"),
            )
            .select_from(LectureSession)
            .join(
                Attendance, 
                Attendance.session_id == LectureSession.id, isouter=True
            )
            .where(LectureSession.discipline_id == discipline_id)
            .group_by(LectureSession.session_date)
            .order_by(LectureSession.session_date.asc())
        )
        by_date = []
        for d, present_count in res2.all():
            by_date.append({
                "date": d, 
                "present_count": int(present_count or 0), 
                "total_students": total_students
            })

        return {
            "total_sessions": total_sessions,
            "total_students": total_students,
            "per_student": per_student,
            "avg_percent": avg_percent,
            "by_date": by_date,
        }
    
    async def stats_for_discipline2(self, teacher_id: int, discipline_id: int):
        ok = await self.session.execute(
            select(Discipline.id)
            .where(
                Discipline.id == discipline_id, 
                Discipline.teacher_id == teacher_id
            )
        )
        if ok.first() is None:
            return {
                "discipline_attendance": {}
            }
        
        sessions = await self.session.execute(
            select(LectureSession.session_date, Student.full_name)
            .select_from(LectureSession)
            .join(Attendance, Attendance.session_id == LectureSession.id)
            .join(Student, Student.id == Attendance.student_id)
            .where(LectureSession.discipline_id == discipline_id)
            .order_by(LectureSession.session_date.asc(), Student.full_name.asc())
        )

        discipline_attendance = {}
        for date, full_name in sessions.all():
            if date not in discipline_attendance:
                discipline_attendance[date] = []
            discipline_attendance[date].append(full_name)

        return {
            "discipline_attendance": discipline_attendance,
        }
