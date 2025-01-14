import configparser
import aiogram


config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)

botToken = config.get('default', 'botToken')


import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage  # или RedisStorage, если нужна внешняя БД для состояний
from aiogram.utils.callback_data import CallbackData

# Импорт модулей
from handlers.chat import router as chat_router
from handlers.faq import router as faq_router
from handlers.registration import router as registration_router
from utils.scheduler import setup_scheduler
from middlewares.token_middleware import TokenMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация бота
TOKEN = botToken
bot = Bot(token=TOKEN, parse_mode="HTML")  # parse_mode позволяет использовать HTML-разметку
dp = Dispatcher(storage=MemoryStorage())  # FSM-хранилище в оперативной памяти

# CallbackData для inline-кнопок (пример)
callback_data_example = CallbackData("action", "value")


# Функция настройки командного меню
async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Запуск бота"),
        BotCommand(command="/chat", description="Задать вопрос GigaChat"),
        BotCommand(command="/faq", description="Часто задаваемые вопросы"),
        BotCommand(command="/test", description="Тест на профориентацию"),
    ]
    await bot.set_my_commands(commands)


# Основная функция
async def main():
    # Регистрация middleware
    dp.message.middleware(TokenMiddleware())

    # Регистрация маршрутов
    dp.include_router(chat_router)
    dp.include_router(faq_router)
    dp.include_router(registration_router)

    # Настройка периодических задач
    setup_scheduler(bot)

    # Настройка командного меню
    await set_bot_commands()

    # Запуск бота
    try:
        logging.info("Бот запущен!")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")


# Запуск asyncio
if __name__ == "__main__":
    asyncio.run(main())

