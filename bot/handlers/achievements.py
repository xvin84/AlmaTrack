"""Achievements screen."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, achievements_keyboard
from core.gamification import BADGES
from core.emoji import E

router = Router(name="achievements")


def _build_text(earned_codes: set[str]) -> str:
    earned, locked = [], []
    for code, badge in BADGES.items():
        if code in earned_codes:
            earned.append(f"{badge['emoji']} <b>{badge['name']}</b>\n   {badge['description']}")
        else:
            locked.append(f"🔒 <b>{badge['name']}</b>\n   {badge['hint']}")

    text = f"{E.trophy} <b>Достижения</b>\n\n"
    if earned:
        text += "✅ <b>Получены:</b>\n" + "\n\n".join(earned) + "\n\n"
    else:
        text += "Пока нет бейджей — начни с /start!\n\n"
    if locked:
        text += "🔒 <b>Не получены:</b>\n" + "\n\n".join(locked)
    return text


async def _show(target, earned_codes: set[str] | None = None) -> None:
    if earned_codes is None:
        earned_codes = {"FIRST_STEP"}  # TODO: fetch from DB
    text = _build_text(earned_codes)
    kb   = achievements_keyboard()
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("achievements"))
async def cmd_achievements(message: Message) -> None:
    await _show(message)


@router.callback_query(NavCB.filter(F.page == "achievements"))
async def nav_achievements(call: CallbackQuery) -> None:
    await _show(call)
