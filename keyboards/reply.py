from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def request_phone_keyboard():
    """Клавиатура для запроса номера телефона"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def request_location_keyboard():
    """Клавиатура для запроса местоположения"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить местоположение", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard():
    """Основное меню бота"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Меню")],
            [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📦 Мои заказы")],
            [
                KeyboardButton(text="📞 Контакты"),
                KeyboardButton(text="✏️ Оставить отзыв"),
            ],
        ],
        resize_keyboard=True,
    )


def cart_keyboard():
    """Клавиатура для работы с корзиной"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Оформить заказ")],
            [KeyboardButton(text="🔄 Очистить корзину")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def delivery_keyboard():
    """Клавиатура выбора способа получения"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Доставка")],
            [KeyboardButton(text="🏃 Самовывоз")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def confirm_order_keyboard():
    """Клавиатура подтверждения заказа"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить заказ")],
            [KeyboardButton(text="✏️ Изменить адрес")],
            [KeyboardButton(text="❌ Отменить")],
        ],
        resize_keyboard=True,
    )


def feedback_keyboard():
    """Клавиатура для отзывов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⭐️ 1"),
                KeyboardButton(text="⭐️ 2"),
                KeyboardButton(text="⭐️ 3"),
            ],
            [KeyboardButton(text="⭐️ 4"), KeyboardButton(text="⭐️ 5")],
        ],
        resize_keyboard=True,
    )


def remove_keyboard():
    """Удаление клавиатуры"""
    return ReplyKeyboardRemove()
