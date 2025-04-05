from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from keyboards.inline import menu_categories_keyboard, dishes_keyboard, back_to_menu_keyboard
from loader import db

router = Router()

class MenuNavigation(StatesGroup):
    ChooseCategory = State()
    ChooseDish = State()

@router.message(F.text == '🍽 Меню')
async def show_menu_categories(message: types.Message, state: FSMContext):
    categories = await db.get_dish_categories()
    await message.answer(
        "🍽 Выберите категорию:",
        reply_markup=menu_categories_keyboard(categories)
    )
    await state.set_state(MenuNavigation.ChooseCategory)

@router.callback_query(F.data.startswith('category_'), MenuNavigation.ChooseCategory)
async def show_dishes_in_category(call: types.CallbackQuery, state: FSMContext):
    category_id = int(call.data.split('_')[1])
    dishes = await db.get_dishes_by_category(category_id)

    await call.message.edit_text(
        "🍴 Выберите блюдо:",
        reply_markup=dishes_keyboard(dishes, category_id)
    )
    await state.set_state(MenuNavigation.ChooseDish)

@router.callback_query(F.data.startswith('dish_'), MenuNavigation.ChooseDish)
async def show_dish_details(call: types.CallbackQuery, state: FSMContext):
    dish_id = int(call.data.split('_')[1])
    dish = await db.get_dish_by_id(dish_id)

    text = f"🍛 <b>{dish[1]}</b>\n\n"
    text += f"📝 {dish[2]}\n\n"
    text += f"💰 Цена: {dish[3]} руб.\n\n"
    text += "Выберите действие:"

    await call.message.edit_text(
        text,
        reply_markup=back_to_menu_keyboard(dish_id)
    )

@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_menu_categories(call.message, state)
    await call.answer()

def register_menu_handlers(dp):
    dp.include_router(router)