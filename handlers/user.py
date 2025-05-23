import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from loader import db, bot
from states import UserRegistration
from keyboards.reply import request_phone_keyboard, main_menu_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer(
            "👋 Добро пожаловать в бот ресторана 'Вкус питона'!\n"
            "Пожалуйста, поделитесь своим номером телефона:",
            reply_markup=request_phone_keyboard(),
        )
        await state.set_state(UserRegistration.Phone)
    else:
        if user[5]:
            photo = FSInputFile(user[5])
            await message.answer_photo(
                photo,
                caption=f"🍽 Добро пожаловать, {user[2] or message.from_user.full_name}!",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await message.answer(
                f"🍽 Добро пожаловать, {user[2] or message.from_user.full_name}!",
                reply_markup=main_menu_keyboard(),
            )


@router.message(F.contact, UserRegistration.Phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number

    if phone_number.startswith("+"):
        normalized_phone = "+" + "".join(c for c in phone_number[1:] if c.isdigit())
    else:
        normalized_phone = "".join(c for c in phone_number if c.isdigit())

    await state.update_data(phone_number=normalized_phone, full_name=None)
    await message.answer(
        "📝 Теперь введите ваше имя:", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(UserRegistration.Name)


@router.message(UserRegistration.Name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(
        "📸 Теперь вы можете загрузить фото профиля (необязательно).\n"
        "Если не хотите добавлять фото, нажмите /skip",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(UserRegistration.Photo)


@router.message(Command("skip"), UserRegistration.Photo)
async def skip_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["full_name"],
        phone=data["phone_number"],
        profile_photo=None,
    )

    await message.answer(
        f"✅ Регистрация завершена, {data['full_name']}!\n"
        "Теперь вы можете сделать заказ.",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.message(F.photo, UserRegistration.Photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()

    os.makedirs("data/profile_photos", exist_ok=True)

    photo = message.photo[-1]
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    ext = file_path.split(".")[-1]
    filename = f"data/profile_photos/{message.from_user.id}.{ext}"
    await bot.download_file(file_path, filename)

    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["full_name"],
        phone=data["phone_number"],
        profile_photo=filename,
    )

    await message.answer_photo(
        FSInputFile(filename),
        caption=f"✅ Регистрация завершена, {data['full_name']}!\n"
        "Теперь вы можете сделать заказ.",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Справка по боту:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/menu - Посмотреть меню\n"
        "/cart - Посмотреть корзину\n"
        "/profile - Посмотреть профиль\n"
        "/help - Получить справку\n\n"
        "Если у вас возникли проблемы, обратитесь в поддержку."
    )


@router.message(F.text == "📞 Контакты")
async def contacts(message: types.Message):
    await message.answer("🙋‍♂️ Подержака: 89990109091\n🏆 Сотрудничесвто: 89188589091")


P_count = 0


@router.message(F.text.lower().strip() == "вкуспитона")
async def VP(message: types.Message):
    global P_count
    P_count += 1
    if P_count % 3 == 0:
        await message.answer("Большой Питон гордится тобой ❤️🐍")


@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user = await db.get_user(message.from_user.id)

    if user:
        text = f"<b>Ваш профиль:</b>\n\n"
        text += f"🆔 ID: {user[0]}\n"
        text += f"👤 Имя: {user[2]}\n"
        text += f"📞 Телефон: {user[3]}\n"
        text += f"📅 Дата регистрации: {user[4].split()[0]}"

        if user[5]:
            photo = FSInputFile(user[5])
            await message.answer_photo(photo, caption=text)
        else:
            await message.answer(text)
    else:
        await message.answer(
            "Вы еще не зарегистрированы. Нажмите /start",
            reply_markup=types.ReplyKeyboardRemove(),
        )


def register_user_handlers(dp):
    dp.include_router(router)
