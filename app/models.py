from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Учителя
class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    tg_user_id: Mapped[int] = mapped_column(
        Integer, 
        unique=True, 
        index=True
    )
    display_name: Mapped[str] = mapped_column(String(255))

    disciplines: Mapped[list["Discipline"]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    students: Mapped[list["Student"]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan",
    )


# Дисциплины
class Discipline(Base):
    __tablename__ = "disciplines"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", 
            "name", 
            name="uq_teacher_discipline_name"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), 
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)

    teacher: Mapped["Teacher"] = relationship(back_populates="disciplines")
    sessions: Mapped[list["LectureSession"]] = relationship(
        back_populates="discipline",
        cascade="all, delete-orphan",
    )


# Студенты
class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", 
            "full_name", 
            name="uq_teacher_student_name"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), 
        index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), index=True)

    teacher: Mapped["Teacher"] = relationship(back_populates="students")
    attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )


# Пары
class LectureSession(Base):
    __tablename__ = "lecture_sessions"
    __table_args__ = (
        UniqueConstraint(
            "discipline_id", 
            "session_date", 
            name="uq_discipline_date"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id", ondelete="CASCADE"), 
        index=True
    )
    session_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now()
    )

    discipline: Mapped["Discipline"]= relationship(back_populates="sessions")
    attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


# Посещения
class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "session_id", 
            "student_id", 
            name="uq_session_student"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), 
        index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), 
        index=True
    )

    session: Mapped["LectureSession"] = relationship(back_populates="attendance")
    student: Mapped["Student"] = relationship(back_populates="attendance")