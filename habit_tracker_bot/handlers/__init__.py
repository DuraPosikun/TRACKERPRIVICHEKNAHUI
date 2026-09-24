from aiogram import Dispatcher

from handlers.admin import router as admin_router
from handlers.admin_lolz import router as admin_lolz_router
from handlers.calendar import router as calendar_router
from handlers.common import router as common_router
from handlers.habits import router as habits_router
from handlers.lolz import router as lolz_router
from handlers.profile import router as profile_router
from handlers.settings import router as settings_router
from handlers.start import router as start_router
from handlers.statistics import router as statistics_router


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(common_router)
    dp.include_router(start_router)
    dp.include_router(habits_router)
    dp.include_router(lolz_router)
    dp.include_router(statistics_router)
    dp.include_router(calendar_router)
    dp.include_router(profile_router)
    dp.include_router(settings_router)
    dp.include_router(admin_lolz_router)
    dp.include_router(admin_router)
