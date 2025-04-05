from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline import admin_menu_keyboard
from loader import db
from states import AdminActions
from utils.helpers import is_admin

router = Router()

@router.message(Command('admin'), F.from_user.func(lambda user: is_admin(user.id)))
async def show_admin_menu(message: types.Message):
    await message.answer(
        "👨‍💻 Админ-панель:",
        reply_markup=admin_menu_keyboard()
    )

@router.callback_query(F.from_user.func(lambda user: is_admin(user.id)), F.data == 'admin_view_stats')
async def view_stats(call: types.CallbackQuery):
    stats = await db.get_admin_stats()

    text = (
        "📊 Статистика заказов:\n\n"
        f"• Всего заказов: {stats['total_orders']}\n"
        f"• Средний чек: {stats['avg_order']:.2f} руб.\n"
        f"• Общий доход: {stats['total_revenue']:.2f} руб.\n\n"
        "Последние заказы:\n"
        f"{stats['recent_orders']}"
    )

    await call.message.edit_text(
        text,
        reply_markup=admin_menu_keyboard()
    )

@router.callback_query(F.from_user.func(lambda user: is_admin(user.id)), F.data == 'admin_add_dish')
async def add_dish_start(call: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data='admin_back')]
    ])
    await call.message.edit_text(
        "Введите название блюда:",
        reply_markup=keyboard
    )
    await state.set_state(AdminActions.AddDishName)

@router.message(F.from_user.func(lambda user: is_admin(user.id)), AdminActions.AddDishName)
async def add_dish_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание блюда:")
    await state.set_state(AdminActions.AddDishDescription)

@router.message(F.from_user.func(lambda user: is_admin(user.id)), AdminActions.AddDishDescription)
async def add_dish_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену блюда (только число):")
    await state.set_state(AdminActions.AddDishPrice)

@router.message(F.from_user.func(lambda user: is_admin(user.id)), AdminActions.AddDishPrice)
async def add_dish_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)

        categories = await db.get_dish_categories()
        buttons = []
        for category in categories:
            buttons.append([
                InlineKeyboardButton(
                    text=category['name'],
                    callback_data=f'admin_category_{category["id"]}'
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "Выберите категорию для блюда:",
            reply_markup=keyboard
        )
        await state.set_state(AdminActions.AddDishCategory)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (только число):")

@router.callback_query(F.from_user.func(lambda user: is_admin(user.id)), F.data.startswith('admin_category_'), AdminActions.AddDishCategory)
async def add_dish_category(call: types.CallbackQuery, state: FSMContext):
    category_id = int(call.data.split('_')[2])
    data = await state.get_data()

    await db.add_dish(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        category_id=category_id
    )

    await call.message.edit_text(
        "✅ Блюдо успешно добавлено в меню!",
        reply_markup=admin_menu_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == 'admin_view_stats')
async def view_stats(call: types.CallbackQuery):
    stats = await db.get_admin_stats()
    await call.message.edit_text(
        f"📊 Статистика заказов:\n\n"
        f"• Всего заказов: {stats['total_orders']}\n"
        f"• Средний чек: {stats['avg_order']:.2f} руб.\n"
        f"• Доход: {stats['total_revenue']:.2f} руб.\n\n"
        f"Последние 5 заказов:\n{stats['recent_orders']}",
        reply_markup=admin_menu_keyboard()
    )


@router.callback_query(F.data == 'admin_manage_menu')
async def manage_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить блюдо", callback_data="admin_add_dish"),
        InlineKeyboardButton(text="✏️ Редактировать блюдо", callback_data="admin_edit_dish")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    )

    await call.message.edit_text(
        "📝 Управление меню:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'admin_manage_orders')
async def manage_orders(call: types.CallbackQuery):
    orders = await db.get_recent_orders(5)

    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.row(
            InlineKeyboardButton(
                text=f"Заказ #{order['id']} - {order['status']}",
                callback_data=f"admin_order_{order['id']}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    )

    text = "📦 Последние заказы:\n"
    text += "\n".join([f"#{o['id']} - {o['status']} - {o['total']} руб." for o in orders])

    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'admin_manage_users')
async def manage_users(call: types.CallbackQuery):
    users = await db.get_recent_users(5)

    builder = InlineKeyboardBuilder()
    for user in users:
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {user['full_name']}",
                callback_data=f"admin_user_{user['id']}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    )

    text = "👥 Последние пользователи:\n"
    text += "\n".join([f"{u['full_name']} - {u['registration_date']}" for u in users])

    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'admin_back')
async def back_to_admin_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "👨‍💻 Админ-панель:",
        reply_markup=admin_menu_keyboard()
    )

def register_admin_handlers(dp):
    dp.include_router(router)