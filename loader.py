from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from data.config import BOT_TOKEN
from services.database import Database

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()


async def setup():
    """Инициализация всех компонентов"""
    await db.connect()
    dp["db"] = db
    return bot, dp, db


async def add_to_cart(self, user_id, dish_id, name, price):
    """Добавляет блюдо в корзину"""
    async with self.connection.execute(
        "INSERT OR REPLACE INTO cart (user_id, dish_id, name, price, quantity) "
        "VALUES (?, ?, ?, ?, COALESCE((SELECT quantity FROM cart WHERE user_id = ? AND dish_id = ?), 0) + 1)",
        (user_id, dish_id, name, price, user_id, dish_id)
    ) as cursor:
        await self.connection.commit()

async def remove_from_cart(self, user_id, dish_id):
    """Удаляет блюдо из корзины"""
    async with self.connection.execute(
        "DELETE FROM cart WHERE user_id = ? AND dish_id = ?",
        (user_id, dish_id)
    ) as cursor:
        await self.connection.commit()

async def increase_quantity(self, user_id, dish_id):
    """Увеличивает количество на 1"""
    await self.connection.execute(
        "UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND dish_id = ?",
        (user_id, dish_id)
    )
    await self.connection.commit()

async def decrease_quantity(self, user_id, dish_id):
    """Уменьшает количество на 1 или удаляет если 0"""
    await self.connection.execute(
        "UPDATE cart SET quantity = quantity - 1 WHERE user_id = ? AND dish_id = ? AND quantity > 1",
        (user_id, dish_id)
    )
    await self.connection.execute(
        "DELETE FROM cart WHERE user_id = ? AND dish_id = ? AND quantity <= 1",
        (user_id, dish_id)
    )
    await self.connection.commit()