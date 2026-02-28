import logging
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from db.base import get_session, init_db
from db.models import User, Employment

cfg = get_settings()
bot = Bot(token=cfg.bot_token)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await bot.session.close()

app = FastAPI(title="AlmaTrack API", lifespan=lifespan)

async def get_db_session():
    async with get_session() as session:
        yield session

@app.get("/api/admin/pending")
async def get_pending_users(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(User).where(User.status == "pending").order_by(User.created_at)
    )
    users = result.scalars().all()
    return [
        {
            "telegram_id": u.telegram_id,
            "full_name": u.full_name,
            "faculty": u.faculty,
            "enrollment_year": u.enrollment_year,
            "created_at": u.created_at.isoformat()
        } for u in users
    ]

@app.post("/api/admin/approve/{user_id}")
async def approve_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = "approved"
    
    # Send notification
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="nav:home")]])
        await bot.send_message(user_id, "✅ <b>Твоя анкета одобрена!</b> Теперь тебе доступен полный функционал бота.", reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
        
    return {"status": "ok"}

@app.post("/api/admin/reject/{user_id}")
async def reject_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = "rejected"
    
    try:
        await bot.send_message(user_id, "❌ <b>Твоя анкета отклонена.</b> К сожалению, мы не можем подтвердить твои данные.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
        
    return {"status": "ok"}

@app.get("/api/stats/summary")
async def get_stats_summary(session: AsyncSession = Depends(get_db_session)):
    users_count = await session.scalar(select(func.count()).select_from(User))
    companies_count = await session.scalar(select(func.count(Employment.company_name.distinct())))
    cities_count = await session.scalar(select(func.count(Employment.city.distinct())))
    
    # Employers chart (top companies)
    employers_result = await session.execute(
        select(Employment.company_name, func.count()).group_by(Employment.company_name).order_by(func.count().desc()).limit(10)
    )
    employers = []
    employers_count = []
    for row in employers_result:
        employers.append(row[0])
        employers_count.append(row[1])

    # Levels chart
    levels_result = await session.execute(
        select(Employment.position_level, func.count()).group_by(Employment.position_level)
    )
    levels = []
    levels_count = []
    for row in levels_result:
        levels.append(row[0] or "unknown")
        levels_count.append(row[1])

    # Cities chart
    cities_result = await session.execute(
        select(Employment.city, func.count()).group_by(Employment.city).order_by(func.count().desc()).limit(7)
    )
    cities = []
    city_counts = []
    for row in cities_result:
        cities.append(row[0] or "unknown")
        city_counts.append(row[1])

    return {
        "summary": {
            "total_users": users_count or 0,
            "total_companies": companies_count or 0,
            "total_cities": cities_count or 0,
        },
        "charts": {
            "employers": {"labels": employers, "data": employers_count},
            "levels": {"labels": levels, "data": levels_count},
            "cities": {"labels": cities, "data": city_counts}
        }
    }
