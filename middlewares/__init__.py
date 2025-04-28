from aiogram import Dispatcher
from .user_middleware import UserMiddleware


def register_all_middlewares(dp: Dispatcher):
    # Регистрируем все middleware
    dp.update.outer_middleware(UserMiddleware())
