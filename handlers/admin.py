from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline import admin_menu_keyboard, edit_keyboard
from loader import db
from data.config import ADMIN_IDS
from states import AdminActions
from utils.helpers import is_admin

router = Router()


class AdminActions(StatesGroup):
    AddDishName = State()
    AddDishDescription = State()
    AddDishPrice = State()
    AddDishCategory = State()
    AddCategoryName = State()
    EditDishSelect = State()
    EditDishName = State()
    EditDishDescription = State()
    EditDishPrice = State()
    EditDishCategory = State()


@router.message(Command("admin"))
async def show_admin_menu(message: types.Message):
    user = await db.get_user(message.from_user.id)

    if user[0] in ADMIN_IDS:
        await message.answer("👨‍💻 Админ-панель:", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("Вы не админ")


@router.callback_query(
    F.from_user.func(lambda user: is_admin(user.id)), F.data == "admin_view_stats"
)
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

    await call.message.edit_text(text, reply_markup=admin_menu_keyboard())


@router.callback_query(
    F.from_user.func(lambda user: is_admin(user.id)), F.data == "admin_add_dish"
)
async def add_dish_start(call: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ]
    )
    await call.message.edit_text("Введите название блюда:", reply_markup=keyboard)
    await state.set_state(AdminActions.AddDishName)


@router.message(
    F.from_user.func(lambda user: is_admin(user.id)), AdminActions.AddDishName
)
async def add_dish_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание блюда:")
    await state.set_state(AdminActions.AddDishDescription)


@router.message(
    F.from_user.func(lambda user: is_admin(user.id)), AdminActions.AddDishDescription
)
async def add_dish_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену блюда (только число):")
    await state.set_state(AdminActions.AddDishPrice)


@router.message(
    F.from_user.func(lambda user: is_admin(user.id)), AdminActions.AddDishPrice
)
async def add_dish_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)

        categories = await db.get_all_categories()
        if not categories:
            await message.answer("Нет доступных категорий. Сначала создайте категории.")
            await state.clear()
            return

        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.button(
                text=category["name"],
                callback_data=f'admin_category_{category["category_id"]}',
            )

        builder.button(text="◀️ Назад", callback_data="admin_back")

        builder.adjust(2, 1)

        await message.answer(
            "Выберите категорию для блюда:", reply_markup=builder.as_markup()
        )
        await state.set_state(AdminActions.AddDishCategory)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (только число):")


@router.callback_query(
    F.from_user.func(lambda user: is_admin(user.id)),
    F.data.startswith("admin_category_"),
    AdminActions.AddDishCategory,
)
async def add_dish_category(call: types.CallbackQuery, state: FSMContext):
    try:
        category_id = int(call.data.split("_")[2])
        data = await state.get_data()

        success = await db.add_dish(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            category_id=category_id,
        )

        if success:
            await call.message.edit_text(
                "✅ Блюдо успешно добавлено в меню!", reply_markup=admin_menu_keyboard()
            )
        else:
            await call.message.edit_text(
                "❌ Не удалось добавить блюдо", reply_markup=admin_menu_keyboard()
            )
    finally:
        await state.clear()


@router.callback_query(F.data == "admin_view_stats")
async def view_stats(call: types.CallbackQuery):
    stats = await db.get_admin_stats()
    await call.message.edit_text(
        f"📊 Статистика заказов:\n\n"
        f"• Всего заказов: {stats['total_orders']}\n"
        f"• Средний чек: {stats['avg_order']:.2f} руб.\n"
        f"• Доход: {stats['total_revenue']:.2f} руб.\n\n"
        f"Последние 5 заказов:\n{stats['recent_orders']}",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data == "admin_manage_menu")
async def manage_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить блюдо", callback_data="admin_add_dish"),
        InlineKeyboardButton(
            text="✏️ Редактировать блюдо", callback_data="admin_edit_dish"
        ),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))

    await call.message.edit_text(
        "📝 Управление меню:", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "admin_manage_orders")
async def manage_orders(call: types.CallbackQuery):
    orders = await db.get_recent_orders(5)

    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.row(
            InlineKeyboardButton(
                text=f"Заказ #{order['id']} - {order['status']}",
                callback_data=f"admin_order_{order['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))

    text = "📦 Последние заказы:\n"
    text += "\n".join(
        [f"#{o['id']} - {o['status']} - {o['total']} руб." for o in orders]
    )

    await call.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin_manage_users")
async def manage_users(call: types.CallbackQuery):
    users = await db.get_recent_users(5)

    builder = InlineKeyboardBuilder()
    for user in users:
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {user['full_name']}", callback_data=f"admin_user_{user['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))

    text = "👥 Последние пользователи:\n"
    text += "\n".join([f"{u['full_name']} - {u['registration_date']}" for u in users])

    await call.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin_manage_categories")
async def manage_categories(call: types.CallbackQuery):
    """Меню управления категориями"""
    categories = await db.get_all_categories()

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить категорию", callback_data="admin_add_category"
        ),
        InlineKeyboardButton(
            text="🗑 Удалить категорию", callback_data="admin_delete_category"
        ),
    )

    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"📁 {category['name']}",
                callback_data=f"admin_view_category_{category['category_id']}",
            )
        )

    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))

    text = "📂 Управление категориями:\n"
    if categories:
        text += "\n".join([f"- {c['name']}" for c in categories])
    else:
        text += "Пока нет категорий"

    if hasattr(call, "message") and call.message:
        await call.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await call.answer(text)


@router.callback_query(F.data == "admin_add_category")
async def add_category_start(call: types.CallbackQuery, state: FSMContext):
    """Начало добавления категории"""
    await call.message.edit_text(
        "Введите название новой категории:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data="admin_manage_categories"
                    )
                ]
            ]
        ),
    )
    await state.set_state(AdminActions.AddCategoryName)


@router.message(AdminActions.AddCategoryName)
async def add_category_name(message: types.Message, state: FSMContext):
    """Добавление новой категории"""
    category_name = message.text.strip()
    if len(category_name) < 2:
        await message.answer("Название категории должно быть не короче 2 символов")
        return

    success = await db.add_category(category_name)
    if success:
        await message.answer(f"✅ Категория '{category_name}' успешно добавлена!")
    else:
        await message.answer(
            "❌ Не удалось добавить категорию. Возможно, она уже существует."
        )

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Вернуться к категориям",
                    callback_data="admin_manage_categories",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 В админ-панель", callback_data="admin_back"
                )
            ],
        ]
    )

    await message.answer("Выберите действие:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("admin_view_category_"))
async def view_category(call: types.CallbackQuery):
    """Просмотр категории"""
    category_id = int(call.data.split("_")[3])
    category = await db.get_category(category_id)
    dishes = await db.get_dishes_by_category(category_id)

    text = f"📁 Категория: {category['name']}\n\n"
    text += "🍽 Блюда в этой категории:\n"
    text += "\n".join([f"- {d['name']} ({d['price']} руб.)" for d in dishes])

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data="admin_manage_categories"
                    )
                ]
            ]
        ),
    )


@router.callback_query(F.data == "admin_delete_category")
async def delete_category_start(call: types.CallbackQuery):
    """Начало удаления категории"""
    categories = await db.get_all_categories()

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 {category['name']}",
                callback_data=f"admin_confirm_delete_category_{category['category_id']}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manage_categories")
    )

    await call.message.edit_text(
        "Выберите категорию для удаления:", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("admin_confirm_delete_category_"))
async def confirm_delete_category(call: types.CallbackQuery):
    """Подтверждение удаления категории"""
    category_id = int(call.data.split("_")[4])
    category = await db.get_category(category_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да",
                    callback_data=f"admin_do_delete_category_{category_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Нет", callback_data="admin_manage_categories"
                ),
            ]
        ]
    )

    await call.message.edit_text(
        f"Вы уверены, что хотите удалить категорию '{category['name']}'?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("admin_do_delete_category_"))
async def do_delete_category(call: types.CallbackQuery):
    """Удаление категории"""
    category_id = int(call.data.split("_")[4])
    success = await db.delete_category(category_id)

    if success:
        await call.message.edit_text(
            "✅ Категория успешно удалена!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="admin_manage_categories"
                        )
                    ]
                ]
            ),
        )
    else:
        await call.message.edit_text(
            "❌ Не удалось удалить категорию. Возможно, она используется в блюдах.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="admin_manage_categories"
                        )
                    ]
                ]
            ),
        )


@router.callback_query(F.data == "admin_edit_dish")
async def edit_dish_start(call: types.CallbackQuery, state: FSMContext):
    """Начало редактирования блюда - выбор блюда"""
    try:
        dishes = await db.get_all_dishes()

        if not dishes:
            await call.message.edit_text(
                "Нет блюд для редактирования", reply_markup=admin_menu_keyboard()
            )
            return

        if not isinstance(dishes, list) or not all(isinstance(d, dict) for d in dishes):
            raise ValueError("Invalid dishes data format")

        builder = InlineKeyboardBuilder()
        for dish in dishes:
            if not all(key in dish for key in ["dish_id", "name", "price"]):
                continue

            builder.button(
                text=f"{dish['name']} ({dish['price']} руб.)",
                callback_data=f"admin_edit_select_{dish['dish_id']}",
            )
        builder.button(text="◀️ Назад", callback_data="admin_back")
        builder.adjust(1)

        await call.message.edit_text(
            "Выберите блюдо для редактирования:", reply_markup=builder.as_markup()
        )
        await state.set_state(AdminActions.EditDishSelect)

    except Exception as e:
        await call.message.edit_text(
            f"Ошибка при получении списка блюд: {str(e)}",
            reply_markup=admin_menu_keyboard(),
        )


@router.callback_query(
    F.data.startswith("admin_edit_select_"), AdminActions.EditDishSelect
)
async def edit_dish_select(call: types.CallbackQuery, state: FSMContext):
    dish_id = int(call.data.split("_")[3])
    dish = await db.get_dish_by_id(dish_id)

    if not dish:
        await call.answer("Блюдо не найдено")
        return

    await state.update_data(dish_id=dish_id)

    await call.message.edit_text(
        f"Выберите что редактировать для блюда {dish['name']}:",
        reply_markup=edit_keyboard(dish_id=dish_id),
    )


@router.callback_query(F.data == "admin_edit_name")
async def edit_dish_name_start(call: types.CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    await call.message.edit_text("Введите новое название блюда:")
    await state.set_state(AdminActions.EditDishName)


@router.message(AdminActions.EditDishName)
async def edit_dish_name(message: types.Message, state: FSMContext):
    """Сохранение нового названия"""
    data = await state.get_data()
    await db.update_dish(
        dish_id=data["dish_id"],
        name=message.text,
    )
    await message.answer(
        f"✅ Название успешно обновлено!\n\n" f"Выберите что редактировать для блюда:",
        reply_markup=edit_keyboard(dish_id=data["dish_id"]),
    )
    await state.set_state(AdminActions.EditDishSelect)


@router.callback_query(F.data == "admin_edit_description")
async def edit_dish_description_start(call: types.CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    await call.message.edit_text("Введите новое описание блюда:")
    await state.set_state(AdminActions.EditDishDescription)


@router.message(AdminActions.EditDishDescription)
async def edit_dish_description(message: types.Message, state: FSMContext):
    """Сохранение нового описания"""
    data = await state.get_data()
    await db.update_dish(
        dish_id=data["dish_id"],
        description=message.text,
    )
    await message.answer(
        "Описание успешно обновлено!",
        reply_markup=edit_keyboard(dish_id=data["dish_id"]),
    )
    await state.set_state(AdminActions.EditDishSelect)


@router.callback_query(F.data == "admin_edit_price")
async def edit_dish_price_start(call: types.CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    await call.message.edit_text("Введите новую цену блюда:")
    await state.set_state(AdminActions.EditDishPrice)


@router.message(AdminActions.EditDishPrice)
async def edit_dish_price(message: types.Message, state: FSMContext):
    """Сохранение новой цены"""
    try:
        price = float(message.text)
        data = await state.get_data()
        await db.update_dish(
            dish_id=data["dish_id"],
            price=price,
        )
        await message.answer(
            "Цена успешно обновлена!",
            reply_markup=edit_keyboard(dish_id=data["dish_id"]),
        )
        await state.set_state(AdminActions.EditDishSelect)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (число):")


@router.callback_query(F.data == "admin_edit_category")
async def edit_dish_category_start(call: types.CallbackQuery, state: FSMContext):
    """Начало редактирования категории"""
    categories = await db.get_all_categories()

    if not categories:
        await call.answer("Нет доступных категорий")
        return

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category["name"],
            callback_data=f"admin_edit_category_select_{category['category_id']}",
        )
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(2, 1)

    await call.message.edit_text(
        "Выберите новую категорию для блюда:", reply_markup=builder.as_markup()
    )
    await state.set_state(AdminActions.EditDishCategory)


@router.callback_query(
    F.data.startswith("admin_edit_category_select_"), AdminActions.EditDishCategory
)
async def edit_dish_category_select(call: types.CallbackQuery, state: FSMContext):
    """Сохранение новой категории"""
    category_id = int(call.data.split("_")[4])
    data = await state.get_data()

    await db.update_dish(dish_id=data["dish_id"], category_id=category_id)

    category = await db.get_category(category_id)
    await call.message.edit_text(
        f"Категория успешно изменена на {category['name']}!",
        reply_markup=edit_keyboard(dish_id=data["dish_id"]),
    )
    await state.set_state(AdminActions.EditDishSelect)


@router.callback_query(F.data == "admin_view_feedback")
async def view_feedback(call: types.CallbackQuery):
    """Просмотр всех отзывов"""
    try:
        feedbacks = await db.get_all_feedback()

        if not feedbacks:
            await call.message.edit_text(
                "Пока нет отзывов", reply_markup=admin_menu_keyboard()
            )
            return

        text = "📝 Все отзывы:\n\n"
        for fb in feedbacks:
            user = await db.get_user(fb["user_id"])
            username = user[1] if user and len(user) > 1 else "Аноним"
            text += (
                f"⭐️ Оценка: {fb['rating']}/5\n"
                f"👤 Пользователь: {username}\n"
                f"📅 Дата: {fb['created_at']}\n"
            )
            if fb["comment"]:
                text += f"📝 Комментарий: {fb['comment']}\n"
            text += "――――――――――――――――――――\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
            ]
        )

        await call.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        await call.message.edit_text(
            "Ошибка при получении отзывов", reply_markup=admin_menu_keyboard()
        )


@router.callback_query(F.data.startswith("admin_delete_dish_"))
async def delete_dish_confirmation(call: types.CallbackQuery):
    dish_id = int(call.data.split("_")[3])
    dish = await db.get_dish_by_id(dish_id)

    if not dish:
        await call.answer("Блюдо не найдено")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да", callback_data=f"admin_do_delete_dish_{dish_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Нет", callback_data=f"admin_edit_select_{dish_id}"
                ),
            ]
        ]
    )

    await call.message.edit_text(
        f"Вы уверены, что хотите удалить блюдо '{dish['name']}'?", reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("admin_do_delete_dish_"))
async def delete_dish_execute(call: types.CallbackQuery):
    dish_id = int(call.data.split("_")[4])
    success = await db.delete_dish(dish_id)

    if success:
        await call.message.edit_text(
            "✅ Блюдо успешно удалено!", reply_markup=admin_menu_keyboard()
        )
    else:
        await call.message.edit_text(
            "❌ Не удалось удалить блюдо", reply_markup=admin_menu_keyboard()
        )


@router.callback_query(F.data == "admin_back")
async def back_to_admin_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "👨‍💻 Админ-панель:", reply_markup=admin_menu_keyboard()
    )


def register_admin_handlers(dp):
    dp.include_router(router)
