from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import loader
from keyboards.inline import cart_keyboard, menu_categories_keyboard
from loader import db
from handlers.menu import show_menu_categories
from states import CartActions
from utils.helpers import format_cart
from typing import Union
import json

router = Router()


async def _show_cart(user_id: int, message_or_callback: Union[types.Message, types.CallbackQuery], state: FSMContext):
    cart_items = await db.get_cart_items(user_id)

    if not cart_items:
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer("🛒 Ваша корзина пуста!")
        else:
            await message_or_callback.answer("🛒 Ваша корзина пуста!", show_alert=True)
        return

    text, total = format_cart(cart_items)

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(
            text,
            reply_markup=cart_keyboard(cart_items)
        )
    else:
        await message_or_callback.message.edit_text(
            text,
            reply_markup=cart_keyboard(cart_items)
        )

    await state.set_state(CartActions.ManageCart)


@router.message(Command('cart'))
async def show_cart(message: types.Message, state: FSMContext):
    await _show_cart(message.from_user.id, message, state)


@router.callback_query(F.data == 'view_cart')
async def view_cart_callback(callback: types.CallbackQuery, state: FSMContext):
    await _show_cart(callback.from_user.id, callback, state)


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    dish_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id

    # Получаем информацию о блюде из БД
    dish = await db.get_dish_by_id(dish_id)
    if not dish:
        await callback.answer("Блюдо не найдено!", show_alert=True)
        return

    # Добавляем блюдо в корзину
    await db.create_cart_tables()
    await db.add_to_cart(user_id, dish_id, dish['name'], dish['price'])

    await callback.answer(f"{dish['name']} добавлено в корзину!")

    # Возвращаемся в меню
    await callback.message.edit_text(
        "🍽 Меню:",
        show_menu_categories()
    )


@router.callback_query(F.data.startswith('remove_'), CartActions.ManageCart)
async def remove_from_cart(callback: types.CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split('_')[1])
    await db.remove_from_cart(callback.from_user.id, item_id)
    await callback.answer("Товар удалён из корзины")
    await _show_cart(callback.from_user.id, callback, state)


@router.callback_query(F.data.startswith('change_qty_'), CartActions.ManageCart)
async def change_quantity(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    action = data[2]
    item_id = int(data[3])

    if action == 'inc':
        await db.increase_quantity(callback.from_user.id, item_id)
    elif action == 'dec':
        await db.decrease_quantity(callback.from_user.id, item_id)

    await _show_cart(callback.from_user.id, callback, state)


@router.callback_query(F.data == 'clear_cart', CartActions.ManageCart)
async def clear_cart(callback: types.CallbackQuery, state: FSMContext):
    await db.clear_cart(callback.from_user.id)
    await callback.answer("Корзина очищена!", show_alert=True)
    await state.clear()

    # Возвращаемся в меню
    menu = await db.get_menu()
    await callback.message.edit_text(
        "🍽 Меню:",
        reply_markup=menu_categories_keyboard(menu)
    )


@router.callback_query(F.data == 'checkout', CartActions.ManageCart)
async def checkout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите способ получения заказа:")
    await state.set_state(CartActions.ConfirmOrder)


def register_cart_handlers(dp):
    dp.include_router(router)