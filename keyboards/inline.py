from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json


def menu_categories_keyboard(categories):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for category in categories:
        if isinstance(category, dict):
            cat_id = category.get("category_id")
            name = category.get("name")
        else:
            cat_id = category[0]
            name = category[1]

        if cat_id and name:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=name, callback_data=f"category_{cat_id}")]
            )

    return keyboard


def edit_keyboard(dish_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Название", callback_data="admin_edit_name"
                ),
                InlineKeyboardButton(
                    text="📝 Описание", callback_data="admin_edit_description"
                ),
            ],
            [
                InlineKeyboardButton(text="💰 Цена", callback_data="admin_edit_price"),
                InlineKeyboardButton(
                    text="📂 Категория", callback_data="admin_edit_category"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить", callback_data=f"admin_delete_dish_{dish_id}"
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
        ]
    )


def back_to_menu_keyboard(dish_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить в корзину", callback_data=f"add_to_cart_{dish_id}"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад к меню", callback_data="back_to_menu")],
        ]
    )


def dishes_keyboard(dishes, category_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for dish in dishes:
        if isinstance(dish, dict):
            dish_id = dish.get("dish_id")
            name = dish.get("name")
            price = dish.get("price")
        else:
            dish_id = dish[0]
            name = dish[1]
            price = dish[3] if len(dish) > 2 else None

        if not dish_id or not name:
            continue

        text = f"{name}"
        if price is not None:
            text += f" - {price}₽"

        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=text, callback_data=f"dish_{dish_id}")]
        )

    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"),
        ]
    )

    return keyboard


def cart_keyboard(cart_items):
    keyboard = InlineKeyboardMarkup

    for item in cart_items:
        keyboard.row(
            InlineKeyboardButton(
                text=f"❌ {item['name']} ({item['quantity']})",
                callback_data=json.dumps(
                    {
                        "type": "cart",
                        "action": "remove",
                        "cart_item_id": item["cart_id"],
                    }
                ),
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text="✅ Оформить заказ",
            callback_data=json.dumps({"type": "order", "action": "checkout"}),
        )
    )

    keyboard.row(
        InlineKeyboardButton(
            text="◀️ Вернуться в меню",
            callback_data=json.dumps({"type": "menu", "action": "view_categories"}),
        )
    )
    return keyboard


def delivery_method_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            text="🚗 Доставка",
            callback_data=json.dumps(
                {"type": "order", "action": "set_delivery", "method": "delivery"}
            ),
        ),
        InlineKeyboardButton(
            text="🏃 Самовывоз",
            callback_data=json.dumps(
                {"type": "order", "action": "set_delivery", "method": "pickup"}
            ),
        ),
    )
    keyboard.add(
        InlineKeyboardButton(
            text="◀️ Назад", callback_data=json.dumps({"type": "cart", "action": "view"})
        )
    )
    return keyboard


def rating_keyboard(order_id):
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(
        *[
            InlineKeyboardButton(
                text=f"{i}★",
                callback_data=json.dumps(
                    {"type": "feedback", "rating": i, "order_id": order_id}
                ),
            )
            for i in range(1, 6)
        ]
    )
    return keyboard


def confirm_order_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить заказ",
                    callback_data=json.dumps(
                        {"type": "order", "action": "confirm", "order_id": order_id}
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data=json.dumps(
                        {"type": "order", "action": "cancel", "order_id": order_id}
                    ),
                )
            ],
        ]
    )


def admin_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_view_stats")],
        [
            InlineKeyboardButton(
                text="📝 Управление меню", callback_data="admin_manage_menu"
            ),
            InlineKeyboardButton(
                text="📂 Управление категориями",
                callback_data="admin_manage_categories",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📦 Управление заказами", callback_data="admin_manage_orders"
            ),
            InlineKeyboardButton(
                text="📝 Просмотр отзывов", callback_data="admin_view_feedback"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
