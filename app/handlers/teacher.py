from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import kb_teacher_menu, kb_start_role
from app.repositories.disciplines import DisciplineRepo
from app.repositories.students import StudentRepo
from app.repositories.teachers import TeacherRepo
from app.states import TeacherStates

router = Router()


async def require_teacher(db: AsyncSession, tg_user_id: int):
    return await TeacherRepo(db).get_by_tg_user_id(tg_user_id)


@router.callback_query(F.data == "menu:teacher")
async def teacher_menu(call: CallbackQuery, db: AsyncSession, **_):
    teacher = await require_teacher(db, call.from_user.id)
    if not teacher:
        await call.message.edit_text(
            "Нужно зарегистрироваться:", 
            reply_markup=kb_start_role()
        )
        await call.answer()
        return
    await call.message.edit_text(
        "⚙️ Управление:", 
        reply_markup=kb_teacher_menu()
    )
    await call.answer()


@router.callback_query(F.data == "teacher:add_discipline")
async def add_discipline_start(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await require_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer(
            "Сначала зарегистрируйтесь", 
            show_alert=True)
        return
    await state.set_state(TeacherStates.waiting_discipline_name)
    await call.message.edit_text("Введите название дисциплины одним сообщением.\nНапр.: `Матан`")
    await call.answer()


@router.message(TeacherStates.waiting_discipline_name)
async def add_discipline_finish(
    message: Message, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await require_teacher(db, message.from_user.id)
    if not teacher:
        await message.answer("Сначала зарегистрируйтесь: /start")
        return

    name = (message.text or "").strip()
    if not name:
        await message.answer("Пустое название. Попробуйте ещё раз.")
        return

    d = await DisciplineRepo(db).create_if_not_exists(teacher.id, name)
    await state.clear()
    await message.answer(
        f"✅ Дисциплина сохранена: {d.name}", 
        reply_markup=kb_teacher_menu()
    )


@router.callback_query(F.data == "teacher:import_students")
async def import_students_start(
    call: CallbackQuery, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await require_teacher(db, call.from_user.id)
    if not teacher:
        await call.answer("Сначала зарегистрируйтесь", show_alert=True)
        return
    await state.set_state(TeacherStates.waiting_students_bulk)
    await call.message.edit_text(
        "Пришлите список студентов — **каждое ФИО с новой строки**.\n"
        "Пример:\n"
        "Иванов Иван Иванович\n"
        "Петров Пётр Петрович\n"
        "Сидорова Анна Сергеевна"
    )
    await call.answer()


@router.message(TeacherStates.waiting_students_bulk)
async def import_students_finish(
    message: Message, 
    state: FSMContext, 
    db: AsyncSession, 
    **_
):
    teacher = await require_teacher(db, message.from_user.id)
    if not teacher:
        await message.answer("Сначала зарегистрируйтесь: /start")
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Пусто. Пришлите список ФИО.")
        return

    full_names = [line.strip() for line in text.splitlines() if line.strip()]
    created, skipped = await StudentRepo(db).bulk_create_if_not_exists(teacher.id, full_names)

    await state.clear()
    await message.answer(
        f"✅ Импорт завершён.\nДобавлено: {created}\nУже было: {skipped}",
        reply_markup=kb_teacher_menu(),
    )