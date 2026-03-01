from aiogram.fsm.state import State, StatesGroup


class TeacherStates(StatesGroup):
    waiting_discipline_name = State()
    waiting_students_bulk = State()


class AttendanceStates(StatesGroup):
    choosing_discipline = State()
    choosing_date = State()
    marking = State()