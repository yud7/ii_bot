from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import save_user_data

router = Router()

# Состояния FSM для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_email = State()

@router.message(Command("start"))
async def start_registration(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать! Напишите ваше имя.")
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько вам лет?")
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(RegistrationStates.waiting_for_age)
async def get_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом.")
        return
    await state.update_data(age=message.text)
    await message.answer("Введите ваш email.")
    await state.set_state(RegistrationStates.waiting_for_email)

@router.message(RegistrationStates.waiting_for_email)
async def get_email(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_data["email"] = message.text

    # Сохранение данных
    save_user_data(user_data)
    await message.answer("Регистрация завершена! Вы можете использовать бота.")
    await state.clear()
