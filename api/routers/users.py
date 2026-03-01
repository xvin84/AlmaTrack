import asyncio
import logging
from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import get_settings
from db.base import get_session
from db.models import User, Employment

router = APIRouter()
cfg = get_settings()
bot = Bot(token=cfg.bot_token)
logger = logging.getLogger(__name__)

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

@router.get("/admin/pending")
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

@router.post("/admin/approve/{user_id}")
async def approve_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = "approved"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="nav:home:0")]])
    asyncio.create_task(
        safe_send_message(user_id, "✅ <b>Твоя анкета одобрена!</b> Теперь тебе доступен полный функционал бота.", reply_markup=markup)
    )
        
    return {"status": "ok"}

@router.post("/admin/reject/{user_id}")
async def reject_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await session.delete(user)
    
    asyncio.create_task(
        safe_send_message(user_id, "❌ <b>Твоя анкета отклонена.</b> К сожалению, мы не можем подтвердить твои данные. Твой профиль был удален.")
    )
        
    return {"status": "ok"}

@router.post("/admin/approve_all")
async def approve_all(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.status == "pending"))
    users = result.scalars().all()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="nav:home:0")]])
    
    for u in users:
        u.status = "approved"
        asyncio.create_task(
            safe_send_message(u.telegram_id, "✅ <b>Твоя анкета одобрена!</b> Теперь тебе доступен полный функционал бота.", reply_markup=markup)
        )
            
    return {"status": "ok", "count": len(users)}

@router.post("/admin/reject_all")
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
