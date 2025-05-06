from aiogram.fsm.state import State, StatesGroup


class UserRegistration(StatesGroup):
    Phone = State()
    Name = State()
    Photo = State()


class MenuNavigation(StatesGroup):
    ChooseCategory = State()
    ChooseDish = State()


class CartActions(StatesGroup):
    ManageCart = State()
    ConfirmOrder = State()


class OrderProcess(StatesGroup):
    ChooseDelivery = State()
    EnterAddress = State()
    EnterPhone = State()
    ApplyPromo = State()


class FeedbackProcess(StatesGroup):
    EnterComment = State()


class AdminActions(StatesGroup):
    AddDishName = State()
    AddDishDescription = State()
    AddDishPrice = State()
    AddDishCategory = State()
    AddDishPhoto = State()
