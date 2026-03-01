from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import kb_disciplines, kb_students_toggle, kb_start_role, kb_main_menu  
from app.repositories.attendance import AttendanceRepo
from app.repositories.disciplines import DisciplineRepo
from app.repositories.sessions import SessionRepo
from app.repositories.students import StudentRepo
from app.repositories.teachers import TeacherRepo
from app.services.calendar_ui import CalPayload, build_calendar_keyboard
from app.services.xlsx_export import export_attendance_xlsx
from app.states import AttendanceStates

router = Router()

CAL_PREFIX = "cal_att"
DISC_PREFIX = "att_disc"
STUD_PREFIX = "att_stud"


async def get_teacher(db: AsyncSession, tg_user_id: int):
    return await TeacherRepo(db).get_by_tg_user_id(tg_user_id)


@router.callback_query(F.data == "menu:attendance")
async def attendance_start(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.message.edit_text(
            "Нужно зарегистрироваться:", 
            reply_markup=kb_start_role()
        )
        await call.answer()
        return

    await state.set_state(AttendanceStates.choosing_discipline)
    disciplines = await DisciplineRepo(db).list_for_teacher(teacher.id)
    if not disciplines:
        await call.message.edit_text(
            "Нет дисциплин. Создайте их в ⚙️ Управление.",
            reply_markup=kb_main_menu(),
        )
        await call.answer()
        return

    items = [(d.id, d.name) for d in disciplines]
    print(items)
    await call.message.edit_text(
        "Выберите дисциплину:", 
        reply_markup=kb_disciplines(items, cb_prefix=DISC_PREFIX)
    )
    await call.answer()


@router.callback_query(F.data.startswith(f"{DISC_PREFIX}:pick:"))
async def attendance_choose_discipline(
    call: CallbackQuery, 
    state: FSMContext, 
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
        await call.answer("Нет доступа к дисциплине", show_alert=True)
        return

    d = await DisciplineRepo(db).get(did)
    await state.update_data(
        discipline_id=did, 
        discipline_name=d.name
    )
    await state.set_state(AttendanceStates.choosing_date)

    today = date.today()
    kb = build_calendar_keyboard(
        CalPayload(today.year, today.month), 
        cb_prefix=CAL_PREFIX
    )
    await call.message.edit_text(
        f"📅 Выберите дату лекции для «{d.name}»:", 
        reply_markup=kb
    )
    await call.answer()


@router.callback_query(F.data.startswith(f"{CAL_PREFIX}:nav:"))
async def calendar_nav(call: CallbackQuery, **_):
    ym = call.data.split(":")[-1]
    payload = CalPayload.decode(ym)
    kb = build_calendar_keyboard(payload, cb_prefix=CAL_PREFIX)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith(f"{CAL_PREFIX}:pick:"))
async def calendar_pick_date(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    picked = datetime.fromisoformat(call.data.split(":")[-1]).date()
    data = await state.get_data()
    did = int(data["discipline_id"])
    dname = str(data["discipline_name"])

    session = await SessionRepo(db).create_if_not_exists(did, picked)
    await state.update_data(
        session_id=session.id, 
        session_date=picked.isoformat()
    )
    await state.set_state(AttendanceStates.marking)

    students = await StudentRepo(db).list_for_teacher(teacher.id)
    if not students:
        await call.message.edit_text(
            "Нет студентов. Импортируйте список в ⚙️ Управление:",
            reply_markup=kb_main_menu(),
        )
        await call.answer()
        return

    present_ids = await AttendanceRepo(db).list_present_student_ids(
        session.id
    )

    kb = kb_students_toggle(
        students=[(s.id, s.full_name) for s in students],
        present_ids=present_ids,
        cb_prefix=STUD_PREFIX,
        save_cb="att:save",
        export_cb="att:export_xlsx",
        back_cb="menu:attendance",
    )

    await call.message.edit_text(
        f"📝 Отметка посещаемости\nДисциплина: {dname}\n"
        f"Дата: {picked.isoformat()}\n\n"
        f"Нажимайте на ФИО, чтобы отметить присутствие:",
        reply_markup=kb,
    )
    await call.answer()


@router.callback_query(F.data.startswith(f"{STUD_PREFIX}:toggle:"))
async def toggle_student(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    parts = call.data.split(":")
    student_id = int(parts[2])
    page = int(parts[3])
    data = await state.get_data()
    session_id = int(data["session_id"])

    arepo = AttendanceRepo(db)
    now_present = await arepo.is_present(session_id, student_id)
    await arepo.set_present(session_id, student_id, present=not now_present)

    students = await StudentRepo(db).list_for_teacher(teacher.id)
    present_ids = await arepo.list_present_student_ids(session_id)

    kb = kb_students_toggle(
        students=[(s.id, s.full_name) for s in students],
        present_ids=present_ids,
        cb_prefix=STUD_PREFIX,
        save_cb="att:save",
        export_cb="att:export_xlsx",
        back_cb="menu:attendance",
        page=page,  # сохраняем текущую страницу
    )
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer("Ок")

@router.callback_query(F.data.startswith(f"{STUD_PREFIX}:page:"))
async def change_page(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession
):
    page = int(call.data.split(":")[-1])

    data = await state.get_data()
    session_id = int(data["session_id"])

    teacher = await get_teacher(db, call.from_user.id)
    students = await StudentRepo(db).list_for_teacher(teacher.id)
    present_ids = await AttendanceRepo(db).list_present_student_ids(
        session_id
    )

    kb = kb_students_toggle(
        students=[(s.id, s.full_name) for s in students],
        present_ids=present_ids,
        cb_prefix=STUD_PREFIX,
        save_cb="att:save",
        export_cb="att:export_xlsx",
        back_cb="menu:attendance",
        page=page,
    )

    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "att:save")
async def attendance_save(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    data = await state.get_data()
    dname = str(data["discipline_name"])
    session_id = int(data["session_id"])
    sdate = date.fromisoformat(str(data["session_date"]))

    students = await StudentRepo(db).list_for_teacher(teacher.id)
    present_ids = await AttendanceRepo(db).list_present_student_ids(
        session_id
    )
    present_count = sum(1 for s in students if s.id in present_ids)

    await call.message.edit_text(
        f"✅ Сохранено!\nДисциплина: {dname}\nДата: {sdate.isoformat()}\n"
        f"Присутствовали: {present_count}/{len(students)}\n\n"
        f"Можно перейти в 📊 Статистика.",
        reply_markup=kb_main_menu(),
    )
    await state.clear()
    await call.answer("Сохранено ✅")


@router.callback_query(F.data == "att:export_xlsx")
async def attendance_export_xlsx(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await get_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала /start", show_alert=True)
        return

    data = await state.get_data()
    if "session_id" not in data:
        await call.answer("Сначала выберите дату", show_alert=True)
        return

    dname = str(data["discipline_name"])
    session_id = int(data["session_id"])
    sdate = date.fromisoformat(str(data["session_date"]))

    students = await StudentRepo(db).list_for_teacher(teacher.id)
    present_ids = await AttendanceRepo(db).list_present_student_ids(
        session_id
    )

    payload = [{
        "full_name": s.full_name, 
        "present": (s.id in present_ids)
    } for s in students]
    out = Path("out") / f"attendance_{teacher.tg_user_id}_{sdate.isoformat()}.xlsx"
    export_attendance_xlsx(out, dname, sdate, payload)

    await call.message.answer_document(
        FSInputFile(out), 
        caption=f"📥 XLSX: {dname} ({sdate.isoformat()})"
    )
    await call.message.answer(text="Таблица сделана", reply_markup=kb_main_menu())
    await call.answer()