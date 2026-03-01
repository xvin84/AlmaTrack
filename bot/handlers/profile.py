"""Profile screen — shown via NavCB(page="profile")."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, home_keyboard, profile_keyboard, DeleteAccountCB, delete_account_keyboard
from core.emoji import E
from db.base import get_session
from db.crud import get_user, get_current_employment, get_user_progress, get_user_badge_codes, delete_user
from core.gamification import LEVEL_NAMES, xp_to_next_level, BADGE_META
from bot.handlers.employment import LEVEL_LABELS, FORMAT_LABELS

router = Router()

async def _show_profile(target, user_id: int) -> None:
    """Render profile. target is Message or CallbackQuery."""
    async with get_session() as session:
        user = await get_user(user_id, session)
        if not user:
            msg = "❌ Пользователь не найден. Введи /start для регистрации."
            if isinstance(target, CallbackQuery):
                await target.message.edit_text(msg)
                await target.answer()
            else:
                await target.answer(msg)
            return

        employment = await get_current_employment(user_id, session)
        progress = await get_user_progress(user_id, session)
        badges_set = await get_user_badge_codes(user_id, session)

    level = progress.current_level if progress else 1
    xp = progress.xp_points if progress else 0
    streak = progress.streak_days if progress else 0

    needed = xp_to_next_level(xp)
    xp_text = f"{xp} / {xp + needed}" if needed else f"{xp} (MAX)"

    badge_list = []
    for code in badges_set:
        b = BADGE_META.get(code, {})
        emoji = b.get("emoji", "🏅")
        name = b.get("name", code)
        badge_list.append(f"{emoji} {name}")
        
    badge_line = "  ".join(badge_list) if badge_list else "<i>Пока нет бейджей</i>"
    
    text = (
        f"👤 <b>{user.full_name}</b>\n"
        f"🎓 {user.faculty} · {user.enrollment_year}\n\n"
        f"<b>Уровень {level} — {LEVEL_NAMES.get(level, 'Студент')}</b>\n"
        f"{E.star} XP: {xp_text}  {E.fire} Стрик: {streak} дн.\n\n"
    )
    
    if employment:
        level_str = LEVEL_LABELS.get(employment.position_level, employment.position_level)
        fmt_str = FORMAT_LABELS.get(employment.work_format, employment.work_format)
        
        text += (
            f"💼 <b>Место работы</b>\n"
            f"🏢 {employment.company_name}\n"
            f"👔 {employment.position_title} ({level_str})\n"
            f"🌆 {employment.city or '—'} · {fmt_str}\n\n"
        )
    else:
        text += "💼 Место работы не указано\n\n"

    text += f"{E.trophy} <b>Бейджи:</b>\n{badge_line}"

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=profile_keyboard(), parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await _show_profile(message, message.from_user.id)


@router.callback_query(NavCB.filter(F.page == "profile"))
async def nav_profile(call: CallbackQuery) -> None:
    await _show_profile(call, call.from_user.id)


@router.callback_query(NavCB.filter(F.page == "delete_acc"))
async def prompt_delete_account(call: CallbackQuery) -> None:
    text = (
        "⚠️ <b>Удаление аккаунта</b>\n\n"
        "Ты уверен, что хочешь удалить свой профиль?\n"
        "Все твои достижения, опыт и статистика будут безвозвратно удалены. "
        "Это действие нельзя отменить!"
    )
    try:
        await call.message.edit_text(text, reply_markup=delete_account_keyboard(), parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=delete_account_keyboard(), parse_mode="HTML")
    await call.answer()


@router.callback_query(DeleteAccountCB.filter())
async def process_delete_account(call: CallbackQuery, callback_data: DeleteAccountCB) -> None:
    if callback_data.action == "cancel":
        await call.answer("Отменено")
        await _show_profile(call, call.from_user.id)
        return

    # User confirmed deletion
    user_id = call.from_user.id
    current_msg_id = call.message.message_id
    
    # Attempt to wipe recent history
    try:
        for i in range(1, 50):
            try:
                await call.bot.delete_message(chat_id=user_id, message_id=current_msg_id - i)
            except Exception:
                pass
    except Exception:
        pass

    async with get_session() as session:
        await delete_user(user_id, session)
        await session.commit()
    
    await call.message.edit_text(
        "👋 <b>Твой аккаунт и все данные успешно удалены.</b>\n\n"
        "Если захочешь вернуться, просто нажми /start.",
        parse_mode="HTML"
    )
    await call.answer()
