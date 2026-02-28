"""Events screen."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, EventActionCB, events_keyboard

router = Router(name="events")

# Placeholder events — TODO: fetch from DB
_MOCK_EVENTS = [
    {"id": 1, "title": "Карьерная встреча — Яндекс", "date": "15 марта"},
    {"id": 2, "title": "Лекция: жизнь после вуза",   "date": "20 марта"},
]


def _build_text(events: list[dict], registered: set[int]) -> str:
    lines = ["📅 <b>Мероприятия для тебя</b>\n"]
    for e in events:
        mark = "✅" if e["id"] in registered else "📌"
        lines.append(f"{mark} <b>{e['title']}</b> — {e['date']}")
    lines.append("\nНажми, чтобы записаться / отменить:")
    return "\n".join(lines)


async def _show(target, events=None, registered=None) -> None:
    if events is None:
        events = _MOCK_EVENTS          # TODO: fetch from DB
    if registered is None:
        registered = set()             # TODO: fetch from DB

    if not events:
        text = "📅 Пока нет доступных мероприятий."
        kb   = events_keyboard([], set())
    else:
        text = _build_text(events, registered)
        kb   = events_keyboard(events, registered)

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
async def nav_events(call: CallbackQuery) -> None:
    await _show(call)


@router.callback_query(EventActionCB.filter())
async def process_event_action(call: CallbackQuery, callback_data: EventActionCB) -> None:
    if callback_data.action == "register":
        # TODO: save to DB
        await call.answer("✅ Записан на мероприятие!")
    else:
        # TODO: delete from DB
        await call.answer("❌ Запись отменена.")
    # TODO: refresh keyboard with updated registration state
