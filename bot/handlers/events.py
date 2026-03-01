import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, func
from db.base import get_session
from db.models import Event, EventsAttendance, User, UserProgress
from core.gamification import award_xp

from bot.keyboards import NavCB, EventActionCB, events_keyboard
from bot.keyboards.main import event_details_keyboard

router = Router(name="events")
logger = logging.getLogger(__name__)

EVENTS_PER_PAGE = 5

def _build_text(events: list[dict], registered: set[int]) -> str:
    lines = ["📅 <b>Мероприятия для тебя</b>\n"]
    for e in events:
        mark = "✅" if e["id"] in registered else "📌"
        date_str = e["date"].strftime("%d.%m.%Y %H:%M") if e.get("date") else "Без времени"
        lines.append(f"{mark} <b>{e['title']}</b> — {date_str}")
        if e.get("description"):
            lines.append(f"  <i>{e['description']}</i>")
            
    lines.append("\nНажми, чтобы записаться / отменить:")
    return "\n".join(lines)


async def _show(target, page: int = 0) -> None:
    user_id = target.from_user.id
    
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            # Need registration first
            return
            
        # Get count to see if we have next page
        total_events = await session.scalar(select(func.count(Event.id)))
        
        # Fetch events matching user level? Or all events? Let's show all for now, or filter by min_level
        stmt = select(Event).order_by(Event.event_date.desc()).offset(page * EVENTS_PER_PAGE).limit(EVENTS_PER_PAGE)
        result = await session.execute(stmt)
        events_db = result.scalars().all()
        
        # Fetch registrations
        reg_stmt = select(EventsAttendance.event_id).where(EventsAttendance.user_id == user_id)
        reg_result = await session.execute(reg_stmt)
        registered = set(reg_result.scalars().all())

    events = []
    for edb in events_db:
        events.append({
            "id": edb.id,
            "title": edb.title,
            "description": edb.description,
            "date": edb.event_date,
            "min_level": edb.min_level
        })

    has_next = (page + 1) * EVENTS_PER_PAGE < total_events

    if not events:
        text = "📅 Пока нет доступных мероприятий."
        kb   = events_keyboard([], set())
    else:
        text = _build_text(events, registered)
        kb   = events_keyboard(events, registered, page=page, has_next=has_next)

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("events"))
async def cmd_events(message: Message) -> None:
    await _show(message)


@router.callback_query(NavCB.filter(F.page == "events"))
async def nav_events(call: CallbackQuery, callback_data: NavCB) -> None:
    await _show(call, page=callback_data.subpage)


@router.callback_query(EventActionCB.filter(F.action == "view"))
async def process_event_view(call: CallbackQuery, callback_data: EventActionCB) -> None:
    event_id = callback_data.event_id
    user_id = call.from_user.id
    
    async with get_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            await call.answer("Мероприятие не найдено", show_alert=True)
            return
            
        reg_stmt = select(EventsAttendance).where(
            EventsAttendance.user_id == user_id,
            EventsAttendance.event_id == event_id
        )
        res = await session.execute(reg_stmt)
        registered = res.scalar_one_or_none() is not None

    date_str = event.event_date.strftime("%d.%m.%Y %H:%M") if event.event_date else "Скоро"
    text = (
        f"📅 <b>{event.title}</b>\n\n"
        f"🕒 Время: {date_str}\n"
        f"📈 Мин. уровень: {event.min_level}\n\n"
        f"<i>{event.description or 'Нет описания'}</i>"
    )
    await call.message.edit_text(text, reply_markup=event_details_keyboard(event_id, registered), parse_mode="HTML")
    await call.answer()


@router.callback_query(EventActionCB.filter(F.action.in_(["register", "unregister"])))
async def process_event_action(call: CallbackQuery, callback_data: EventActionCB) -> None:
    user_id = call.from_user.id
    event_id = callback_data.event_id
    action = callback_data.action
    
    try:
        async with get_session() as session:
            # Check user level requirements first
            user = await session.get(User, user_id)
            event = await session.get(Event, event_id)
            
            if not user or not event:
                await call.answer("Возникла ошибка: не найдено", show_alert=True)
                return
            
            prog = await session.scalar(select(UserProgress).where(UserProgress.user_id == user_id))
            current_level = prog.current_level if prog else 1
            
            if action == "register":
                if current_level < event.min_level:
                    await call.answer(f"🔒 Это мероприятие от {event.min_level} уровня (у тебя {current_level})", show_alert=True)
                    return
                    
                attendance = EventsAttendance(user_id=user_id, event_id=event_id)
                session.add(attendance)
                # optionally award XP
                await award_xp(user_id, "register_event", session)
                await session.commit()
                await call.answer("✅ Записан на мероприятие!")
            else:
                stmt = select(EventsAttendance).where(
                    EventsAttendance.user_id == user_id,
                    EventsAttendance.event_id == event_id
                )
                res = await session.execute(stmt)
                att = res.scalar_one_or_none()
                if att:
                    await session.delete(att)
                    await session.commit()
                await call.answer("❌ Запись отменена.")
    except Exception as e:
        logger.exception("Event action failed")
        await call.answer("Возникла ошибка", show_alert=True)
        return

    # Return to details view
    await process_event_view(call, EventActionCB(action="view", event_id=event_id))
