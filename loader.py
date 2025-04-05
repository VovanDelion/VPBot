from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from data.config import BOT_TOKEN
from services.database import Database

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

async def setup():
    """Инициализация всех компонентов"""
    await db.connect()
    dp['db'] = db
    return bot, dp, db