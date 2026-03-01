from aiogram import Router

from .start import router as start_router
from .teacher import router as teacher_router
from .attendance import router as attendance_router
from .stats import router as stats_router


def get_root_router() -> Router:
    root = Router()
    root.include_router(start_router)
    root.include_router(teacher_router)
    root.include_router(attendance_router)
    root.include_router(stats_router)
    return root