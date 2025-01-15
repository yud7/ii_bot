import asyncio
import logging
from aiogram import Bot, Dispatcher,types
from aiogram.filters.command import Command
import configparser

config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()


@dispatcher.message(Command('start'))
async def start(message: types.Message):
    await message.answer('hey')


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


@dispatcher.message(Command('faq'))
async def faq(message: types.Message):
    await message.answer('....')


@dispatcher.message(Command('test'))        #проверка знаний
async def start(message: types.Message):
    await message.answer('проверка знаний')


@dispatcher.message(Command('career_guidance'))       #тест на проф ориентацию
async def career_guidance(message: types.Message):
    await message.answer('тест на проф ориентацию')


@dispatcher.message(Command('profile'))           #управление профилем
async def profile(message: types.Message):
    await message.answer('профиль')


@dispatcher.message(Command('exam'))           #подготовка к экзамену
async def profile(message: types.Message):
    await message.answer('подготовка к экзамену')


async def start_bot():
    await dispatcher.start_polling(bot)