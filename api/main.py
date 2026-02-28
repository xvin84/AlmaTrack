import logging
import asyncio
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, update, func
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

async def safe_send_message(user_id: int, text: str, reply_markup=None):
    try:
        if reply_markup:
            await bot.send_message(user_id, text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")

@app.get("/api/admin/pending")
async def get_pending_users(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(User, Employment)
        .outerjoin(Employment, (User.telegram_id == Employment.user_id) & (Employment.is_current == True))
        .where(User.status == "pending")
        .order_by(User.created_at.desc())
    )
    
    users_data = []
    for user, emp in result:
        users_data.append({
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "faculty": user.faculty,
            "enrollment_year": user.enrollment_year,
            "company": emp.company_name if emp else "—",
            "position": emp.position_level if emp else "—",
            "created_at": user.created_at.isoformat()
        })
    return users_data

@app.post("/api/admin/approve/{user_id}")
async def approve_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = "approved"
    
    # Send notification
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="nav:home")]])
    asyncio.create_task(
        safe_send_message(user_id, "✅ <b>Твоя анкета одобрена!</b> Теперь тебе доступен полный функционал бота.", reply_markup=markup)
    )
        
    return {"status": "ok"}

@app.post("/api/admin/reject/{user_id}")
async def reject_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user instead of just marking as rejected
    await session.delete(user)
    
    asyncio.create_task(
        safe_send_message(user_id, "❌ <b>Твоя анкета отклонена.</b> К сожалению, мы не можем подтвердить твои данные. Твой профиль был удален.")
    )
        
    return {"status": "ok"}


@app.post("/api/admin/approve_all")
async def approve_all(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.status == "pending"))
    users = result.scalars().all()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="nav:home")]])
    
    for u in users:
        u.status = "approved"
        asyncio.create_task(
            safe_send_message(u.telegram_id, "✅ <b>Твоя анкета одобрена!</b> Теперь тебе доступен полный функционал бота.", reply_markup=markup)
        )
            
    return {"status": "ok", "count": len(users)}


@app.post("/api/admin/reject_all")
async def reject_all(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.status == "pending"))
    users = result.scalars().all()
    count = len(users)
    
    for u in users:
        await session.delete(u)
        asyncio.create_task(
            safe_send_message(u.telegram_id, "❌ <b>Твоя анкета отклонена.</b> К сожалению, мы не можем подтвердить твои данные. Твой профиль был удален.")
        )
            
    return {"status": "ok", "count": count}


@app.get("/api/stats/summary")
async def get_stats_summary(session: AsyncSession = Depends(get_db_session)):
    # Filter stats to exclude users with privacy_level == 2
    users_count = await session.scalar(select(func.count()).select_from(User).where(User.privacy_level < 2))
    companies_count = await session.scalar(
        select(func.count(Employment.company_name.distinct()))
        .join(User, User.telegram_id == Employment.user_id)
        .where(User.privacy_level < 2)
    )
    cities_count = await session.scalar(
        select(func.count(Employment.city.distinct()))
        .join(User, User.telegram_id == Employment.user_id)
        .where(User.privacy_level < 2)
    )
    
    # Employers chart (top companies)
    employers_result = await session.execute(
        select(Employment.company_name, func.count())
        .join(User, User.telegram_id == Employment.user_id)
        .where((User.privacy_level < 2) & (Employment.company_name != None))
        .group_by(Employment.company_name)
        .order_by(func.count().desc()).limit(10)
    )
    employers = []
    employers_count = []
    for row in employers_result:
        employers.append(row[0])
        employers_count.append(row[1])

    # Levels chart
    levels_result = await session.execute(
        select(Employment.position_level, func.count())
        .join(User, User.telegram_id == Employment.user_id)
        .where((User.privacy_level < 2) & (Employment.position_level != None))
        .group_by(Employment.position_level)
    )
    levels = []
    levels_count = []
    for row in levels_result:
        levels.append(row[0])
        levels_count.append(row[1])

    # Cities chart
    cities_result = await session.execute(
        select(Employment.city, func.count())
        .join(User, User.telegram_id == Employment.user_id)
        .where((User.privacy_level < 2) & (Employment.city != None))
        .group_by(Employment.city)
        .order_by(func.count().desc()).limit(7)
    )
    cities = []
    city_counts = []
    for row in cities_result:
        cities.append(row[0])
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
