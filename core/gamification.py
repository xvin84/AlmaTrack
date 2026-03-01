"""
Gamification logic: XP rewards, level thresholds, badge definitions.
Aligned strictly with TZ.
"""
from __future__ import annotations

from enum import IntEnum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import select, func
from db.models import UserProgress, Achievement, Employment, EventsAttendance, User

class BadgeCode(str):
    FIRST_JOB = "FIRST_JOB"
    UPDATED = "UPDATED"
    REMOTE_WORKER = "REMOTE_WORKER"
    ALUMNI = "ALUMNI"
    LEVEL_UP = "LEVEL_UP"
    MENTOR = "MENTOR"
    LOYAL = "LOYAL"
    PIONEER = "PIONEER"

BADGE_META = {
    BadgeCode.FIRST_JOB:     {"name": "Первый шаг",        "emoji": "🎯", "xp": 50, "description": "Добавлено первое место работы.", "hint": "Добавь своё первое место работы."},
    BadgeCode.UPDATED:       {"name": "Не стоит на месте", "emoji": "🔄", "xp": 30, "description": "Обновлены данные о работе минимум один раз.", "hint": "Обнови свои данные о работе."},
    BadgeCode.REMOTE_WORKER: {"name": "Удалёнщик",         "emoji": "🏠", "xp": 20, "description": "Работает в удалённом формате.", "hint": "Укажи формат работы «Удаленно»."},
    BadgeCode.ALUMNI:        {"name": "Выпускник",         "emoji": "🎓", "xp": 40, "description": "Является выпускником (alumni).", "hint": "Заполни год выпуска."},
    BadgeCode.LEVEL_UP:      {"name": "Рост",              "emoji": "📈", "xp": 60, "description": "Достигнут 2 уровень.", "hint": "Прокачай свой профиль до 2 уровня."},
    BadgeCode.MENTOR:        {"name": "Ментор",            "emoji": "🤝", "xp": 80, "description": "Отмечен как ментор.", "hint": "Стань ментором проекта."},
    BadgeCode.LOYAL:         {"name": "Свой",              "emoji": "⭐", "xp": 50, "description": "Пользуется ботом длительное время.", "hint": "Будь активным пользователем AlmaTrack."},
    BadgeCode.PIONEER:       {"name": "Первопроходец",     "emoji": "🥇", "xp": 100, "description": "Один из первых пользователей.", "hint": "Зарегистрируйся в числе первых."},
}

LEVEL_THRESHOLDS = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}
LEVEL_NAMES = {1: "🌱 Новичок", 2: "🚀 Стажёр", 3: "💼 Специалист",
               4: "🔥 Профи", 5: "👑 Легенда"}

XP_REWARDS: dict[str, int] = {
    "onboarding_complete": 50,
    "add_job": 40,
    "update_job": 30,
    "income_increase": 60,
    "streak_7": 25,
    "register_event": 15,
    "first_alumni": 40,
    "mentor": 80,
}

def calculate_level(xp: int) -> int:
    """Return the Level corresponding to the given XP total."""
    level = 1
    for lvl, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if xp >= threshold:
            level = lvl
    return level

def xp_to_next_level(xp: int) -> Optional[int]:
    """Return how many XP are needed to reach the next level."""
    current = calculate_level(xp)
    if current == 5:
        return None
    next_threshold = LEVEL_THRESHOLDS[current + 1]
    return next_threshold - xp

def format_level_bar(xp: int, length: int = 10) -> str:
    """Return a visual progress bar string for the current level."""
    current_level = calculate_level(xp)
    if current_level == 5:
        return "█" * length + " MAX"
    current_threshold = LEVEL_THRESHOLDS[current_level]
    next_threshold = LEVEL_THRESHOLDS[current_level + 1]
    progress = (xp - current_threshold) / (next_threshold - current_threshold)
    filled = int(progress * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"{bar} {int(progress * 100)}%"

async def award_xp(user_id: int, event: str, session) -> tuple[int, int | None]:
    """
    Add XP for the given event, check for level-up.
    Returns: (xp_gained, new_level_if_leveled_up)
    """
    xp_gained = XP_REWARDS.get(event, 0)
    if xp_gained == 0:
        return 0, None

    result = await session.execute(select(UserProgress).where(UserProgress.user_id == user_id))
    progress = result.scalar_one_or_none()

    if not progress:
        progress = UserProgress(user_id=user_id, xp_points=0, current_level=1)
        session.add(progress)

    old_level = progress.current_level
    progress.xp_points += xp_gained
    progress.last_xp_gain = datetime.now()

    new_level = calculate_level(progress.xp_points)

    if event in ["update_job", "add_job"]:
        progress.total_updates += 1

    if new_level > old_level:
        progress.current_level = int(new_level)
        return xp_gained, new_level

    return xp_gained, None

async def check_and_award_badges(user_id: int, session) -> list[str]:
    """
    Evaluate all badge conditions and award unearned ones.
    Returns list of newly awarded badge codes.
    """
    result = await session.execute(select(Achievement.badge_code).where(Achievement.user_id == user_id))
    existing = set(result.scalars().all())

    new_badges = []

    async def add_badge_with_xp(code: str):
        if code not in existing:
            session.add(Achievement(user_id=user_id, badge_code=code))
            new_badges.append(code)
            existing.add(code)
            # Award XP for the badge
            prog_res = await session.execute(select(UserProgress).where(UserProgress.user_id == user_id))
            prog = prog_res.scalar_one()
            prog.xp_points += BADGE_META[code]["xp"]
            prog.current_level = calculate_level(prog.xp_points)

    # FIRST_JOB
    emp_res = await session.execute(select(func.count(Employment.id)).where(Employment.user_id == user_id))
    if emp_res.scalar() > 0:
        await add_badge_with_xp(BadgeCode.FIRST_JOB)

    prog_res = await session.execute(select(UserProgress).where(UserProgress.user_id == user_id))
    prog = prog_res.scalar_one_or_none()
    
    user_res = await session.execute(select(User).where(User.telegram_id == user_id))
    user = user_res.scalar_one_or_none()

    if prog:
        # UPDATED
        if prog.total_updates > 0:
            await add_badge_with_xp(BadgeCode.UPDATED)

        # LOYAL (Active 30+ days)
        if user and user.created_at:
            days_active = (datetime.now() - user.created_at).days
            if days_active >= 30:
                await add_badge_with_xp(BadgeCode.LOYAL)

    # REMOTE_WORKER
    remote_res = await session.execute(
        select(func.count(Employment.id))
        .where(Employment.user_id == user_id, Employment.work_format == "remote")
    )
    if remote_res.scalar() > 0:
        await add_badge_with_xp(BadgeCode.REMOTE_WORKER)
        
    # ALUMNI
    if user and user.is_alumni:
        await add_badge_with_xp(BadgeCode.ALUMNI)

    # PIONEER (First 100 users)
    user_pioneer = await session.execute(select(User.telegram_id).order_by(User.created_at).limit(100))
    pioneers = [row[0] for row in user_pioneer]
    if user_id in pioneers:
        await add_badge_with_xp(BadgeCode.PIONEER)

    return new_badges

async def update_streak(user_id: int, session) -> int:
    """
    Update daily streak. Call on every user interaction.
    Returns current streak_days value.
    """
    result = await session.execute(select(UserProgress).where(UserProgress.user_id == user_id))
    progress = result.scalar_one_or_none()
    
    now = datetime.now()
    if not progress:
        progress = UserProgress(user_id=user_id, streak_days=1, last_active=now)
        session.add(progress)
        return 1
    
    if progress.last_active:
        diff = (now.date() - progress.last_active.date()).days
        if diff == 1:
            progress.streak_days += 1
            if progress.streak_days % 7 == 0:
                await award_xp(user_id, "streak_7", session)
        elif diff > 1:
            progress.streak_days = 1
    else:
        progress.streak_days = 1
        
    progress.last_active = now

    return progress.streak_days
