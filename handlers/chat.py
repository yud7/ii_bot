from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Утилита для работы с GigaChat API
from utils.gigachat import query_gigachat

router = Router()


@router.message(Command("chat"))
async def chat_command(message: types.Message, state: FSMContext):
    await message.answer("Напишите ваш вопрос для GigaChat.")
    await state.set_state("waiting_for_question")


@router.message(state="waiting_for_question")
async def handle_question(message: types.Message, state: FSMContext):
    user_question = message.text
    await message.answer("Обрабатываю ваш запрос...")

    try:
        # Запрос к GigaChat API
        response = query_gigachat(user_question)
        await message.answer(f"GigaChat ответил:\n{response}")
    except Exception as e:
        await message.answer("Произошла ошибка при обращении к GigaChat. Попробуйте позже.")

    await state.clear()
