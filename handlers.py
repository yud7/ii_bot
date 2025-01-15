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
    name TEXT,
    age INTEGER,
    email TEXT
)
""")
conn.commit()

# Хранилище для временных данных регистрации
registration_data = {}

# Команда /start
@dispatcher.message(Command('start'))
async def start(message: types.Message):
    await message.answer("Привет! Для использования всех функций бота зарегистрируйтесь с помощью команды /register.")

# Команда /register (регистрация пользователя)
@dispatcher.message(Command('register'))
async def register(message: types.Message):
    telegram_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer(f"Вы уже зарегистрированы!\nВаш профиль:\nИмя: {user[2]}\nВозраст: {user[3]}\nEmail: {user[4]}")
    else:
        registration_data[telegram_id] = {}
        registration_data[telegram_id]['step'] = 'name'
        await message.answer("Введите ваше имя:")

# Обработка данных регистрации
@dispatcher.message(lambda message: message.from_user.id in registration_data)
async def process_registration(message: types.Message):
    telegram_id = message.from_user.id
    step = registration_data[telegram_id]['step']

    if step == 'name':
        registration_data[telegram_id]['name'] = message.text
        registration_data[telegram_id]['step'] = 'age'
        await message.answer("Введите ваш возраст:")
    elif step == 'age':
        if not message.text.isdigit():
            await message.answer("Возраст должен быть числом. Попробуйте снова:")
            return
        registration_data[telegram_id]['age'] = int(message.text)
        registration_data[telegram_id]['step'] = 'email'
        await message.answer("Введите ваш email:")
    elif step == 'email':
        registration_data[telegram_id]['email'] = message.text

        # Сохраняем данные в базу данных
        try:
            cursor.execute(
                "INSERT INTO users (telegram_id, name, age, email) VALUES (?, ?, ?, ?)",
                (telegram_id,
                 registration_data[telegram_id]['name'],
                 registration_data[telegram_id]['age'],
                 registration_data[telegram_id]['email'])
            )
            conn.commit()

            await message.answer("Регистрация завершена! Теперь вы можете использовать все функции бота.")
        except sqlite3.IntegrityError:
            await message.answer("Вы уже зарегистрированы.")
        finally:
            del registration_data[telegram_id]

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

    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer(text, parse_mode='HTML')
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")

# Команда /profile (отображение профиля пользователя)
@dispatcher.message(Command('profile'))
async def profile(message: types.Message):
    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer(f"Ваш профиль:\nИмя: {user[2]}\nВозраст: {user[3]}\nEmail: {user[4]}")
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")

# Прочие команды
@dispatcher.message(Command('faq'))
async def faq(message: types.Message):

    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer('FAQ: Здесь будут часто задаваемые вопросы.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")

@dispatcher.message(Command('test'))
async def test(message: types.Message):

    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer('Проверка знаний.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")

@dispatcher.message(Command('career_guidance'))
async def career_guidance(message: types.Message):

    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer('Тест на профориентацию.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")

@dispatcher.message(Command('exam'))
async def exam(message: types.Message):

    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    if user:
        await message.answer('Подготовка к экзамену.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")

# Запуск бота
async def start_bot():
    dispatcher.update.middleware.register(SomeMiddleware())
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())