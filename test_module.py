import re


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
