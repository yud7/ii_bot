import re
from aiogram import types


def parse_test_response(response_text: str) -> dict:
    # Код парсинга из предыдущего ответа
    lines = response_text.strip().split('\n')
    questions = {}
    current_question = {}
    question_number = 0
    for i, line in enumerate(lines):
        if line.startswith("**Вопрос"):
            if current_question:
                questions[question_number] = current_question
            question_number += 1
            current_question = {"question": lines[i + 1].strip(), "options": {}}
        elif re.match(r"(A|B|C|D)\)\s(.+)", line):
            key, text = re.match(r"(A|B|C|D)\)\s(.+)", line).groups()
            current_question["options"][key] = text.strip()
        elif line.startswith("**Правильный ответ:"):
            _, correct_text = re.match(r"(A|B|C|D)\)\s(.+)", lines[i + 1]).groups()
            current_question["correct_answer"] = correct_text.strip()
    if current_question:
        questions[question_number] = current_question
    return questions


async def send_question(message: types.Message, session: dict):
    current_question_num = session["current_question"] - 1
    question_data = session["questions"][current_question_num]

    question_text = f"Вопрос {current_question_num + 1}:\n{question_data['question']}\n\n"
    question_text += "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(question_data["options"])])

    keyboard_buttons = [
        [types.InlineKeyboardButton(text=chr(65+i), callback_data=f"answer_{chr(65+i)}")]
        for i in range(len(question_data["options"]))
    ]
    inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(question_text, reply_markup=inline_keyboard)


async def finalize_preparation(message: types.Message, session: dict):
    correct_answers = sum(1 for ans in session["answers"] if ans["user_answer"] == ans["correct"])
    total_questions = len(session["questions"])

    await message.answer(
        f"Подготовка завершена! Вы ответили правильно на {correct_answers} из {total_questions} вопросов."
    )
