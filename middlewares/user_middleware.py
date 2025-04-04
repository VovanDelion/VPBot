from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable


class UserMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # Получаем объект пользователя в зависимости от типа события
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.message.from_user.id
        else:
            return await handler(event, data)

        # Получаем пользователя из базы данных
        db = data.get('db')
        if not db:
            raise ValueError("Database connection not found")

        data['user'] = await db.get_user(user_id)
        return await handler(event, data)