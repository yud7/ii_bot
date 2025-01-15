import asyncio
import logging
import sqlite3
from typing import Callable, Awaitable, Any, Dict
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
import configparser
import aiosqlite

# Читаем токен из файла конфигурации
config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')

# Настраиваем логирование и создаем бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()

# Middleware для проверки регистрации пользователя
class SomeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, types.Message):  # Убедитесь, что это сообщение
            if event.text != '/start':  # Проверка на текст сообщения
                user_id = event.chat.id
                async with aiosqlite.connect('users.db') as db:
                    async with db.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_id,)) as cursor:
                        if await cursor.fetchone() is None:
                            await bot.send_message(
                                chat_id=user_id,
                                text='Вы не зарегистрированы! Зарегистрируйтесь, используя команду /start.'
                            )
                            return
        result = await handler(event, data)
        return result

# Подключение к SQLite базе данных
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Создание таблицы пользователей (если не создана)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    notification TEXT
)
""")
conn.commit()

# Хранилище для временных данных регистрации
registration_data = {}


# Команда /start
@dispatcher.message(Command('start'))
async def start(message: types.Message):

    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (message.from_user.id,)) as cursor:
            if await cursor.fetchone() is None:
                await cursor.execute('INSERT INTO users (telegram_id, notification) VALUES (?, ?)', (message.from_user.id, False))
                await db.commit()
                await message.answer(
                    f'{message.from_user.last_name} {message.from_user.first_name}! Вы зарегистрированы!')
            else:
                await message.answer(
                    f'Привет {message.from_user.last_name} {message.from_user.first_name}! Вы уже зарегистрированы!')



# Команда /help
@dispatcher.message(Command('help'))
async def help_command(message: types.Message):

    text = (
        "Hиже представлены все доступные команды:\n\n"
        "<b>/start</b> - Начать работа бота \n"
        "<b>/faq</b> - Самые частозадаваемы вопросы и ответы на них\n"
        "<b>/test</b> - Начать тест по выбранному предмету (например физика раздел термодинамика)\n"
        "<b>/career_guidance</b> - Начать тест на профориентацию\n"
        "<b>/profile</b> - Посмотреть статистику выполненых тестов и прогресс их выполнения\n"
    )

    await message.answer(text, parse_mode='HTML')


# Команда /profile (отображение профиля пользователя)
@dispatcher.message(Command('profile'))
async def profile(message: types.Message):
    await message.answer(f"Ваш профиль:{message.from_user.last_name} {message.from_user.first_name}")


# Прочие команды
@dispatcher.message(Command('faq'))
async def faq(message: types.Message):
    await message.answer('FAQ: Здесь будут часто задаваемые вопросы.')


@dispatcher.message(Command('test'))
async def test(message: types.Message):
    await message.answer('Проверка знаний.')


@dispatcher.message(Command('career_guidance'))
async def career_guidance(message: types.Message):
    await message.answer('Тест на профориентацию.')


@dispatcher.message(Command('exam'))
async def exam(message: types.Message):
    await message.answer('Подготовка к экзамену.')


# Запуск бота
async def start_bot():
    dispatcher.message.outer_middleware(SomeMiddleware())
    # dispatcher.update.middleware.register(SomeMiddleware())
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())