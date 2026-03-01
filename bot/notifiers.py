import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User, Event, EventsAttendance
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import get_settings

cfg = get_settings()
bot_token = cfg.bot_token
# If API is running, we can just instantiate a bot to send messages
_bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) if bot_token else None

from db.base import get_session

async def notify_new_event(event_id: int):
    async with get_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            return
            
        stmt = select(User.telegram_id).where(User.privacy_level < 2, User.status == "approved")
        from db.models import UserProgress
        stmt = (
            select(User.telegram_id)
            .join(UserProgress, User.telegram_id == UserProgress.user_id)
            .where(User.status == "approved", UserProgress.current_level >= event.min_level)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        date_str = event.event_date.strftime("%d.%m.%Y %H:%M") if event.event_date else "Скоро"
        title = event.title
        desc = event.description or ''
        
    text = (
        f"🌟 <b>Новое мероприятие!</b>\n\n"
        f"<b>{title}</b> — {date_str}\n"
        f"<i>{desc}</i>\n\n"
        "Зайди в раздел /events, чтобы записаться!"
    )
    for u in users:
        try:
            if _bot:
                await _bot.send_message(u, text, parse_mode="HTML")
        except Exception:
            pass

async def notify_event_update(event_id: int, changes_desc: str):
    async with get_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            return
            
        stmt = select(EventsAttendance.user_id).where(EventsAttendance.event_id == event.id)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        date_str = event.event_date.strftime("%d.%m.%Y %H:%M") if event.event_date else "Скоро"
        title = event.title
        
    text = (
        f"⚠️ <b>Внимание: изменения в мероприятии!</b>\n\n"
        f"<b>{title}</b> ({date_str})\n"
        f"<i>Что изменилось: {changes_desc}</i>"
    )
    for u in users:
        try:
            if _bot:
                await _bot.send_message(u, text, parse_mode="HTML")
        except Exception:
            pass

