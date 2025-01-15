# handlers.py
import asyncio
import logging
import sqlite3
from typing import Callable, Awaitable, Any, Dict
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
import configparser
import aiosqlite

# -----------------------------------------------------------------------------
# Читаем токен из файла конфигурации
# -----------------------------------------------------------------------------
config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')

# -----------------------------------------------------------------------------
# Настраиваем логирование и создаём бота
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()

# -----------------------------------------------------------------------------
# Middleware для проверки регистрации пользователя
# -----------------------------------------------------------------------------
class SomeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, является ли событие сообщением
        if isinstance(event, types.Message):
            # Если это не команда /start, проверяем регистрацию
            if event.text != '/start':
                user_id = event.from_user.id
                async with aiosqlite.connect('users.db') as db:
                    async with db.execute(
                        "SELECT telegram_id FROM users WHERE telegram_id = ?",
                        (user_id,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row is None:
                            await bot.send_message(
                                chat_id=user_id,
                                text='Вы не зарегистрированы! Зарегистрируйтесь, используя команду /start.'
                            )
                            return
        return await handler(event, data)

# -----------------------------------------------------------------------------
# Подключение к БД, создаём таблицу (если не существует)
# -----------------------------------------------------------------------------
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Добавляем колонку last_activity, если её нет, чтобы хранить дату/время
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    notification TEXT,
    last_activity DATETIME
)
""")
conn.commit()

# -----------------------------------------------------------------------------
# Хэндлеры команд
# -----------------------------------------------------------------------------

@dispatcher.message(Command("start"))
async def start_command(message: types.Message):
    """
    Регистрирует пользователя, если он ещё не в базе,
    и устанавливает время последней активности.
    """
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        # Проверяем, есть ли уже запись
        async with db.execute("""
            SELECT id FROM users WHERE telegram_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()

        if row is None:
            # Создаём новую запись с текущим временем
            now_str = datetime.now().isoformat()
            await db.execute("""
                INSERT INTO users (telegram_id, notification, last_activity)
                VALUES (?, ?, ?)
            """, (user_id, 'False', now_str))
            await db.commit()

            await message.answer(
                f'{message.from_user.last_name} {message.from_user.first_name}, вы зарегистрированы!'
            )
        else:
            await message.answer(
                f'Привет, {message.from_user.last_name} {message.from_user.first_name}! '
                f'Вы уже зарегистрированы!'
            )


@dispatcher.message(Command("help"))
async def help_command(message: types.Message):
    text = (
        "Ниже представлены все доступные команды:\n\n"
        "<b>/start</b> - Зарегистрироваться\n"
        "<b>/faq</b> - Часто задаваемые вопросы\n"
        "<b>/test</b> - Начать тест\n"
        "<b>/career_guidance</b> - Тест на профориентацию\n"
        "<b>/profile</b> - Просмотр профиля\n"
        "<b>/exam</b> - Подготовка к экзамену\n"
    )
    await message.answer(text, parse_mode='HTML')


@dispatcher.message(Command("profile"))
async def profile_command(message: types.Message):
    await message.answer(
        f"Ваш профиль: {message.from_user.last_name} {message.from_user.first_name}"
    )


@dispatcher.message(Command("faq"))
async def faq_command(message: types.Message):
    await message.answer('FAQ: Здесь будут часто задаваемые вопросы.')


@dispatcher.message(Command("test"))
async def test_command(message: types.Message):
    await message.answer('Проверка знаний.')


@dispatcher.message(Command("career_guidance"))
async def career_guidance_command(message: types.Message):
    await message.answer('Тест на профориентацию.')


@dispatcher.message(Command("exam"))
async def exam_command(message: types.Message):
    await message.answer('Подготовка к экзамену.')


# -----------------------------------------------------------------------------
# Хэндлер на любое сообщение: обновляем last_activity
# -----------------------------------------------------------------------------
@dispatcher.message()
async def any_message_handler(message: types.Message):
    """
    Любое сообщение от пользователя обновляет время последней активности.
    """
    user_id = message.from_user.id
    now_str = datetime.now().isoformat()

    async with aiosqlite.connect('users.db') as db:
        await db.execute("""
            UPDATE users
            SET last_activity = ?
            WHERE telegram_id = ?
        """, (now_str, user_id))
        await db.commit()

    # Можно отреагировать по-своему, либо не отвечать
    await message.answer("Сообщение получено, активность обновлена.")

# -----------------------------------------------------------------------------
# Функция старта бота
# -----------------------------------------------------------------------------
async def start_bot():
    # Регистрируем middleware
    dispatcher.message.outer_middleware(SomeMiddleware())
    await dispatcher.start_polling(bot)