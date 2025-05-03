import json
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from keyboards.inline import (
    menu_categories_keyboard,
    dishes_keyboard,
    back_to_menu_keyboard,
)
from loader import db

router = Router()


class MenuNavigation(StatesGroup):
    ChooseCategory = State()
    ChooseDish = State()


@router.message(Command("menu"))
@router.message(F.text == "🍽 Меню")
async def show_menu_categories(message: types.Message, state: FSMContext):
    categories = await db.get_dish_categories()
    await message.answer(
        "🍽 Выберите категорию:", reply_markup=menu_categories_keyboard(categories)
    )
    await state.set_state(MenuNavigation.ChooseCategory)


@router.callback_query(F.data.startswith("category_"), MenuNavigation.ChooseCategory)
async def show_dishes_in_category(call: types.CallbackQuery, state: FSMContext):
    try:
        category_id = int(call.data.split("_")[1])
        dishes = await db.get_dishes_by_category(category_id)

        category = await db.get_category(category_id)
        if isinstance(category, dict):
            category_name = category.get("name", f"Категория {category_id}")
        else:
            category_name = (
                category[1] if len(category) > 1 else f"Категория {category_id}"
            )

        await call.message.edit_text(
            f"🍴 {category_name}:\nВыберите блюдо:",
            reply_markup=dishes_keyboard(dishes, category_id),
        )
        await state.set_state(MenuNavigation.ChooseDish)
    except Exception as e:
        await call.answer("⚠️ Ошибка загрузки меню")


@router.callback_query(F.data.startswith("dish_"))
async def show_dish_details(call: types.CallbackQuery, state: FSMContext):
    try:
        dish_id = int(call.data.split("_")[1])
        dish = await db.get_dish_by_id(dish_id)

        if not dish:
            await call.answer("❌ Блюдо не найдено")
            return

        if isinstance(dish, dict):
            name = dish.get("name", "Без названия")
            description = dish.get("description", "")
            price = dish.get("price", 0)
        else:
            name = dish[1] if len(dish) > 1 else "Без названия"
            description = dish[2] if len(dish) > 2 else ""
            price = dish[3] if len(dish) > 3 else 0

        text = f"🍛 <b>{name}</b>\n\n"
        if description:
            text += f"📝 {description}\n\n"
        text += f"💰 Цена: {price} руб.\n\n"
        text += "Выберите действие:"

        await call.message.edit_text(text, reply_markup=back_to_menu_keyboard(dish_id))
    except json.JSONDecodeError:
        await call.answer("⚠️ Неверный формат данных")
    except Exception as e:
        await call.answer("⚠️ Ошибка загрузки блюда")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_menu_categories(call.message, state)
    await call.answer()


def register_menu_handlers(dp):
    dp.include_router(router)
