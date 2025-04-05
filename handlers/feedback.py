from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from loader import db
from datetime import datetime
from keyboards.reply import feedback_keyboard, remove_keyboard
from keyboards.reply import main_menu_keyboard

router = Router()


class FeedbackProcess(StatesGroup):
    SelectRating = State()
    EnterComment = State()


@router.message(F.text == "✏️ Оставить отзыв")
async def start_feedback(message: types.Message, state: FSMContext):
    """Начало процесса оставления отзыва"""
    await message.answer(
        "Пожалуйста, оцените наше заведение (1-5 звезд):",
        reply_markup=feedback_keyboard()
    )
    await state.set_state(FeedbackProcess.SelectRating)


@router.message(F.text.in_(["⭐️ 1", "⭐️ 2", "⭐️ 3", "⭐️ 4", "⭐️ 5"]), FeedbackProcess.SelectRating)
async def process_rating(message: types.Message, state: FSMContext):
    """Обработка выбранной оценки"""
    rating = int(message.text.split()[1])  # Извлекаем цифру из "⭐️ 1"
    await state.update_data(rating=rating)

    await message.answer(
        "Спасибо за оценку! Теперь напишите ваш отзыв (или /skip чтобы пропустить):",
        reply_markup=remove_keyboard()
    )
    await state.set_state(FeedbackProcess.EnterComment)


@router.message(FeedbackProcess.EnterComment, ~F.text.startswith('/'))
async def process_comment(message: types.Message, state: FSMContext):
    """Обработка текстового отзыва"""
    data = await state.get_data()
    comment = message.text

    await db.add_feedback(
        user_id=message.from_user.id,
        order_id=None,  # Можно привязать к конкретному заказу, если нужно
        rating=data['rating'],
        comment=comment
    )

    await message.answer(
        "Спасибо за ваш отзыв! Мы ценим ваше мнение.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


@router.message(Command("skip"), FeedbackProcess.EnterComment)
async def skip_comment(message: types.Message, state: FSMContext):
    """Пропуск комментария"""
    data = await state.get_data()

    await db.add_feedback(
        user_id=message.from_user.id,
        order_id=None,
        rating=data['rating'],
        comment=None
    )

    await message.answer(
        "Спасибо за вашу оценку!",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


def register_feedback_handlers(dp):
    dp.include_router(router)