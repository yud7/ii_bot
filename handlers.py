import logging
import configparser

from typing import Callable, Awaitable, Any, Dict
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from database_modification import (
    initialize_db,
    get_user_by_id,
    insert_user,
    update_last_activity,
    set_notifications_enabled
)
from token_updater import query_gigachat
from gigachat_talking import generate_test

config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()

# ------------------------------------------------------------------------------
# Middleware для регистрации и обновления last_activity
# ------------------------------------------------------------------------------
class SomeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            user_data = await get_user_by_id(user_id)

            # Если пользователь уже есть, обновляем last_activity
            if user_data:
                await update_last_activity(user_id)

            # Логика /start и пошаговая регистрация
            if not hasattr(self, "registration_step"):
                self.registration_step = None

            if event.text == '/start':
                if user_data:
                    # Пользователь уже зарегистрирован
                    first_name, last_name = user_data[2], user_data[3]
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"{first_name} {last_name}, вы уже зарегистрированы!"
                    )
                else:
                    # Начинаем процесс регистрации
                    self.registration_step = 1
                    await bot.send_message(
                        chat_id=user_id,
                        text="Введите ваше имя:"
                    )
                return

            if self.registration_step:
                # Регистрация в несколько шагов
                if self.registration_step == 1:
                    self.first_name = event.text
                    await bot.send_message(chat_id=user_id, text="Введите вашу фамилию:")
                    self.registration_step += 1
                elif self.registration_step == 2:
                    self.last_name = event.text
                    await bot.send_message(chat_id=user_id, text="Введите ваш возраст:")
                    self.registration_step += 1
                elif self.registration_step == 3:
                    try:
                        age = int(event.text)
                        if 1 <= age <= 120:
                            await insert_user(user_id, self.first_name, self.last_name, age)
                            await update_last_activity(user_id)  # сразу обновляем активность
                            await bot.send_message(chat_id=user_id, text="Регистрация завершена!")
                            self.registration_step = None
                        else:
                            await bot.send_message(
                                chat_id=user_id,
                                text="Пожалуйста, введите возраст от 1 до 120."
                            )
                    except ValueError:
                        await bot.send_message(chat_id=user_id, text="Введите корректный возраст.")
                    return
                return

            # Если пользователь НЕ зарегистрирован, просим выполнить /start
            if not user_data:
                await bot.send_message(
                    chat_id=user_id,
                    text="Вы не зарегистрированы! Пожалуйста, используйте команду /start для регистрации."
                )
                return

        return await handler(event, data)

# ------------------------------------------------------------------------------
# Команда /start (повторная)
# ------------------------------------------------------------------------------
@dispatcher.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if user_data:
        await message.answer(
            f'Привет, {message.from_user.last_name} {message.from_user.first_name}! '
            'Вы уже зарегистрированы!'
        )

# ------------------------------------------------------------------------------
# Команда /help
# ------------------------------------------------------------------------------
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
        "<b>/disable_reminders</b> - Отключить напоминания\n"
        "<b>/enable_reminders</b> - Включить напоминания\n"
    )
    await message.answer(text, parse_mode='HTML')

# ------------------------------------------------------------------------------
# Команда /profile
# ------------------------------------------------------------------------------
@dispatcher.message(Command("profile"))
async def profile_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        first_name = user_data[2]
        last_name = user_data[3]
        age = user_data[4]
        notification_str = user_data[5]  # 'True' или 'False'

        # Преобразуем 'True'/'False' в более читабельный текст
        if notification_str == 'True':
            notif_status = "Включены"
        else:
            notif_status = "Выключены"

        await message.answer(
            f"Ваш профиль:\n"
            f"Имя: {first_name}\n"
            f"Фамилия: {last_name}\n"
            f"Возраст: {age}\n"
            f"Напоминания: {notif_status}"
        )
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
# ------------------------------------------------------------------------------
# Команда /faq
# ------------------------------------------------------------------------------
@dispatcher.message(Command("faq"))
async def faq_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('FAQ: Здесь будут часто задаваемые вопросы.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")

# ------------------------------------------------------------------------------
# Включение/выключение напоминаний
# ------------------------------------------------------------------------------
@dispatcher.message(Command("disable_reminders"))
async def disable_reminders_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
        return

    from database_modification import set_notifications_enabled
    await set_notifications_enabled(user_id, False)
    await message.answer("Вы отключили напоминания! Если захотите получать их снова, используйте /enable_reminders.")

@dispatcher.message(Command("enable_reminders"))
async def enable_reminders_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
        return

    from database_modification import set_notifications_enabled
    await set_notifications_enabled(user_id, True)
    await message.answer("Вы включили напоминания! Теперь вы снова будете их получать.")

# ------------------------------------------------------------------------------
# Тесты
# ------------------------------------------------------------------------------
test_sessions = {}

@dispatcher.message(Command("test"))
async def test_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте команду /start для регистрации.")
        return

    test_sessions[user_id] = {"step": 1}
    await message.answer("Введите тему, по которой хотите пройти тест:")

# ------------------------------------------------------------------------------
# Обработчик входящих сообщений (цепочка теста)
# ------------------------------------------------------------------------------
@dispatcher.message()
async def test_input_handler(message: types.Message):
    user_id = message.from_user.id

    # Если пользователь не в сессии теста, игнорируем
    if user_id not in test_sessions:
        return

    session = test_sessions[user_id]

    if session["step"] == 1:
        session["topic"] = message.text
        session["step"] = 2
        await message.answer("Какой у вас уровень знаний в этой теме? (начальный, средний, продвинутый)")

    elif session["step"] == 2:
        session["knowledge_level"] = message.text
        session["step"] = 3

        # Генерируем тест через GigaChat
        topic = session["topic"]
        knowledge_level = session["knowledge_level"]

        try:
            authorization_key = query_gigachat()  # Если нужно извлечь токен
            test_questions = await generate_test(
                'MjI2YzEzYWItODliMC00MTc0LTk0MWItNDMzZDBjZWVkNDUzOjAzMTIzNTAzLTE5YjAtNDY2Ni04NmNlLThiY2Q5ODg3ODIzMg==',
                topic,
                knowledge_level
            )
            await message.answer(f"Ваш тест:\n{test_questions}")
        except Exception as e:
            await message.answer("Ошибка при создании теста. Попробуйте позже.")
            logging.error(f"Error generating test: {e}")

        del test_sessions[user_id]  # Завершаем сессию теста

# ------------------------------------------------------------------------------
# Команда /career_guidance
# ------------------------------------------------------------------------------
@dispatcher.message(Command("career_guidance"))
async def career_guidance_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('Тест на профориентацию.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")

# ------------------------------------------------------------------------------
# Команда /exam
# ------------------------------------------------------------------------------
@dispatcher.message(Command("exam"))
async def exam_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('Подготовка к экзамену.')
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")

# ------------------------------------------------------------------------------
# Запуск бота
# ------------------------------------------------------------------------------
async def start_bot():
    await initialize_db()
    dispatcher.message.outer_middleware(SomeMiddleware())
    await dispatcher.start_polling(bot)