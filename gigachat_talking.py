from token_updater import query_gigachat

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat as Gigachat


def fetch_test(authorization_key: str, user_request: str, knowledge_level: str):
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
                    f"Не используй математические формулы и специальные символы. Заменяй их на обычные латинские буквы."
                    f"Описывай все математические выражения как обычный текст. Пример: f(x) = 2x + 2"
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


def fetch_preparation(authorization_key: str, topic: str, knowledge_level: str) -> list[str]:
    llm = Gigachat(
        credentials=authorization_key,
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        verify_ssl_certs=False,
        streaming=True,
    )

    prompt_template = (
        f"Ты профессор. Составь список вопросов по теме '{topic}'. "
        f"Они должны быть полезны для подготовки студента с уровнем знаний: {knowledge_level}. "
        f"Список должен быть строго структурирован:\n"
        f"1. Вопрос 1\n"
        f"2. Вопрос 2\n"
        f"3. Вопрос 3\n"
        f"и так далее. Не добавляй никаких комментариев."
    )

    messages = [
        SystemMessage(content="Ты помощник для подготовки к экзаменам."),
        HumanMessage(content=prompt_template),
    ]

    res = llm.invoke(messages)
    messages.append(res)
    questions = res.content.split("\n")

    return [q for q in questions]


def fetch_gigachat_response(authorization_key: str, question_text: str) -> str:
    llm = Gigachat(
        credentials=authorization_key,
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        verify_ssl_certs=False,
        streaming=True,
    )
    prompt = (
        f"СТРОГОЕ ОГРАНИЧЕНИЕ: Сообщение должно содержать не более 2000 символов (включая пробелы, табуляции и пустые строки)."
        f"Объясни следующий вопрос:\n"
        f"{question_text}\n"
        f"Дай логическое объяснение и полезную информацию, чтобы пользователь понял его смысл."
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
