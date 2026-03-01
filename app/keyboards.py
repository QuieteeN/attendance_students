from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def kb_start_role() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="👨‍🏫 Я преподаватель", 
                callback_data="role:teacher"
            )],
        ]
    )


def kb_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📝 Отметить посещаемость", 
                callback_data="menu:attendance"
            )],
            [InlineKeyboardButton(
                text="📊 Статистика", 
                callback_data="menu:stats"
            )],
            [InlineKeyboardButton(
                text="⚙️ Управление", 
                callback_data="menu:teacher"
            )],
        ]
    )


def kb_teacher_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ Создать дисциплину", 
                callback_data="teacher:add_discipline"
            )],
            [InlineKeyboardButton(
                text="👥 Импорт списка студентов (ФИО)", 
                callback_data="teacher:import_students"
            )],
            [InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data="menu:back"
            )],
        ]
    )


def kb_disciplines(
    items: list[tuple[int, str]], 
    cb_prefix: str, 
    back_cb: str = "menu:back"
):
    rows = []
    for did, name in items:
        rows.append([
            InlineKeyboardButton(
                text=name, 
                callback_data=f"{cb_prefix}:pick:{did}"
            )
        ])
    rows.append([InlineKeyboardButton(
        text="⬅️ Назад", 
        callback_data=back_cb
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_students_toggle(
    students: list[tuple[int, str]],
    present_ids: set[int],
    cb_prefix: str,
    save_cb: str,
    export_cb: str,
    back_cb: str,
) -> InlineKeyboardMarkup:
    rows = []
    for sid, full_name in students:
        is_present = sid in present_ids
        mark = "✅ " if is_present else "⬜️ "
        rows.append([
            InlineKeyboardButton(
                text=f"{mark}{full_name}", 
                callback_data=f"{cb_prefix}:toggle:{sid}"
            )
        ])

    rows.append(
        [
            InlineKeyboardButton(
                text="💾 Сохранить", 
                callback_data=save_cb
            ),
            InlineKeyboardButton(
                text="📥 XLSX", 
                callback_data=export_cb
            ),
        ]
    )
    rows.append([InlineKeyboardButton(
        text="⬅️ Назад", 
        callback_data=back_cb
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_stats_actions(discipline_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🧾 Текстовая сводка", 
                callback_data=f"stats:text:{discipline_id}"
            )],
            [InlineKeyboardButton(
                text="📈 Гистограмма по датам", 
                callback_data=f"stats:hist:{discipline_id}"
            )],
            [InlineKeyboardButton(
                text="📥 XLSX по дисциплине ", 
                callback_data=f"stats:xlsx:{discipline_id}"
            )],
            [InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data="menu:back"
            )],
        ]
    )