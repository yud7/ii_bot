import logging
import configparser

from typing import Callable, Awaitable, Any, Dict
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup
from database_modification import insert_test_result
from database_modification import get_user_statistics

from database_modification import (
    initialize_db,
    get_user_by_id,
    insert_user,
    update_last_activity,
    set_notifications_enabled,
    save_review_to_database
)

from gigachat_talking import (
    fetch_test,
    fetch_preparation,
    fetch_gigachat_response,
    generate_career_orientation_questions,
    analyze_answers
)

from test_module import (
    parse_test_response,
    send_question
)

from reminder import send_reminders

config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)
botToken = config.get('default', 'botToken')
authorizationKey = config.get('default', 'authorizationKey')
logging.basicConfig(level=logging.INFO)
bot = Bot(token=botToken)
dispatcher = Dispatcher()

test_sessions = {}
preparation_sessions = {}
guidance_sessions = {}
review_sessions = {}


keyboard_buttons_choice = [
    [
        types.InlineKeyboardButton(text='A', callback_data='answer_A'),
        types.InlineKeyboardButton(text='B', callback_data='answer_B'),
    ],
    [
        types.InlineKeyboardButton(text='C', callback_data='answer_C'),
        types.InlineKeyboardButton(text='D', callback_data='answer_D'),
    ]
]


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

            if user_data:
                await update_last_activity(user_id)

            if not hasattr(self, "registration_step"):
                self.registration_step = None

            if event.text == '/start':
                if user_data:
                    first_name, last_name = user_data[2], user_data[3]
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"{first_name} {last_name}, вы уже зарегистрированы!"
                    )
                else:
                    self.registration_step = 1
                    await bot.send_message(
                        chat_id=user_id,
                        text="Введите ваше имя:"
                    )
                return

            if self.registration_step:
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
                            await update_last_activity(user_id)
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

            if not user_data:
                await bot.send_message(
                    chat_id=user_id,
                    text="Вы не зарегистрированы! Пожалуйста, используйте команду /start для регистрации."
                )
                return

        return await handler(event, data)


@dispatcher.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if user_data:
        await message.answer(
            f'Привет, {message.from_user.last_name} {message.from_user.first_name}! '
            'Вы уже зарегистрированы!'
        )


@dispatcher.message(Command("help"))
async def help_command(message: types.Message):
    text = (
        "Ниже представлены все доступные команды:\n\n"
        "<b>/start</b> - Начать работу с ботом и зарегистрироваться\n"
        "<b>/help</b> - Просмотреть список всех команд и их описание\n"
        "<b>/faq</b> - Часто задаваемые вопросы для быстрого решения проблем\n"
        "<b>/test</b> - Пройти тестирование по выбранному предмету\n"
        "<b>/career_guidance</b> - Пройти тест на профориентацию\n"
        "<b>/preparation</b> - Подготовиться к экзамену с помощью учебных материалов\n"
        "<b>/review</b> - Оставить отзыв о работе бота\n"
        "<b>/enable_reminders</b> - Включить уведомления для напоминаний\n"
        "<b>/disable_reminders</b> - Отключить уведомления\n"
        "<b>/profile</b> - Посмотреть свою статистику и профиль\n"
    )
    await message.answer(text, parse_mode='HTML')


@dispatcher.message(Command("profile"))
async def profile_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if user_data:
        first_name = user_data[2]
        last_name = user_data[3]
        age = user_data[4]
        notification_str = user_data[5]
        notification_str = user_data[5]
        notif_status = "Включены" if notification_str == 'True' else "Выключены"

        user_statistics = await get_user_statistics(user_id)
        stats_text = "Статистика:\n"
        if user_statistics:
            for topic, correct, total, date in user_statistics[:5]:
                stats_text += f"- {topic} ({date.split('T')[0]}): {correct}/{total} правильных\n"
        else:
            stats_text += "Нет данных о пройденных тестах.\n"

        await message.answer(
            f"Ваш профиль:\n"
            f"Имя: {first_name}\n"
            f"Фамилия: {last_name}\n"
            f"Возраст: {age}\n"
            f"Напоминания: {notif_status}\n\n"
            f"{stats_text}"
        )
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")


@dispatcher.message(Command("faq"))
async def faq_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if user_data:
        faq_text = """
        <b>FAQ (Часто Задаваемые Вопросы)</b>

        1. <b>Как зарегистрироваться в боте?</b>
           Используйте команду <code>/start</code>. Если вы не зарегистрированы, бот начнет процесс регистрации.

        2. <b>Какие команды поддерживает бот?</b>
           - <code>/start</code> – Начало работы и регистрация.
           - <code>/help</code> – Список доступных команд.
           - <code>/profile</code> – Просмотр профиля.
           - <code>/test</code> – Прохождение теста.
           - <code>/career_guidance</code> – Тест на профориентацию.
           - <code>/preparation</code> – Подготовка к экзаменам.
           - <code>/faq</code> – Часто задаваемые вопросы.
           - <code>/disable_reminders</code> – Отключение напоминаний.
           - <code>/enable_reminders</code> – Включение напоминаний.

        3. <b>Как пройти тест?</b>
           Введите <code>/test</code>, выберите тему и уровень знаний, а затем отвечайте на вопросы.

        4. <b>Как работает тест на профориентацию?</b>
           Введите <code>/career_guidance</code> и ответьте на вопросы. Бот предложит подходящие профессии.

        5. <b>Как подготовиться к экзамену?</b>
           Введите <code>/preparation</code>, выберите тему и вопросы для объяснений.

        6. <b>Как посмотреть мою статистику?</b>
           Используйте <code>/profile</code>, чтобы увидеть свои данные и результаты тестов.

        7. <b>Как включить/отключить напоминания?</b>
           - Включение: <code>/enable_reminders</code>
           - Отключение: <code>/disable_reminders</code>

        8. <b>Как оставить отзыв?</b>
           После теста бот предложит поставить оценку и написать комментарий.

        9. <b>Что делать, если бот не отвечает?</b>
           Проверьте интернет, перезапустите бот командой <code>/start</code>. Если проблема сохраняется, обратитесь в поддержку.

        10. <b>Где хранятся мои данные?</b>
            Данные хранятся в защищенной базе и не передаются третьим лицам.
        """
        await message.answer(faq_text, parse_mode="HTML")
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")


@dispatcher.message(Command("disable_reminders"))
async def disable_reminders_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
        return

    await set_notifications_enabled(user_id, False)
    await message.answer("Вы отключили напоминания! Если захотите получать их снова, используйте /enable_reminders.")


@dispatcher.message(Command("enable_reminders"))
async def enable_reminders_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
        return

    await set_notifications_enabled(user_id, True)
    await message.answer("Вы включили напоминания! Теперь вы снова будете их получать.")


@dispatcher.message(Command("test"))
async def test_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте команду /start для регистрации.")
        return

    test_sessions[user_id] = {"step": 1}
    await message.answer("Введите тему, по которой хотите пройти тест:")


@dispatcher.callback_query(lambda call: call.data.startswith("answer_"))
async def handle_answer(call: types.CallbackQuery):
    user_id = call.from_user.id

    if user_id not in test_sessions:
        await call.answer("Тест не найден. Используйте /test для начала.")
        return

    session = test_sessions[user_id]
    current_question_num = session["current_question"]
    questions = session["questions"]

    user_answer = call.data.split("_")[1]
    session["user_answers"].append(user_answer)
    correct_answer_text = questions[current_question_num]["correct_answer"]
    if questions[current_question_num]["options"][user_answer] == correct_answer_text:
        session["correct_answers"] += 1

    if current_question_num < len(questions) - 1:
        session["current_question"] += 1
        await send_question(call.message, session)
    else:
        correct_answers = session["correct_answers"]
        total_questions = len(questions)
        topic = session["topic"]

        await insert_test_result(user_id, topic, correct_answers, total_questions)

        await call.message.answer(
            f"Тест завершён! Вы ответили правильно на {correct_answers} из {total_questions} вопросов."
        )
        del test_sessions[user_id]


async def send_question(message: types.Message, session: dict):
    current_question_num = session["current_question"]
    question_data = session["questions"][current_question_num]

    question_text = f"Вопрос {current_question_num}:\n{question_data['question']}\n\n"
    for key, option in question_data["options"].items():
        question_text += f"{key}) {option}\n"

    inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons_choice)

    await message.answer(question_text.strip(), reply_markup=inline_keyboard, parse_mode="HTML")


@dispatcher.message(Command("preparation"))
async def preparation_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте команду /start для регистрации.")
        return

    preparation_sessions[user_id] = {"step": 1}
    await message.answer("Введите тему, по которой хотите подготовиться:")


@dispatcher.message(Command("career_guidance"))
async def career_guidance_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)
    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте команду /start для регистрации.")
        return

    guidance_sessions[user_id] = {
        "step": 1,
        "user_answers": [],
        "questions": []
    }

    await message.answer("Добро пожаловать в тест на профориентацию! Вы готовы начать? (Напишите 'Да' для начала)")


@dispatcher.message(Command("review"))
async def preparation_command(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_by_id(user_id)

    if not user_data:
        await message.answer("Вы не зарегистрированы. Используйте команду /start для регистрации.")
        return

    review_sessions[user_id] = {"step": 1}
    keyboard_rating = [
        [
            types.InlineKeyboardButton(text='1', callback_data='rating_1'),
            types.InlineKeyboardButton(text='2', callback_data='rating_2'),
        ],
        [
            types.InlineKeyboardButton(text='3', callback_data='rating_3'),
            types.InlineKeyboardButton(text='4', callback_data='rating_4'),
        ],
        [
            types.InlineKeyboardButton(text='5', callback_data='rating_5'),
        ]
    ]
    review_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rating)
    await message.answer("Какое ваше общее впечатление от работы бота по шкале от 1 до 5?", reply_markup=review_keyboard)


@dispatcher.callback_query(lambda c: c.data.startswith("rating_"))
async def handle_rating(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in review_sessions:
        session = review_sessions[user_id]
        if session["step"] == 1:
            rating = int(callback_query.data.split("_")[1])
            session["rating"] = rating
            session["step"] = 2
            await callback_query.message.edit_text("Опишите, что вам понравилось в работе бота.")
        else:
            await callback_query.answer("Ответ уже принят.")

    await callback_query.answer()


@dispatcher.message()
async def unified_input_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id in test_sessions:
        session = test_sessions[user_id]

        if session["step"] == 1:
            session["topic"] = message.text
            session["step"] = 2
            await message.answer("Какой у вас уровень знаний в этой теме? (начальный, средний, продвинутый)")

        elif session["step"] == 2:
            session["knowledge_level"] = message.text
            session["step"] = 3
            topic = session["topic"]
            knowledge_level = session["knowledge_level"]

            try:
                response = fetch_test(authorizationKey, topic, knowledge_level)
                questions = parse_test_response(response)
                session["questions"] = questions
                session["current_question"] = 1
                session["user_answers"] = []
                session["correct_answers"] = 0

                await send_question(message, session)
            except Exception as e:
                await message.answer("Ошибка при создании теста. Попробуйте позже.")
                logging.error(f"Error generating test: {e}")
                del test_sessions[user_id]

    elif user_id in preparation_sessions:
        session = preparation_sessions[user_id]

        if session["step"] == 1:
            session["topic"] = message.text
            session["step"] = 2
            await message.answer("Какой у вас уровень знаний в этой теме? (начальный, средний, продвинутый)")

        elif session["step"] == 2:
            session["knowledge_level"] = message.text
            session["step"] = 3
            topic = session["topic"]
            knowledge_level = session["knowledge_level"]

            try:
                questions = fetch_preparation(authorizationKey, topic, knowledge_level)
                session["questions"] = questions
                session["selected_questions"] = []
                session["step"] = 4

                question_list = "\n".join([f"{q}" for i, q in enumerate(questions)])
                await message.answer(
                    f"Вот список вопросов по теме '{topic}':\n\n{question_list}\n\n"
                    "Введите номера вопросов, которые вы хотите разобрать, через запятую."
                )
            except Exception as e:
                await message.answer("Ошибка при создании подготовки. Попробуйте позже.")
                logging.error(f"Error generating preparation: {e}")
                del preparation_sessions[user_id]

        elif session["step"] == 4:
            try:
                selected_indices = [int(idx.strip()) for idx in message.text.split(",")]
                session["selected_questions"] = selected_indices
                session["current_index"] = 0
                session["step"] = 5

                await send_explanation(message, session)
            except ValueError:
                await message.answer("Ошибка ввода. Укажите номера вопросов через запятую (например: 1, 3, 5).")

    elif user_id in guidance_sessions:
        session = guidance_sessions[user_id]
        if session["step"] == 1:
            if message.text.strip().lower() == "да":
                try:
                    authorization_key = authorizationKey
                    session["questions"] = generate_career_orientation_questions(authorization_key)
                    session["step"] = 2
                    session["current_question"] = 0
                    print('fewfwefewfwefwe')
                    await send_question_guidance(message, session)
                except Exception as e:
                    await message.answer("Ошибка при генерации вопросов. Попробуйте позже.")
                    logging.error(f"Error generating career test: {e}")
                    del guidance_sessions[user_id]
            else:
                await message.answer("Введите 'Да', чтобы начать тест.")

        elif session["step"] == 2:
            try:
                session["user_answers"].append(message.text.strip())
                session["current_question"] += 1
                if session["current_question"] < len(session["questions"]):
                    await send_question_guidance(message, session)
                else:
                    await message.answer("Спасибо за прохождение теста! Анализируем ваши ответы...")
                    try:
                        analysis_result = analyze_answers(session["user_answers"], authorizationKey)
                        await message.answer(f"Результат анализа: {analysis_result}")
                    except Exception as e:
                        await message.answer("Ошибка при анализе ваших ответов. Попробуйте позже.")
                        logging.error(f"Error analyzing answers: {e}")

                    # Завершение сессии
                    del guidance_sessions[user_id]
            except Exception as e:
                await message.answer("Произошла ошибка. Попробуйте позже.")
                logging.error(f"Error during test session: {e}")

    elif user_id in review_sessions:
        session = review_sessions[user_id]

        if session["step"] == 2:
            session["positive_feedback"] = message.text
            session["step"] = 3
            await message.answer("Опишите, что можно улучшить в работе бота.")

        elif session["step"] == 3:
            session["negative_feedback"] = message.text
            # Сохранение данных в базу или логи
            try:
                await save_review_to_database(
                    user_id=user_id,
                    rating=session["rating"],
                    positive_feedback=session["positive_feedback"],
                    negative_feedback=session["negative_feedback"],
                )
                await message.answer("Ваш отзыв сохранен. Спасибо за помощь в улучшении бота!")
            except Exception as e:
                await message.answer("Произошла ошибка при сохранении отзыва. Попробуйте позже.")
                logging.error(f"Error saving review: {e}")
            finally:
                del review_sessions[user_id]
    else:
        await message.answer("Команда не распознана! Введите /help и посмотрите весь список доступных команд")
        return


async def send_explanation(message: types.Message, session: dict):
    """Отправка пояснений по выбранным вопросам."""
    questions = session["questions"]
    selected_indices = session["selected_questions"]
    current_index = session["current_index"]

    if current_index >= len(selected_indices):
        await message.answer("Объяснения завершены. Удачи в подготовке!")
        del preparation_sessions[message.from_user.id]
        return

    question_num = selected_indices[current_index]
    if question_num <= 0 or question_num > len(questions):
        await message.answer(f"Пропущен вопрос с номером {question_num} (он отсутствует в списке).")
        session["current_index"] += 1
        await send_explanation(message, session)
        return

    question_text = questions[question_num - 1]
    explanation_prompt = (
        f"Объясни подробно следующий вопрос:\n"
        f"{question_text}\n"
        f"Дай логическое объяснение и полезную информацию, чтобы стало понятно."
    )

    response = ""
    attempt = 0
    max_attempts = 5

    while len(response) == 0 or len(response) > 4096:
        try:
            response = fetch_gigachat_response(authorizationKey, explanation_prompt)
            if len(response) <= 4096:
                break
            attempt += 1
            explanation_prompt = (
                f"Ответ слишком длинный. Дай краткое, но логическое и ясное объяснение:\n{question_text}"
            )
        except Exception as e:
            logging.error(f"Ошибка получения ответа: {e}")
            attempt += 1

        if attempt >= max_attempts:
            await message.answer("Не удалось получить корректное объяснение. Попробуйте позже.")
            return

    session["current_index"] += 1
    keyboard_buttons = [
        types.InlineKeyboardButton(text="Далее", callback_data="next_question"),
        types.InlineKeyboardButton(text="Стоп", callback_data="stop_preparation")
    ],

    inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(f"Вопрос {question_num}:\n{question_text}\n\nПояснение:\n{response}", parse_mode="HTML",
                         reply_markup=inline_keyboard)


@dispatcher.callback_query(lambda call: call.data == "next_question")
async def handle_next_question(call: types.CallbackQuery):
    """Обработка кнопки 'Далее'."""
    user_id = call.from_user.id
    if user_id not in preparation_sessions:
        await call.answer("Вы не находитесь в режиме подготовки. Используйте команду /preparation.")
        return

    session = preparation_sessions[user_id]
    await send_explanation(call.message, session)


@dispatcher.callback_query(lambda call: call.data == "stop_preparation")
async def handle_stop_preparation(call: types.CallbackQuery):
    """Обработка кнопки 'Стоп'."""
    user_id = call.from_user.id
    if user_id in preparation_sessions:
        del preparation_sessions[user_id]
    await call.message.answer("Вы завершили подготовку. Удачи!")


async def send_question_guidance(message: types.Message, session):
    question_index = session["current_question"]
    question = session["questions"][question_index]
    await message.answer(f"Вопрос {question_index + 1}: {question}")


async def start_bot():
    await initialize_db()
    dispatcher.message.outer_middleware(SomeMiddleware())
    await dispatcher.start_polling(bot)
