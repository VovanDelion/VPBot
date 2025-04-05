from datetime import datetime
import os


def format_cart(cart_items):
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0

    for item in cart_items:
        item_total = item['price'] * item['quantity']
        text += f"• {item['name']} x{item['quantity']} = {item_total} руб.\n"
        total += item_total

    text += f"\n<b>Итого: {total} руб.</b>"
    return text, total


def format_order(order_items):
    if not order_items:
        return "Информация о заказе недоступна"

    order = order_items[0]
    text = f"📦 <b>Заказ #{order['id']}</b>\n"
    text += f"📅 {order['created_at']}\n"
    text += f"🚚 Способ: {order['delivery_type']}\n"
    text += f"📞 Телефон: {order['phone_number']}\n"

    if order['delivery_type'] == 'delivery':
        text += f"🏠 Адрес: {order['address']}\n"

    text += "\n<b>Состав заказа:</b>\n"

    items_text = []
    for item in order_items:
        items_text.append(f"• {item['name']} x{item['quantity']} = {item['price'] * item['quantity']} руб.")

    text += "\n".join(items_text)
    text += f"\n\n<b>Итого: {order['total_amount']} руб.</b>"

    return text


def is_current_month(date_str):
    if isinstance(date_str, str):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    else:
        date_obj = date_str

    now = datetime.now()
    return date_obj.month == now.month and date_obj.year == now.year


async def is_admin(user_id):
    return user_id in list(map(int, os.getenv('ADMIN_IDS').split(',')))