from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import kb_main_menu, kb_start_role
from app.repositories.teachers import TeacherRepo

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession):
    tg_id = message.from_user.id
    teacher = await TeacherRepo(db).get_by_tg_user_id(tg_id)

    if not teacher:
        await message.answer(
            "Привет! Это бот-регистратор посещаемости.\n"
            "Чтобы начать работу, зарегистрируйтесь как преподаватель:",
            reply_markup=kb_start_role(),
        )
        return

    await message.answer("Меню:", reply_markup=kb_main_menu())


@router.callback_query(F.data == "menu:back")
async def back_to_menu(call: CallbackQuery, db: AsyncSession):
    teacher = await TeacherRepo(db).get_by_tg_user_id(
        call.from_user.id
    )
    if not teacher:
        await call.message.edit_text(
            "Нужно зарегистрироваться как преподаватель:", 
            reply_markup=kb_start_role()
        )
        await call.answer()
        return

    await call.message.edit_text("Меню:", reply_markup=kb_main_menu())
    await call.answer()


@router.callback_query(F.data == "role:teacher")
async def role_teacher(call: CallbackQuery, db: AsyncSession):
    display_name = (
        call.from_user.full_name or str(call.from_user.id)
    ).strip()
    await TeacherRepo(db).ensure_teacher(call.from_user.id, display_name)
    await call.message.edit_text(
        "✅ Профиль преподавателя создан.\nМеню:",
        reply_markup=kb_main_menu()
    )
    await call.answer()