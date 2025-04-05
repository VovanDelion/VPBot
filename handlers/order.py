import asyncio
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from keyboards.inline import confirm_order_keyboard, rating_keyboard
from keyboards.reply import request_phone_keyboard, request_location_keyboard
from loader import db
from utils.helpers import format_order

router = Router()

class OrderProcess(StatesGroup):
    ChooseDelivery = State()
    EnterAddress = State()
    EnterPhone = State()


@router.message(F.text == "📦 Мои заказы")
async def show_user_orders(message: types.Message):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас пока нет заказов")
        return

    text = "📦 Ваши заказы:\n\n"
    for order in orders:
        text += f"🔹 #{order['id']} - {order['status']} - {order['total']} руб.\n"

    await message.answer(text)

@router.callback_query(F.text == "📦 Мои заказы")
async def process_delivery_choice(call: types.CallbackQuery, state: FSMContext):
    delivery_type = call.data.split('_')[1]
    await state.update_data(delivery_type=delivery_type)

    user_data = await db.get_user(call.from_user.id)

    if delivery_type == 'delivery':
        if user_data and user_data.get('address'):
            await call.message.edit_text(
                f"Доставка по адресу: {user_data['address']}\n"
                "Подтвердите адрес или отправьте новый:",
                reply_markup=request_location_keyboard()
            )
        else:
            await call.message.edit_text(
                "Пожалуйста, отправьте ваш адрес доставки:",
                reply_markup=request_location_keyboard()
            )
        await state.set_state(OrderProcess.EnterAddress)
    else:
        await call.message.edit_text(
            "Самовывоз по адресу: ул. Питонова, 42\n"
            "Время работы: 10:00 - 22:00"
        )
        await state.set_state(OrderProcess.EnterPhone)
        await call.message.answer(
            "Пожалуйста, отправьте ваш номер телефона:",
            reply_markup=request_phone_keyboard()
        )

# Исправленный обработчик контактов
@router.message(F.content_type == 'contact', OrderProcess.EnterPhone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone_number=phone_number)

    data = await state.get_data()
    cart_items = await db.get_cart_items(message.from_user.id)

    total = sum(item['price'] * item['quantity'] for item in cart_items)
    if 'promo_code' in data:
        discount = data['promo_discount']
        total = total * (1 - discount)

    order_id = await db.create_order(
        user_id=message.from_user.id,
        total_amount=total,
        delivery_type=data['delivery_type'],
        address=data.get('address', 'Самовывоз'),
        phone_number=phone_number
    )

    await db.add_order_items(order_id, cart_items)
    await db.clear_cart(message.from_user.id)

    order_details = await db.get_order_details(order_id)
    order_text = format_order(order_details)

    await message.answer(
        f"✅ Заказ #{order_id} оформлен!\n\n"
        f"{order_text}\n\n"
        "Спасибо за заказ! Ожидайте подтверждения.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await asyncio.sleep(3600)
    await message.answer(
        "Пожалуйста, оцените ваш заказ:",
        reply_markup=rating_keyboard(order_id)
    )

    await state.clear()

def register_order_handlers(dp):
    dp.include_router(router)