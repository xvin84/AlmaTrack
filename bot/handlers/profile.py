"""Profile screen — shown via NavCB(page="profile")."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, home_keyboard, profile_keyboard
from core.emoji import E

router = Router(name="profile")

LEVEL_NAMES  = {1: "Новичок", 2: "Активный", 3: "Опытный", 4: "Эксперт", 5: "Легенда"}
LEVEL_EMOJIS = {1: "🌱", 2: "⚡", 3: "🔥", 4: "💎", 5: "👑"}


def _build_profile_text(full_name: str, user: dict, employment: dict | None,
                        progress: dict, badges: list[str]) -> str:
    level = progress["current_level"]
    xp    = progress["xp_points"]
    xp_next = 300  # TODO: from gamification module
    streak  = progress["streak_days"]

    badge_line = "  ".join(f"🏅 {b}" for b in badges) if badges else "Пока нет бейджей"

    text = (
        f"👤 <b>{full_name}</b>\n"
        f"🎓 {user['faculty']} · {user['enrollment_year']}\n\n"
        f"{LEVEL_EMOJIS[level]} <b>Уровень {level} — {LEVEL_NAMES[level]}</b>\n"
        f"{E.star} XP: {xp} / {xp_next}  {E.fire} Стрик: {streak} дн.\n\n"
    )
    if employment:
        text += (
            f"💼 <b>Место работы</b>\n"
            f"🏢 {employment['company_name']}\n"
            f"👔 {employment['position_title']} ({employment['position_level']})\n"
            f"🌆 {employment['city']} · {employment['work_format']}\n\n"
        )
    else:
        text += "💼 Место работы не указано\n\n"

    text += f"{E.trophy} <b>Бейджи:</b>\n{badge_line}"
    return text


async def _show_profile(target, user_id: int) -> None:
    """Render profile. target is Message or CallbackQuery."""
    # TODO: fetch from DB
    user       = {"faculty": "Информационные технологии", "enrollment_year": 2021, "is_alumni": False}
    employment = {"company_name": "Tech Corp", "position_title": "Python-разработчик",
                  "position_level": "junior", "work_format": "remote", "city": "Москва"}
    progress   = {"xp_points": 150, "current_level": 2, "streak_days": 3}
    badges     = ["FIRST_STEP", "FIRST_JOB"]

    if isinstance(target, CallbackQuery):
        full_name = target.from_user.full_name
        text = _build_profile_text(full_name, user, employment, progress, badges)
        try:
            await target.message.edit_text(text, reply_markup=profile_keyboard(), parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")
        await target.answer()
    else:
        full_name = target.from_user.full_name
        text = _build_profile_text(full_name, user, employment, progress, badges)
        await target.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await _show_profile(message, message.from_user.id)


@router.callback_query(NavCB.filter(F.page == "profile"))
async def nav_profile(call: CallbackQuery) -> None:
    await _show_profile(call, call.from_user.id)
