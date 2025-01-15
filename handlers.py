import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
import configparser

# Читаем токен из файла конфигурации
config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')

# Настраиваем логирование и создаем бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()

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
async def help(message: types.Message):
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
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())