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


async def start_bot():
    await dispatcher.start_polling(bot)