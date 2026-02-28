"""Privacy screen."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, PrivacyToggleCB, privacy_keyboard
from db.base import get_session
from db.crud import get_user, update_privacy_level

router = Router(name="privacy")

PRIVACY_DESCRIPTIONS = {
    1: (
        "🔓 <b>Стандартная приватность</b>\n\n"
        "✅ Вуз видит: факультет, год, уровень, город, компанию (обезличенно)\n"
        "❌ НЕ видит: имя, username, зарплату"
    ),
    2: (
        "🔒 <b>Максимальная приватность</b>\n\n"
        "✅ Вуз видит: только факультет и год (обезличенно)\n"
        "❌ НЕ видит: компанию, город, уровень, имя"
    ),
}


async def _show(target, current_level: int = 1) -> None:
    text = PRIVACY_DESCRIPTIONS[current_level] + "\n\nВыбери уровень:"
    kb   = privacy_keyboard(current_level)
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    user_id = message.from_user.id
    async with get_session() as session:
        user = await get_user(user_id, session)
        level = user.privacy_level if user else 1
    await _show(message, level)


@router.callback_query(NavCB.filter(F.page == "privacy"))
async def nav_privacy(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    async with get_session() as session:
        user = await get_user(user_id, session)
        level = user.privacy_level if user else 1
    await _show(call, level)


@router.callback_query(PrivacyToggleCB.filter())
async def process_privacy_toggle(call: CallbackQuery, callback_data: PrivacyToggleCB) -> None:
    user_id = call.from_user.id
    async with get_session() as session:
        await update_privacy_level(user_id, callback_data.level, session)
        await session.commit()
        
    await call.answer("✅ Настройки сохранены")
    text = PRIVACY_DESCRIPTIONS[callback_data.level] + "\n\nВыбери уровень:"
    try:
        await call.message.edit_text(
            text, reply_markup=privacy_keyboard(callback_data.level), parse_mode="HTML"
        )
    except Exception:
        pass
