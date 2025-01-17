from token_updater import query_gigachat

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat as Gigachat


def fetch_test(authorization_key: str, user_request: str, knowledge_level: str):
    """
    Получить список вопросов и правильных ответов на тему user_request.
    """
    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.SYSTEM,
                content=(
                    f"Ты профессор. Составь тест по теме '{user_request}', состоящий из ДЕСЯТИ вопросов с выбором из четырёх вариантов ответа. "
                    f"Один из вариантов всегда правильный. Уровень знаний пользователя: {knowledge_level}.\n\n"
                    f"Ответы должны быть строго структурированы в следующем формате:\n"
                    f"Вопрос 1:\n"
                    f"текст вопроса"
                    f"Варианты:\n"
                    f"A) [вариант A]\n"
                    f"B) [вариант B]\n"
                    f"C) [вариант C]\n"
                    f"D) [вариант D]\n"
                    f"Правильный ответ:\n\n"
                    f"буква и текст правильного ответа"
                    f"Вопрос 2:\n"
                    f"текст вопроса"
                    f"Варианты:\n"
                    f"A) [вариант A]\n"
                    f"B) [вариант B]\n"
                    f"C) [вариант C]\n"
                    f"D) [вариант D]\n"
                    f"Правильный ответ:\n\n"
                    f"буква и текст правильного ответа"
                    f"Не добавляй никаких пояснений, заголовков, комментариев или вводных слов. Только список вопросов и вариантов ответа в указанном формате."
                )
            )
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    with GigaChat(credentials=authorization_key, verify_ssl_certs=False) as giga_chat:
        response = giga_chat.chat(payload)
        print(response.choices[0].message.content)
        return response.choices[0].message.content


def evaluate_answer(authorization_key, question, answer):
    """
    Sends the user's answer to GigaChat for evaluation.
    """
    prompt = f"Вопрос: {question}\nОтвет: {answer}\nПравильно ли это? Ответь 'да' или 'нет'."
    payload = Chat(
        messages=[Messages(role=MessagesRole.SYSTEM, content=prompt)],
        temperature=1.0,
        max_tokens=50,
    )
    with GigaChat(credentials=authorization_key, verify_ssl_certs=False) as giga_chat:
        response = giga_chat.chat(payload)
        return {"is_correct": "да" in response.choices[0].message.content.lower()}
