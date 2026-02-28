"""Stats screen."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, stats_keyboard
from db.base import get_session
from sqlalchemy import select, func
from db.models import User, Employment

router = Router(name="stats")


async def _stats_text(user_id: int) -> str:
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user or not user.faculty:
            return "Факультет не указан."
            
        faculty = user.faculty
        
        # Get stats for this faculty
        faculty_users_count = await session.scalar(
            select(func.count(User.telegram_id)).where(User.faculty == faculty)
        )
        
        levels_res = await session.execute(
            select(Employment.position_level, func.count(Employment.id))
            .join(User)
            .where(User.faculty == faculty, Employment.is_current == True)
            .group_by(Employment.position_level)
        )
        dist = {row[0]: row[1] for row in levels_res if row[0]}
        
        comps_res = await session.execute(
            select(Employment.company_name, func.count(Employment.id))
            .join(User)
            .where(User.faculty == faculty, Employment.is_current == True)
            .group_by(Employment.company_name)
            .order_by(func.count(Employment.id).desc())
            .limit(3)
        )
        top_companies = [row[0] for row in comps_res]
        
        cities_res = await session.execute(
            select(Employment.city, func.count(Employment.id))
            .join(User)
            .where(User.faculty == faculty, Employment.is_current == True)
            .group_by(Employment.city)
            .order_by(func.count(Employment.id).desc())
            .limit(3)
        )
        top_cities = [row[0] for row in cities_res if row[0]]

        # User's own level
        my_emp_res = await session.execute(
            select(Employment.position_level).where(Employment.user_id == user_id, Employment.is_current == True)
        )
        my_level = my_emp_res.scalar_one_or_none()

    dist_lines = []
    for k in ["intern", "junior", "middle", "senior", "lead", "cto"]:
        v = dist.get(k, 0)
        marker = "→" if k == my_level else " "
        dist_lines.append(f"  {marker} {k.capitalize()}: {v} чел.")
        
    dist_str = "\n".join(dist_lines)
    comp_str = ", ".join(top_companies) or "Нет данных"
    city_str = ", ".join(top_cities) or "Нет данных"

    return (
        f"📊 <b>Статистика по факультету</b>\n"
        f"🎓 {faculty}\n\n"
        f"👥 Всего профилей: {faculty_users_count}\n\n"
        f"📈 <b>По уровням:</b>\n{dist_str}\n\n"
        f"🏢 <b>Топ компании:</b> {comp_str}\n"
        f"🌆 <b>Топ города:</b> {city_str}\n\n"
        "🔒 Данные обезличены."
    )


async def _show(target) -> None:
    text = await _stats_text(target.from_user.id)
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=stats_keyboard(), parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=stats_keyboard(), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=stats_keyboard(), parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await _show(message)


@router.callback_query(NavCB.filter(F.page == "stats"))
async def nav_stats(call: CallbackQuery) -> None:
    await _show(call)
