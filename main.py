import asyncio
import logging
from loader import setup
from handlers import register_all_handlers
from middlewares import register_all_middlewares
from utils.set_bot_commands import set_default_commands

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot, db):
    """Действия при запуске бота"""
    try:
        await set_default_commands(bot)
        logger.info("✅ Бот успешно запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")


async def on_shutdown(bot, db):
    """Действия при выключении бота"""
    try:
        if db:
            await db.close()
        await bot.session.close()
        logger.info("Бот выключен")
    except Exception as e:
        logger.error(f"Ошибка при выключении: {e}")


async def main():
    try:
        bot, dp, db = await setup()

        if not db or not db.conn:
            logger.error("Не удалось подключиться к базе данных")
            raise RuntimeError("Database connection failed")

        register_all_middlewares(dp)

        register_all_handlers(dp)

        await on_startup(bot, db)

        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
    finally:
        await on_shutdown(bot, db)


if __name__ == "__main__":
    asyncio.run(main())
