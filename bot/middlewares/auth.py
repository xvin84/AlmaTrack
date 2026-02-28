from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from db.base import get_session
from db.crud import get_user

class PendingUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Only process messages and callback queries
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user_id = event.from_user.id
        
        # Check if the text is /start
        is_start = False
        if isinstance(event, Message) and event.text and event.text.startswith('/start'):
            is_start = True

        async with get_session() as session:
            user = await get_user(user_id, session)

        if user and user.status == "pending" and not is_start:
            # Check if callback
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ Ваша заявка всё ещё на проверке. Ожидайте!", show_alert=True)
            else:
                await event.answer("⏳ <i>Твоя анкета находится на проверке у администратора. Полный функционал будет доступен после одобрения.</i>", parse_mode="HTML")
            return

        return await handler(event, data)
