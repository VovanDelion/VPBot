from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from loader import db, bot
from states import UserRegistration
from keyboards.reply import request_phone_keyboard, main_menu_keyboard

# Создаем роутер
router = Router()

# Обработчик команды /start
@router.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer(
            "👋 Добро пожаловать в бот ресторана 'Вкус питона'!\n"
            "Пожалуйста, поделитесь своим номером телефона:",
            reply_markup=request_phone_keyboard()
        )
        await state.set_state(UserRegistration.Phone)
    else:
        await message.answer(
            f"🍽 Добро пожаловать, {user[2] or message.from_user.full_name}!\n",
            reply_markup=main_menu_keyboard()
        )


# Обработчик получения номера телефона
@router.message(F.contact, UserRegistration.Phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number

    if phone_number.startswith('+'):
        normalized_phone = '+' + ''.join(c for c in phone_number[1:] if c.isdigit())
    else:
        normalized_phone = ''.join(c for c in phone_number if c.isdigit())

    await state.update_data(phone_number=normalized_phone)

    await message.answer(
        "📝 Теперь введите ваше имя:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(UserRegistration.Name)


# Обработчик получения имени
@router.message(UserRegistration.Name)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.text,
        phone=data['phone_number']
    )

    await message.answer(
        f"✅ Регистрация завершена, {message.text}!\n"
        "Теперь вы можете сделать заказ.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


# Обработчик команды /help
@router.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Справка по боту:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/menu - Посмотреть меню\n"
        "/cart - Посмотреть корзину\n"
        "/help - Получить справку\n\n"
        "Если у вас возникли проблемы, обратитесь в поддержку."
    )


# Обработчик команды /profile
@router.message(Command('profile'))
async def cmd_profile(message: types.Message):
    user = await db.get_user(message.from_user.id)

    if user:
        text = f"<b>Ваш профиль:</b>\n\n"
        text += f"🆔 ID: {user[0]}\n"
        text += f"👤 Имя: {user[2]}\n"
        text += f"📞 Телефон: {user[3]}\n"
        text += f"📅 Дата регистрации: {user[4]}"

        await message.answer(text)
    else:
        await message.answer(
            "Вы еще не зарегистрированы. Нажмите /start",
            reply_markup=types.ReplyKeyboardRemove()
        )


# Функция для регистрации обработчиков
def register_user_handlers(dp):
    dp.include_router(router)