from aiogram import Router, types
from aiogram.filters import Command

router = Router()

FAQ_TEXT = """
<b>Часто задаваемые вопросы:</b>
1. Как зарегистрироваться? - Используйте команду /start.
2. Что делает этот бот? - Помогает с профориентацией и тестированием.
3. Как задать вопрос GigaChat? - Введите команду /chat.
"""

@router.message(Command("faq"))
async def faq_command(message: types.Message):
    await message.answer(FAQ_TEXT, parse_mode="HTML")
