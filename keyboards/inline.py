from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json


def menu_categories_keyboard(categories):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for category in categories:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=category['name'],
                callback_data=json.dumps({
                    'type': 'menu',
                    'action': 'view_category',
                    'category_id': category['id']
                })
            )
        ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text='🛒 Корзина',
            callback_data=json.dumps({'type': 'cart', 'action': 'view'})
        )
    ])
    return keyboard


def back_to_menu_keyboard(dish_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Добавить в корзину",
                callback_data=f"add_{dish_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к меню",
                callback_data="back_to_menu"
            )
        ]
    ])


def dishes_keyboard(dishes, category_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for dish in dishes:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=dish['name'],
                callback_data=json.dumps({
                    'type': 'menu',
                    'action': 'view_dish',
                    'dish_id': dish['id'],
                    'category_id': category_id
                })
            )
        ])

    # Добавляем кнопки назад и корзины в один ряд
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text='◀️ Назад',
            callback_data=json.dumps({'type': 'menu', 'action': 'view_categories'})
        ),
        InlineKeyboardButton(
            text='🛒 Корзина',
            callback_data=json.dumps({'type': 'cart', 'action': 'view'})
        )
    ])
    return keyboard

def cart_keyboard(cart_items):
    keyboard = InlineKeyboardMarkup()

    for item in cart_items:
        keyboard.row(
            InlineKeyboardButton(
                text=f"❌ {item['name']} ({item['quantity']})",
                callback_data=json.dumps({
                    'type': 'cart',
                    'action': 'remove',
                    'cart_item_id': item['cart_id']
                })
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text='✅ Оформить заказ',
            callback_data=json.dumps({'type': 'order', 'action': 'checkout'})
        )
    )

    keyboard.row(
        InlineKeyboardButton(
            text='◀️ Вернуться в меню',
            callback_data=json.dumps({'type': 'menu', 'action': 'view_categories'})
        )
    )
    return keyboard

def delivery_method_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            text='🚗 Доставка',
            callback_data=json.dumps({
                'type': 'order',
                'action': 'set_delivery',
                'method': 'delivery'
            })
        ),
        InlineKeyboardButton(
            text='🏃 Самовывоз',
            callback_data=json.dumps({
                'type': 'order',
                'action': 'set_delivery',
                'method': 'pickup'
            })
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='◀️ Назад',
            callback_data=json.dumps({'type': 'cart', 'action': 'view'})
        )
    )
    return keyboard

def rating_keyboard(order_id):
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(
        *[InlineKeyboardButton(
            text=f"{i}★",
            callback_data=json.dumps({
                'type': 'feedback',
                'rating': i,
                'order_id': order_id
            })
        ) for i in range(1, 6)]
    )
    return keyboard

def confirm_order_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data=json.dumps({
                'type': 'order',
                'action': 'confirm',
                'order_id': order_id
            })
        )],
        [InlineKeyboardButton(
            text="❌ Отменить заказ",
            callback_data=json.dumps({
                'type': 'order',
                'action': 'cancel',
                'order_id': order_id
            })
        )]
    ])

def admin_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            text='📊 Статистика',
            callback_data=json.dumps({'type': 'admin', 'action': 'stats'})
        ),
        InlineKeyboardButton(
            text='📝 Управление меню',
            callback_data=json.dumps({'type': 'admin', 'action': 'manage_menu'})
        ),
        InlineKeyboardButton(
            text='📦 Управление заказами',
            callback_data=json.dumps({'type': 'admin', 'action': 'manage_orders'})
        ),
        InlineKeyboardButton(
            text='👥 Управление пользователями',
            callback_data=json.dumps({'type': 'admin', 'action': 'manage_users'})
        )
    )
    return keyboard