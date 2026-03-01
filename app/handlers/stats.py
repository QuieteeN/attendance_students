from __future__ import annotations

from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import kb_disciplines, kb_stats_actions, kb_start_role, kb_main_menu
from app.repositories.attendance import AttendanceRepo
from app.repositories.disciplines import DisciplineRepo
from app.repositories.sessions import SessionRepo
from app.repositories.students import StudentRepo
from app.repositories.teachers import TeacherRepo
from app.services.charts import build_histogram_by_dates
from app.services.xlsx_export import export_discipline_xlsx

router = Router()
ST_DISC_PREFIX = "stats_disc"


async def get_teacher(db: AsyncSession, tg_user_id: int):
    return await TeacherRepo(db).get_by_tg_user_id(tg_user_id)


@router.callback_query(F.data == "menu:stats")
async def stats_start(call: CallbackQuery, db: AsyncSession, **_):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.message.edit_text(
            "Нужно зарегистрироваться:", 
            reply_markup=kb_start_role()
        )
        await call.answer()
        return

    disciplines = await DisciplineRepo(db).list_for_teacher(teacher.id)
    if not disciplines:
        await call.message.edit_text(
            "Нет дисциплин. Создайте их в ⚙️ Управление.",
            reply_markup=kb_main_menu(),
        )
        await call.answer()
        return

    items = [(d.id, d.name) for d in disciplines]
    await call.message.edit_text(
        "Выберите дисциплину для статистики:", 
        reply_markup=kb_disciplines(items, cb_prefix=ST_DISC_PREFIX)
    )
    await call.answer()


@router.callback_query(F.data.startswith(f"{ST_DISC_PREFIX}:pick:"))
async def stats_choose_discipline(
    call: CallbackQuery, 
    db: AsyncSession, 
    **_
):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    did = int(call.data.split(":")[-1])
    if not await SessionRepo(db).discipline_belongs_to_teacher(
        did, 
        teacher.id
    ):
        await call.answer("Нет доступа", show_alert=True)
        return

    d = await DisciplineRepo(db).get(did)
    await call.message.edit_text(
        f"📊 Статистика по дисциплине: {d.name}\nВыберите действие:",
        reply_markup=kb_stats_actions(did),
    )
    await call.answer()


@router.callback_query(F.data.startswith("stats:text:"))
async def stats_text(call: CallbackQuery, db: AsyncSession, **_):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    did = int(call.data.split(":")[-1])
    d = await DisciplineRepo(db).get(did)
    if not d:
        await call.answer("Не найдено", show_alert=True)
        return

    stats = await AttendanceRepo(db).stats_for_discipline(
        teacher.id, 
        did
    )
    total_sessions = stats["total_sessions"]
    avg = stats["avg_percent"]
    per_student = stats["per_student"]

    lines = [
        f"📊 <b>{d.name}</b>",
        f"Лекций: {total_sessions}",
        f"Средняя посещаемость (по людям): {avg:.1f}%",
        "",
        "По каждому (первые 20):",
    ]

    for row in per_student[:20]:
        lines.append(
            f"• {row['full_name']}: {row['present']}"
            f"/{total_sessions} ({row['percent']:.1f}%)"
        )
    if len(per_student) > 20:
        lines.append(f"... и ещё {len(per_student)-20}")

    await call.message.edit_text(
        "\n".join(lines), 
        reply_markup=kb_stats_actions(did)
    )
    await call.answer()


@router.callback_query(F.data.startswith("stats:hist:"))
async def stats_hist(call: CallbackQuery, db: AsyncSession, **_):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    did = int(call.data.split(":")[-1])
    d = await DisciplineRepo(db).get(did)
    if not d:
        await call.answer("Не найдено", show_alert=True)
        return

    stats = await AttendanceRepo(db).stats_for_discipline(
        teacher.id, 
        did
    )
    by_date = stats["by_date"]
    if not by_date:
        await call.answer(
            "Пока нет данных для гистограммы", 
            show_alert=True
        )
        return

    out = Path("out") / f"hist_{teacher.tg_user_id}_{did}.png"
    build_histogram_by_dates(
        out, 
        by_date, 
        title=f"Посещаемость по датам — {d.name}"
    )

    await call.message.answer_photo(
        FSInputFile(out), 
        caption=f"📈 Гистограмма: {d.name}"
    )
    await call.message.answer(text="Гистограмма сделана", reply_markup=kb_main_menu())
    await call.answer()

@router.callback_query(F.data.startswith("stats:xlsx:"))
async def stats_xlsx(call: CallbackQuery, db: AsyncSession, **_):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    did = int(call.data.split(":")[-1])
    d = await DisciplineRepo(db).get(did)
    if not d:
        await call.answer("Не найдено", show_alert=True)
        return
    
    stats = await AttendanceRepo(db).stats_for_discipline2(
        teacher.id,
        did
    )

    discipline_attendance = stats["discipline_attendance"]
    if not discipline_attendance:
        await call.answer(
            "Пока нет данных для xlsx", 
            show_alert=True
        )
        return

    students = await StudentRepo(db).list_for_teacher(teacher.id)

    payload = [{
        "full_name": s.full_name, 
    } for s in students]
    
    out = Path("out") / f"attendance_{teacher.tg_user_id}_{d.name}.xlsx"
    export_discipline_xlsx(out, d.name, discipline_attendance, payload)

    await call.message.answer_document(
        FSInputFile(out), 
        caption=f"📥 XLSX: {d.name}"
    )
    await call.message.answer(text="Таблица сделана", reply_markup=kb_main_menu())
    await call.answer()
