from aiogram import Bot
from aiogram.types import BotCommand

async def set_default_commands(bot: Bot):
    """Установка стандартных команд бота"""
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="menu", description="Посмотреть меню"),
        BotCommand(command="cart", description="Посмотреть корзину"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="help", description="Помощь")
    ]
    await bot.set_my_commands(commands)