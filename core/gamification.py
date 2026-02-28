"""
Gamification logic: XP rewards, level thresholds, badge definitions.

Usage example (after DB integration):
    xp_gained, new_level = await award_xp(user_id, "update_job", session)
    new_badges = await check_and_award_badges(user_id, session)
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import select, func
from db.models import UserProgress, Achievement, Employment, EventsAttendance

if TYPE_CHECKING:
    pass  # type hints only — no circular imports

# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------


class Level(IntEnum):
    NEWCOMER = 1
    ACTIVE = 2
    EXPERIENCED = 3
    EXPERT = 4
    LEGEND = 5


LEVEL_NAMES = {
    Level.NEWCOMER: "Новичок",
    Level.ACTIVE: "Активный",
    Level.EXPERIENCED: "Опытный",
    Level.EXPERT: "Эксперт",
    Level.LEGEND: "Легенда",
}

LEVEL_EMOJIS = {
    Level.NEWCOMER: "🌱",
    Level.ACTIVE: "⚡",
    Level.EXPERIENCED: "🔥",
    Level.EXPERT: "💎",
    Level.LEGEND: "👑",
}

# XP required to *reach* each level
XP_THRESHOLDS: dict[Level, int] = {
    Level.NEWCOMER: 0,
    Level.ACTIVE: 100,
    Level.EXPERIENCED: 300,
    Level.EXPERT: 700,
    Level.LEGEND: 1500,
}

# ---------------------------------------------------------------------------
# XP reward table
# ---------------------------------------------------------------------------

XP_REWARDS: dict[str, int] = {
    "onboarding_complete": 50,
    "first_job": 100,
    "update_job": 30,
    "profile_complete": 20,
    "streak_3": 15,
    "streak_7": 30,
    "streak_30": 100,
    "register_event": 10,
}

# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

BADGES: dict[str, dict] = {
    "FIRST_STEP": {
        "emoji": "👣",
        "name": "Первый шаг",
        "description": "Прошёл регистрацию в AlmaTrack",
        "hint": "Пройди регистрацию",
    },
    "FIRST_JOB": {
        "emoji": "💼",
        "name": "Первая работа",
        "description": "Добавил первое место работы",
        "hint": "Укажи место работы",
    },
    "UPDATER": {
        "emoji": "🔄",
        "name": "Обновлятель",
        "description": "Обновил данные о работе 3 раза",
        "hint": "Обнови данные 3 раза командой /update",
    },
    "STREAK_7": {
        "emoji": "🔥",
        "name": "Неделя активности",
        "description": "7 дней подряд взаимодействовал с ботом",
        "hint": "Заходи в бот 7 дней подряд",
    },
    "SENIOR_PLUS": {
        "emoji": "🚀",
        "name": "Старший специалист",
        "description": "Достиг уровня Senior или выше",
        "hint": "Укажи должность Senior/Lead",
    },
    "NETWORKER": {
        "emoji": "🤝",
        "name": "Нетворкер",
        "description": "Зарегистрировался на 3 мероприятия",
        "hint": "Запишись на 3 мероприятия",
    },
    "LEGEND_LEVEL": {
        "emoji": "👑",
        "name": "Легенда",
        "description": "Достиг 5-го уровня (1500 XP)",
        "hint": "Набери 1500 XP",
    },
}

# ---------------------------------------------------------------------------
# Pure functions (no DB)
# ---------------------------------------------------------------------------


def calculate_level(xp: int) -> Level:
    """Return the Level corresponding to the given XP total."""
    current = Level.NEWCOMER
    for lvl in Level:
        if xp >= XP_THRESHOLDS[lvl]:
            current = lvl
    return current


def xp_to_next_level(xp: int) -> int | None:
    """
    Return how many XP are needed to reach the next level.
    Returns None if the user is already at max level.
    """
    current = calculate_level(xp)
    if current == Level.LEGEND:
        return None
    next_lvl = Level(current + 1)
    return XP_THRESHOLDS[next_lvl] - xp


def format_level_bar(xp: int, bar_length: int = 10) -> str:
    """Return a visual progress bar string for the current level."""
    current = calculate_level(xp)
    if current == Level.LEGEND:
        return "█" * bar_length + " MAX"
    next_lvl = Level(current + 1)
    low = XP_THRESHOLDS[current]
    high = XP_THRESHOLDS[next_lvl]
    progress = (xp - low) / (high - low)
    filled = round(progress * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    return f"{bar} {xp}/{high} XP"


# ---------------------------------------------------------------------------
# Async DB-integrated functions (implement after DB layer is ready)
# ---------------------------------------------------------------------------


async def award_xp(user_id: int, event: str, session) -> tuple[int, Level | None]:
    """
    Add XP for the given event, check for level-up.

    Returns:
        (xp_gained, new_level_if_leveled_up)
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

    if event == "update_job" or event == "profile_complete":
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

    def add_badge(code: str):
        if code not in existing:
            session.add(Achievement(user_id=user_id, badge_code=code))
            new_badges.append(code)
            existing.add(code)

    # FIRST_STEP
    add_badge("FIRST_STEP")

    # FIRST_JOB
    emp_res = await session.execute(select(func.count(Employment.id)).where(Employment.user_id == user_id))
    if emp_res.scalar() > 0:
        add_badge("FIRST_JOB")

    prog_res = await session.execute(select(UserProgress).where(UserProgress.user_id == user_id))
    prog = prog_res.scalar_one_or_none()

    if prog:
        # UPDATER
        if prog.total_updates >= 3:
            add_badge("UPDATER")

        # STREAK_7
        if prog.streak_days >= 7:
            add_badge("STREAK_7")

        # LEGEND_LEVEL
        if prog.current_level >= 5:
            add_badge("LEGEND_LEVEL")

    # SENIOR_PLUS
    seniors = await session.execute(
        select(func.count(Employment.id))
        .where(Employment.user_id == user_id)
        .where(Employment.position_level.in_(["senior", "lead", "cto"]))
    )
    if seniors.scalar() > 0:
        add_badge("SENIOR_PLUS")

    # NETWORKER
    att_res = await session.execute(select(func.count(EventsAttendance.event_id)).where(EventsAttendance.user_id == user_id))
    if att_res.scalar() >= 3:
        add_badge("NETWORKER")

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
    else:
        if progress.last_active:
            diff = (now.date() - progress.last_active.date()).days
            if diff == 1:
                progress.streak_days += 1
            elif diff > 1:
                progress.streak_days = 1
        else:
            progress.streak_days = 1
            
        progress.last_active = now

    return progress.streak_days
