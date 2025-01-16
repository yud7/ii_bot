import logging
import configparser

from typing import Callable, Awaitable, Any, Dict
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from database_modification import initialize_db, get_user_by_id, insert_user, update_last_activity

config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()


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

            if not hasattr(self, "registration_step"):
                self.registration_step = None

            if event.text == '/start':
                if user_data:
                    # User already registered
                    first_name, last_name = user_data[2], user_data[3]
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"{first_name} {last_name}, вы уже зарегистрированы!"
                    )
                else:

                    self.registration_step = 1
                    await bot.send_message(chat_id=user_id, text="Введите ваше имя:")
                return

            if self.registration_step:
                # Handle the registration steps
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
                            await bot.send_message(chat_id=user_id, text="Регистрация завершена!")
                            self.registration_step = None
                        else:
                            await bot.send_message(chat_id=user_id, text="Пожалуйста, введите возраст от 1 до 120.")
                    except ValueError:
                        await bot.send_message(chat_id=user_id, text="Введите корректный возраст.")
                    return
                return

            if not user_data:
                # User is not registered
                await bot.send_message(
                    chat_id=user_id,
                    text="Вы не зарегистрированы! Пожалуйста, используйте команду /start для регистрации."
                )
            # TODO закончить реакцию на сообщение пользователя, если ни одна из команд не находится в обработке

            # else:
            #     # User exists; redirect to /help for unrecognized commands
            #     await bot.send_message(
            #         chat_id=user_id,
            #         text="Команда не распознана. Для списка доступных команд используйте /help."
            #     )
            #     return

        # Pass the event to the next middleware or handler
        return await handler(event, data)


@dispatcher.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if user_data:
        await message.answer(
            f'Привет, {message.from_user.last_name} {message.from_user.first_name}! Вы уже зарегистрированы!'
        )

# TODO переделать реакцию на новое сообщение (в нынешнем виде даже на команду выдаётся только текст, что таймер обновлён)
# @dispatcher.message()
# async def any_message_handler(message: types.Message):
#     user_id = message.from_user.id
#     user_data = await get_user_by_id(user_id)
#     if user_data:
#         await update_last_activity(user_id)
#         await message.answer("Сообщение получено, активность обновлена.")


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
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer(
            f"Ваш профиль: {message.from_user.last_name} {message.from_user.first_name}"
        )


@dispatcher.message(Command("faq"))
async def faq_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('FAQ: Здесь будут часто задаваемые вопросы.')


@dispatcher.message(Command("test"))
async def test_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('Проверка знаний.')


@dispatcher.message(Command("career_guidance"))
async def career_guidance_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('Тест на профориентацию.')


@dispatcher.message(Command("exam"))
async def exam_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if user_data:
        await message.answer('Подготовка к экзамену.')


async def start_bot():
    await initialize_db()
    dispatcher.message.outer_middleware(SomeMiddleware())
    await dispatcher.start_polling(bot)
