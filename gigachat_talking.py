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


def generate_career_orientation_questions(authorization_key: str):
    """
    Генерирует 20 вопросов для профориентационного теста с использованием LLM.

    :param authorization_key: Ключ авторизации для API языковой модели.
    :return: Список из 20 вопросов в текстовом формате.
    """
    # Формируем payload для LLM
    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.SYSTEM,
                content=(
                    "Составь тест максимум из 10 вопросов по профориентации. Все вопросы должны быть открытыми и побуждать человека "
                    "развернуто отвечать. Не добавляй варианты ответов или комментарии. Вопросы должны быть такеие, чтобы по окончании ответов на 1- вопросов, можно было посоветовать человеку подходящую профессию. Пример вопроса: "
                    "'Какие виды деятельности приносят вам наибольшее удовольствие и почему?'"
                )
            )
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    # Отправляем запрос к LLM
    with GigaChat(credentials=authorization_key, verify_ssl_certs=False) as giga_chat:
        response = giga_chat.chat(payload)

    # Получаем текст ответа и разделяем его на вопросы
    questions = response.choices[0].message.content.strip().split("\n")

    # Возвращаем список вопросов
    q = [question.strip() for question in questions if question.strip()][1:]
    print(q)
    return q


def analyze_answers(answers, authorization_key):
    """
    Анализирует ответы пользователя с использованием модели LLM.

    :param answers: Список ответов пользователя.
    :return: Результат анализа в текстовом формате.
    :authorization_key: ключ для апи.
    """
    try:

        payload = Chat(
            messages=[
                Messages(
                    role=MessagesRole.SYSTEM,
                    content=(
                                "Ты эксперт по профориентации. Проанализируй ответы пользователя и предложи подходящие карьерные направления. "
                                "Ответы пользователя:") + "\n" + "\n".join(answers)
                )
            ],
            temperature=0.7,
            max_tokens=500,
        )

        with GigaChat(credentials=authorization_key, verify_ssl_certs=False) as giga_chat:
            response = giga_chat.chat(payload)
            return response.choices[0].message.content.strip()
    except Exception as e:
        return "Не удалось проанализировать ваши ответы. Попробуйте позже."
