"""
/update command — update current job record.

Triggered by:
  - /update command
  - NavCB(page="update_job") from profile screen
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    ConfirmCB,
    NavCB,
    PositionLevelCB,
    WorkCityCB,
    WorkFormatCB,
    cancel_keyboard,
    confirm_keyboard,
    position_level_keyboard,
    work_city_keyboard,
    work_format_keyboard,
)
from bot.states import UpdateEmploymentFSM

from db.base import get_session
from db.crud import get_user, has_current_employment, close_current_employment, create_employment
from core.gamification import award_xp, check_and_award_badges
import logging

logger = logging.getLogger(__name__)

router = Router(name="employment")

FORMAT_LABELS = {"office": "Офис 🏢", "remote": "Удалёнка 🏠", "hybrid": "Гибрид 🔀"}
LEVEL_LABELS  = {
    "intern": "Стажёр", "junior": "Junior", "middle": "Middle",
    "senior": "Senior", "lead": "Lead",     "cto": "CTO/C-level",
}


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

@router.message(Command("update"))
async def cmd_update_msg(message: Message, state: FSMContext) -> None:
    await _start_update(message, state)


@router.callback_query(NavCB.filter(F.page == "update_job"))
async def cmd_update_cb(call: CallbackQuery, state: FSMContext) -> None:
    await _start_update(call.message, state)
    await call.answer()


async def _start_update(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(message.from_user.id, session)
        if not user:
            await message.answer("❌ Сначала нужно пройти регистрацию: /start")
            return
            
        has_job = await has_current_employment(message.from_user.id, session)

    await state.set_state(UpdateEmploymentFSM.confirm_end_current)
    if has_job:
        await message.answer(
            "✏️ <b>Обновление места работы</b>\n\n"
            "Текущая запись будет закрыта. Продолжить?",
            reply_markup=confirm_keyboard(),
            parse_mode="HTML",
        )
    else:
        await _job_input(message, state)


@router.callback_query(UpdateEmploymentFSM.confirm_end_current, ConfirmCB.filter())
async def process_end_confirm(call: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.answer != "yes":
        await state.clear()
        await call.message.edit_text("❌ Обновление отменено.")
        await call.answer()
        return
    await _job_input(call.message, state)
    await call.answer()


# ---------------------------------------------------------------------------
# Job detail steps (same pattern as onboarding)
# ---------------------------------------------------------------------------

async def _job_input(message: Message, state: FSMContext) -> None:
    await state.set_state(UpdateEmploymentFSM.company_name)
    await message.answer("🏢 Название новой компании:", reply_markup=cancel_keyboard())


@router.message(UpdateEmploymentFSM.company_name, F.text)
async def upd_company(message: Message, state: FSMContext) -> None:
    await state.update_data(company_name=message.text.strip())
    await state.set_state(UpdateEmploymentFSM.work_city)
    await message.answer("🌆 Город:", reply_markup=work_city_keyboard())


@router.callback_query(UpdateEmploymentFSM.work_city, WorkCityCB.filter())
async def upd_city(call: CallbackQuery, callback_data: WorkCityCB, state: FSMContext) -> None:
    if callback_data.city == "Другой":
        await state.update_data(_awaiting_custom_city=True)
        await call.message.edit_text("✏️ Введи название города:")
        await call.answer()
        return
    await state.update_data(work_city=callback_data.city)
    await state.set_state(UpdateEmploymentFSM.work_format)
    await call.message.edit_text("🔀 Формат работы:", reply_markup=work_format_keyboard())
    await call.answer()


@router.message(UpdateEmploymentFSM.work_city, F.text)
async def upd_custom_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("_awaiting_custom_city"):
        return
    await state.update_data(work_city=message.text.strip(), _awaiting_custom_city=False)
    await state.set_state(UpdateEmploymentFSM.work_format)
    await message.answer("🔀 Формат работы:", reply_markup=work_format_keyboard())


@router.callback_query(UpdateEmploymentFSM.work_format, WorkFormatCB.filter())
async def upd_format(call: CallbackQuery, callback_data: WorkFormatCB, state: FSMContext) -> None:
    await state.update_data(work_format=callback_data.fmt)
    await state.set_state(UpdateEmploymentFSM.position_title)
    await call.message.edit_text("👔 Должность:")
    await call.answer()


@router.message(UpdateEmploymentFSM.position_title, F.text)
async def upd_title(message: Message, state: FSMContext) -> None:
    await state.update_data(position_title=message.text.strip())
    await state.set_state(UpdateEmploymentFSM.position_level)
    await message.answer("📈 Уровень:", reply_markup=position_level_keyboard())


@router.callback_query(UpdateEmploymentFSM.position_level, PositionLevelCB.filter())
async def upd_level(call: CallbackQuery, callback_data: PositionLevelCB, state: FSMContext) -> None:
    await state.update_data(position_level=callback_data.level)
    data = await state.get_data()
    summary = (
        f"🏢 <b>{data['company_name']}</b>\n"
        f"🌆 {data.get('work_city', '—')} · {FORMAT_LABELS.get(data.get('work_format', ''), '—')}\n"
        f"👔 {data.get('position_title', '—')} ({LEVEL_LABELS.get(callback_data.level, '—')})\n"
    )
    await state.set_state(UpdateEmploymentFSM.confirm)
    await call.message.edit_text(
        f"📋 <b>Проверь новые данные:</b>\n\n{summary}\nСохранить?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(UpdateEmploymentFSM.confirm, ConfirmCB.filter())
async def upd_final(call: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.answer != "yes":
        await state.set_state(UpdateEmploymentFSM.company_name)
        await call.message.edit_text("🏢 Введи компанию заново:")
        await call.answer()
        return

    data = await state.get_data()
    user_id = call.from_user.id
    
    try:
        async with get_session() as session:
            await close_current_employment(user_id, session)
            
            await create_employment(
                user_id=user_id,
                company_name=data["company_name"],
                city=data.get("work_city"),
                work_format=data.get("work_format"),
                position_title=data["position_title"],
                position_level=data.get("position_level"),
                session=session
            )
            
            xp, new_level = await award_xp(user_id, "update_job", session)
            badges = await check_and_award_badges(user_id, session)
            
            await session.commit()
            
    except Exception as e:
        logger.exception("Failed to update employment")
        await call.answer("Ошибка сохранения данных", show_alert=True)
        return

    await state.clear()
    
    msg = "✅ <b>Данные о работе обновлены!</b>\n\n"
    if xp > 0:
        msg += f"⭐ <b>+{xp} XP</b>\n"
    if new_level is not None:
        msg += f"🎉 <b>Уровень повышен: {new_level.name}!</b>\n"
    if badges:
        from core.gamification import BADGES
        b_names = [BADGES.get(b, {}).get('name', b) for b in badges]
        msg += f"🏅 <b>Новые бейджи: {', '.join(b_names)}</b>\n"
        
    await call.message.edit_text(msg, parse_mode="HTML")
    await call.answer()
