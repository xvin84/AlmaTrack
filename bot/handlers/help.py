"""Help screen + home NavCB handler."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, home_keyboard, help_keyboard

router = Router(name="help")

HELP_TEXT = (
    "❓ <b>Справка AlmaTrack</b>\n\n"
    "Навигация через кнопки — без лишних команд.\n\n"
    "<b>Команды:</b>\n"
    "/start — регистрация или перезапуск\n"
    "/profile — карточка профиля\n"
    "/stats — статистика по факультету\n"
    "/achievements — достижения и бейджи\n"
    "/events — мероприятия университета\n"
    "/privacy — настройки приватности\n"
    "/help — эта справка\n\n"
    "🔒 Твои личные данные надёжно защищены.\n"
    "Вуз видит только обезличенную аналитику."
)


async def _show(target) -> None:
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(HELP_TEXT, reply_markup=help_keyboard(), parse_mode="HTML")
        except Exception:
            await target.message.answer(HELP_TEXT, reply_markup=help_keyboard(), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(HELP_TEXT, reply_markup=help_keyboard(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await _show(message)


@router.callback_query(NavCB.filter(F.page == "help"))
async def nav_help(call: CallbackQuery) -> None:
    await _show(call)


# ---------------------------------------------------------------------------
# Home — "← Главная" button returns here
# ---------------------------------------------------------------------------

HOME_TEXT = (
    "🏠 <b>AlmaTrack</b> — карьерный дневник студента\n\n"
    "Выбери раздел 👇"
)


@router.callback_query(NavCB.filter(F.page == "home"))
async def nav_home(call: CallbackQuery) -> None:
    try:
        await call.message.edit_text(HOME_TEXT, reply_markup=home_keyboard(), parse_mode="HTML")
    except Exception:
        await call.message.answer(HOME_TEXT, reply_markup=home_keyboard(), parse_mode="HTML")
    await call.answer()
