from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from loader import db
from datetime import datetime

router = Router()

class FeedbackProcess(StatesGroup):
    EnterComment = State()

def is_current_month(date_str):
    now = datetime.now()
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return date.month == now.month and date.year == now.year

@router.callback_query(F.data.startswith('feedback_'))
async def process_feedback(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split('_')
    rating = int(parts[1])
    order_id = int(parts[2])

    await call.message.edit_text(
        f"Спасибо за оценку {rating}★!\n"
        "Хотите оставить комментарий? (Отправьте текстом или нажмите /skip)"
    )

    await state.update_data(rating=rating, order_id=order_id)
    await state.set_state(FeedbackProcess.EnterComment)

@router.message(FeedbackProcess.EnterComment)
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    comment = message.text

    await db.add_feedback(
        user_id=message.from_user.id,
        order_id=data['order_id'],
        rating=data['rating'],
        comment=comment
    )

    await message.answer("Спасибо за ваш отзыв!")

    # Check if user has 3 orders this month for special sticker
    orders = await db.get_user_orders(message.from_user.id)
    recent_orders = [o for o in orders if is_current_month(o['created_at'])]

    if len(recent_orders) >= 3:
        await message.answer_sticker("CAACAgIAAxkBAAEIBQtkBQABYxKZ9CwWv3bU3V3V3V3V3V0C")
        await message.answer("Вы получили стикер 'Я ❤️ Вкус питона!' за 3 заказа в этом месяце!")

    await state.clear()

@router.message(Command('skip'), FeedbackProcess.EnterComment)
async def skip_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await db.add_feedback(
        user_id=message.from_user.id,
        order_id=data['order_id'],
        rating=data['rating'],
        comment=None
    )

    await message.answer("Спасибо за вашу оценку!")
    await state.clear()

def register_feedback_handlers(dp):
    dp.include_router(router)