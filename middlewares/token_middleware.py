from aiogram.types import Message
from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

class TokenMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Вы можете добавить логику проверки или обновления токена, если нужно
        return await handler(event, data)
