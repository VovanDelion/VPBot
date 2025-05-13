import asyncio
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline import confirm_order_keyboard, rating_keyboard
from keyboards.reply import (
    request_phone_keyboard,
    request_location_keyboard,
    main_menu_keyboard,
)
from loader import db
from utils.helpers import format_order

router = Router()


class OrderProcess(StatesGroup):
    ChooseDelivery = State()
    EnterAddress = State()
    EnterPhone = State()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    cart_items = await db.get_cart_items(message.from_user.id)

    if not cart_items:
        await message.answer("Ваша корзина пуста")
        return

    total = 0
    cart_text = "🛒 Ваша корзина:\n\n"

    for item in cart_items:
        cart_text += f"{item['name']} - {item['quantity']} x {item['price']} руб. = {item['quantity'] * item['price']} руб.\n"
        total += item["quantity"] * item["price"]

    cart_text += f"\n💳 Итого: {total} руб."

    # Создаем клавиатуру для управления корзиной
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="❌ Очистить корзину", callback_data="clear_cart"
        ),
        types.InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
    )
    builder.adjust(1)

    await message.answer(cart_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    await db.clear_cart(call.from_user.id)
    await call.message.edit_text("Ваша корзина очищена")
    await call.answer()


@router.message(F.text == "📦 Мои заказы")
async def show_user_orders(message: types.Message):
    orders = await db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer("У вас пока нет заказов")
        return

    orders_text = "📦 Ваши заказы:\n\n"

    for order in orders:
        status_emoji = {
            "new": "🆕",
            "processing": "🔄",
            "completed": "✅",
            "cancelled": "❌",
        }.get(order["status"].lower(), "❓")

        orders_text += (
            f"{status_emoji} Заказ #{order['id']}\n"
            f"📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            f"💰 Сумма: {order['total']} руб.\n"
            f"🚚 {order['delivery_type']}\n"
            f"📦 {len(order['items'])} позиций\n\n"
        )

    await message.answer(orders_text)


@router.callback_query(F.data == "checkout")
async def start_checkout(call: types.CallbackQuery, state: FSMContext):
    cart_items = await db.get_cart_items(call.from_user.id)

    if not cart_items:
        await call.answer("Ваша корзина пуста", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="🚗 Самовывоз", callback_data="delivery_pickup"
        ),
        types.InlineKeyboardButton(
            text="🚚 Доставка", callback_data="delivery_delivery"
        ),
    )
    builder.adjust(1)

    await call.message.edit_text(
        "Выберите способ получения заказа:", reply_markup=builder.as_markup()
    )

    await state.set_state(OrderProcess.ChooseDelivery)


@router.callback_query(F.data.startswith("delivery_"))
async def process_delivery_choice(call: types.CallbackQuery, state: FSMContext):
    delivery_type = call.data.split("_")[1]
    await state.update_data(delivery_type=delivery_type)

    if delivery_type == "delivery":
        user_data = await db.get_user(call.from_user.id)

        location_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📍 Отправить местоположение",
                        callback_data="send_location",
                    )
                ]
            ]
        )

        if user_data:
            await call.message.edit_text(
                "Отправте адрес:",
                reply_markup=location_keyboard,
            )
        await state.set_state(OrderProcess.EnterAddress)
    else:
        await call.message.edit_text(
            "Самовывоз по адресу: ул. Питонова, 42\n" "Время работы: 10:00 - 22:00"
        )


@router.callback_query(F.data == "send_location")
async def request_location(call: types.CallbackQuery):
    await call.message.answer("зов", reply_markup=request_location_keyboard())


@router.message(F.content_type == "location")
async def handle_location(message: types.Message):
    await message.answer(
        "Спасибо! Ваше местоположение получено.", reply_markup=main_menu_keyboard()
    )


@router.message(F.content_type == "contact", OrderProcess.EnterPhone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone_number=phone_number)

    data = await state.get_data()
    cart_items = await db.get_cart_items(message.from_user.id)

    total = sum(item["price"] * item["quantity"] for item in cart_items)

    if "promo_code" in data:
        discount = data["promo_discount"]
        total = total * (1 - discount)

    order_id = await db.create_order(
        user_id=message.from_user.id,
        total_amount=total,
        delivery_type=data["delivery_type"],
        address=data.get("address", "Самовывоз"),
        phone_number=phone_number,
    )

    await db.add_order_items(order_id, cart_items)
    await db.clear_cart(message.from_user.id)

    order_details = await db.get_order_details(order_id)
    order_text = format_order(order_details)

    await message.answer(
        f"✅ Заказ #{order_id} оформлен!\n\n"
        f"{order_text}\n\n"
        "Спасибо за заказ! Ожидайте подтверждения.",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    await asyncio.sleep(3600)
    await message.answer(
        "Пожалуйста, оцените ваш заказ:", reply_markup=rating_keyboard(order_id)
    )

    await state.clear()


def register_order_handlers(dp):
    dp.include_router(router)
