from token_updater import query_gigachat

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat as Gigachat


def chat_with_without_history(authorization_key: str, case_sensitive: int):
    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.SYSTEM,
                content="Ты - руководитель группой по разработке плана реализации мебельного магазина"
            )
        ],
        temperature=1.7,
        max_tokens=100,
    )
    print("Введите 'конец диалога' для завершения диалога")

    with GigaChat(credentials=authorization_key, verify_ssl_certs=False) as giga_chat:
        while True:
            text_to_giga_chat = input("Ваше сообщение\n")
            if text_to_giga_chat == "конец диалога":
                break
            payload.messages.append(Messages(role=MessagesRole.USER, content=text_to_giga_chat))
            response = giga_chat.chat(payload)
            if case_sensitive:
                payload.messages.append(response.choices[0].message)
            print("Bot\n", response.choices[0].message.content)


def chat_langchain_gigachat(authorization_key_user: str, case_sensitive: int):
    llm = Gigachat(
        credentials=authorization_key_user,
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        verify_ssl_certs=False,
        streaming=True,
    )

    messages = [
        SystemMessage(
            content="Ты - руководитель группой по разработке плана реализации мебельного магазина и можешь ответить на любой вопрос пользователя"
        )
    ]
    print("Введите 'конец диалога' для завершения диалога")
    while True:
        text_to_giga_chat = input("Ваше сообщение\n")
        if text_to_giga_chat == "конец диалога":
            break
        if case_sensitive:
            messages.append(HumanMessage(content=text_to_giga_chat))
            res = llm.invoke(messages)
            messages.append(res)
        else:
            messages = [HumanMessage(content=text_to_giga_chat)]
            res = llm.invoke(messages)
        print("GigaChat\n", res.content)


async def generate_test(authorization_key: str, user_request: str, knowledge_level: str):
    prompt = (
        f"Ты профессор. Составь тест по теме '{user_request}', "
        f"состоящий из 10-15 вопросов. Уровень знаний пользователя: {knowledge_level}."
    )

    payload = Chat(
        messages=[Messages(role=MessagesRole.SYSTEM, content=prompt)],
        temperature=1.2,
        max_tokens=500
    )

    async with GigaChat(credentials=authorization_key, verify_ssl_certs=False) as giga_chat:
        response = await giga_chat.chat(payload)
        return response.choices[0].message.content
