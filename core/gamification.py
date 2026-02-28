"""
Gamification logic: XP rewards, level thresholds, badge definitions.

Usage example (after DB integration):
    xp_gained, new_level = await award_xp(user_id, "update_job", session)
    new_badges = await check_and_award_badges(user_id, session)
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

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
    # TODO: implement
    # 1. Look up XP_REWARDS[event]
    # 2. Fetch current xp from user_progress
    # 3. Add xp, check if level changed
    # 4. Update user_progress in DB
    # 5. Return (gained, new_level or None)
    xp_gained = XP_REWARDS.get(event, 0)
    return xp_gained, None


async def check_and_award_badges(user_id: int, session) -> list[str]:
    """
    Evaluate all badge conditions and award unearned ones.

    Returns list of newly awarded badge codes.
    """
    # TODO: implement
    # For each badge code, check condition against DB data:
    #   FIRST_JOB   — has any employment record
    #   UPDATER     — total_updates >= 3
    #   STREAK_7    — streak_days >= 7
    #   SENIOR_PLUS — any employment with level in (senior, lead, cto)
    #   NETWORKER   — events_attendance count >= 3
    #   LEGEND_LEVEL — current_level == 5
    # Award (INSERT IGNORE) any newly met conditions
    # Return list of newly awarded codes
    return []


async def update_streak(user_id: int, session) -> int:
    """
    Update daily streak. Call on every user interaction.

    Returns current streak_days value.
    """
    # TODO: implement
    # 1. Fetch last_active from user_progress
    # 2. If last_active was yesterday → increment streak_days
    # 3. If last_active was today → no change
    # 4. If last_active was 2+ days ago → reset streak to 1
    # 5. Update last_active = now
    return 0
