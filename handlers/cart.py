from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from keyboards.inline import cart_keyboard
from loader import db
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
            reply_markup=cart_keyboard(cart_items, total)
        )
    else:
        await message_or_callback.message.edit_text(
            text,
            reply_markup=cart_keyboard(cart_items, total)
        )

    await state.set_state(CartActions.ManageCart)

@router.callback_query(F.data == 'view_cart')
@router.message(Command('cart'))
@router.message(F.text == '🛒 Корзина')
async def show_cart(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cart_items = await db.get_cart_items(user_id)

    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста!")
        return

    text, total = format_cart(cart_items)
    await message.answer(
        text,
        reply_markup=cart_keyboard(cart_items, total)
    )
    await state.set_state(CartActions.ManageCart)

@router.callback_query(F.data.startswith('remove_'), CartActions.ManageCart)
async def remove_from_cart(callback: types.CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split('_')[1])
    await db.remove_from_cart(callback.from_user.id, item_id)

    cart_items = await db.get_cart_items(callback.from_user.id)
    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина пуста!")
        await state.clear()
        return

    text, total = format_cart(cart_items)
    await callback.message.edit_text(
        text,
        reply_markup=cart_keyboard(cart_items, total)
    )
    await callback.answer("Товар удалён из корзины")

@router.callback_query(F.data == 'checkout', CartActions.ManageCart)
async def checkout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите способ получения заказа:")
    await state.set_state(CartActions.ConfirmOrder)

@router.callback_query(
    F.data.func(lambda data: json.loads(data)['type'] == 'cart' and
               json.loads(data)['action'] == 'view'),
    StateFilter('*')  # Работает в любом состоянии
)
async def view_cart_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart_items = await db.get_cart_items(user_id)

    if not cart_items:
        await callback.answer("🛒 Ваша корзина пуста!", show_alert=True)
        return

    text, total = format_cart(cart_items)
    await callback.message.edit_text(
        text,
        reply_markup=cart_keyboard(cart_items, total)
    )
    await state.set_state(CartActions.ManageCart)
    await callback.answer()

def register_cart_handlers(dp):
    dp.include_router(router)