from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@dataclass(frozen=True)
class CalPayload:
    year: int
    month: int

    def encode(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @staticmethod
    def decode(s: str):
        y, m = s.split("-")
        return CalPayload(year=int(y), month=int(m))


def build_calendar_keyboard(
    payload: CalPayload, 
    cb_prefix: str, 
    selected: date | None = None
):
    year, month = payload.year, payload.month
    cal = calendar.Calendar(firstweekday=0)  # Monday
    month_days = cal.monthdayscalendar(year, month)

    header = calendar.month_name[month] + f" {year}"
    rows: list[list[InlineKeyboardButton]] = []
    rows.append([
        InlineKeyboardButton(
            text=header, 
            callback_data=f"{cb_prefix}:noop"
        )
    ])

    wd = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    rows.append([
        InlineKeyboardButton(
            text=x, 
            callback_data=f"{cb_prefix}:noop"
        ) for x in wd
    ])

    for week in month_days:
        row_btns = []
        for day in week:
            if day == 0:
                row_btns.append(
                    InlineKeyboardButton(
                        text=" ", 
                        callback_data=f"{cb_prefix}:noop"
                    )
                )
                continue
            d = date(year, month, day)
            mark = "✅" if (selected == d) else ""
            row_btns.append(
                InlineKeyboardButton(
                    text=f"{day}{mark}", 
                    callback_data=f"{cb_prefix}:pick:{d.isoformat()}"
                )
            )
        rows.append(row_btns)

    prev_y, prev_m = (year, month - 1) if month > 1 else (year - 1, 12)
    next_y, next_m = (year, month + 1) if month < 12 else (year + 1, 1)

    rows.append(
        [
            InlineKeyboardButton(text="◀️", callback_data=f"{cb_prefix}:nav:{prev_y:04d}-{prev_m:02d}"),
            InlineKeyboardButton(text="Сегодня", callback_data=f"{cb_prefix}:pick:{date.today().isoformat()}"),
            InlineKeyboardButton(text="▶️", callback_data=f"{cb_prefix}:nav:{next_y:04d}-{next_m:02d}"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)