"""
CRUD operations for AlmaTrack.

All functions accept an AsyncSession as the last argument so callers
can batch multiple operations into a single transaction.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Achievement, Employment, Event, EventsAttendance, User, UserProgress, Moderator


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


async def get_user(telegram_id: int, session: AsyncSession) -> User | None:
    """Fetch a user by Telegram ID."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def create_user(
    telegram_id: int,
    full_name: str,
    faculty: str,
    enrollment_year: int,
    session: AsyncSession,
    *,
    username: str | None = None,
    graduation_year: int | None = None,
    is_alumni: bool = False,
    city: str | None = None,
) -> User:
    """Create a new user and their progress record. Raises if already exists."""
    # TODO: handle IntegrityError for duplicate telegram_id
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        faculty=faculty,
        enrollment_year=enrollment_year,
        graduation_year=graduation_year,
        is_alumni=is_alumni,
        city=city,
    )
    progress = UserProgress(user_id=telegram_id)
    session.add(user)
    session.add(progress)
    await session.flush()
    return user


async def update_privacy_level(
    telegram_id: int, level: int, session: AsyncSession
) -> None:
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(privacy_level=level)
    )


async def touch_last_active(telegram_id: int, session: AsyncSession) -> None:
    """Update last_active timestamp. Call on each user interaction."""
    # TODO: implement — use func.now() or datetime.utcnow()
    pass


async def delete_user(telegram_id: int, session: AsyncSession) -> None:
    """Delete a user and cascading models manually if needed, by ID."""
    user = await get_user(telegram_id, session)
    if user:
        await session.delete(user)


# ---------------------------------------------------------------------------
# Employment
# ---------------------------------------------------------------------------


async def get_current_employment(user_id: int, session: AsyncSession) -> Employment | None:
    """Return the current (is_current=True) employment record, if any."""
    result = await session.execute(
        select(Employment)
        .where(Employment.user_id == user_id, Employment.is_current.is_(True))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def has_current_employment(user_id: int, session: AsyncSession) -> bool:
    return await get_current_employment(user_id, session) is not None


async def create_employment(
    user_id: int,
    company_name: str,
    position_title: str,
    session: AsyncSession,
    *,
    city: str | None = None,
    work_format: str | None = None,
    position_level: str | None = None,
    started_at: date | None = None,
) -> Employment:
    if started_at is None:
        started_at = date.today()
    emp = Employment(
        user_id=user_id,
        company_name=company_name,
        city=city,
        work_format=work_format,
        position_title=position_title,
        position_level=position_level,
        started_at=started_at.isoformat(),
        is_current=True,
    )
    session.add(emp)
    await session.flush()
    # TODO: increment user_progress.total_updates
    return emp


async def close_current_employment(
    user_id: int, session: AsyncSession, ended_at: date | None = None
) -> None:
    """Mark the current job as ended."""
    if ended_at is None:
        ended_at = date.today()
    await session.execute(
        update(Employment)
        .where(Employment.user_id == user_id, Employment.is_current.is_(True))
        .values(is_current=False, ended_at=ended_at.isoformat())
    )


# ---------------------------------------------------------------------------
# Progress & XP
# ---------------------------------------------------------------------------


async def get_user_progress(user_id: int, session: AsyncSession) -> UserProgress | None:
    result = await session.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def add_xp(user_id: int, xp: int, session: AsyncSession) -> UserProgress:
    """
    Add XP to the user's progress record and recalculate level.
    Returns the updated UserProgress.
    """
    # TODO: implement
    # 1. Fetch UserProgress
    # 2. progress.xp_points += xp
    # 3. Recalculate level with gamification.calculate_level()
    # 4. Update progress.current_level if changed
    # 5. Set progress.last_xp_gain = now
    # 6. flush and return
    progress = await get_user_progress(user_id, session)
    if progress is None:
        raise ValueError(f"No progress record for user {user_id}")
    progress.xp_points += xp
    # TODO: recalculate level
    await session.flush()
    return progress


# ---------------------------------------------------------------------------
# Achievements / Badges
# ---------------------------------------------------------------------------


async def get_user_badge_codes(user_id: int, session: AsyncSession) -> set[str]:
    result = await session.execute(
        select(Achievement.badge_code).where(Achievement.user_id == user_id)
    )
    return set(result.scalars().all())


async def award_badge(
    user_id: int, badge_code: str, session: AsyncSession
) -> bool:
    """
    Award a badge if not already earned.
    Returns True if newly awarded, False if already had it.
    """
    existing = await session.execute(
        select(Achievement).where(
            Achievement.user_id == user_id,
            Achievement.badge_code == badge_code,
        )
    )
    if existing.scalar_one_or_none():
        return False
    session.add(Achievement(user_id=user_id, badge_code=badge_code))
    await session.flush()
    return True


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


async def get_available_events(user_level: int, session: AsyncSession) -> list[Event]:
    result = await session.execute(
        select(Event).where(Event.min_level <= user_level).order_by(Event.event_date)
    )
    return list(result.scalars().all())


async def get_user_registered_event_ids(user_id: int, session: AsyncSession) -> set[int]:
    result = await session.execute(
        select(EventsAttendance.event_id).where(EventsAttendance.user_id == user_id)
    )
    return set(result.scalars().all())


async def register_for_event(user_id: int, event_id: int, session: AsyncSession) -> None:
    # TODO: handle duplicate registration gracefully
    session.add(EventsAttendance(user_id=user_id, event_id=event_id))
    await session.flush()


async def unregister_from_event(user_id: int, event_id: int, session: AsyncSession) -> None:
    attendance = await session.execute(
        select(EventsAttendance).where(
            EventsAttendance.user_id == user_id,
            EventsAttendance.event_id == event_id,
        )
    )
    obj = attendance.scalar_one_or_none()
    if obj:
        await session.delete(obj)
        await session.flush()


# ---------------------------------------------------------------------------
# Analytics (for API layer)
# ---------------------------------------------------------------------------


async def get_faculty_stats(faculty: str, session: AsyncSession) -> dict:
    """
    Return aggregated stats for a given faculty.
    Used by /stats command and FastAPI analytics endpoints.
    """
    # TODO: implement aggregation queries
    # - count of users with employment data
    # - distribution by position_level
    # - top 5 companies
    # - top 5 cities
    # - avg months to junior/middle
    return {}


async def get_summary_counts(session: AsyncSession) -> dict:
    """Return total_users, total_companies, total_cities, total_alumni."""
    # TODO: implement COUNT queries
    return {"total_users": 0, "total_companies": 0, "total_cities": 0, "total_alumni": 0}


# ---------------------------------------------------------------------------
# Moderators
# ---------------------------------------------------------------------------


async def get_moderator_by_username(username: str, session: AsyncSession) -> Moderator | None:
    result = await session.execute(select(Moderator).where(Moderator.username == username))
    return result.scalar_one_or_none()


async def get_moderator_by_id(mod_id: int, session: AsyncSession) -> Moderator | None:
    result = await session.execute(select(Moderator).where(Moderator.id == mod_id))
    return result.scalar_one_or_none()


async def get_all_moderators(session: AsyncSession) -> list[Moderator]:
    result = await session.execute(select(Moderator).order_by(Moderator.created_at))
    return list(result.scalars().all())


async def create_moderator(
    username: str,
    full_name: str,
    password_hash: str,
    session: AsyncSession,
    priority: int = 2
) -> Moderator:
    mod = Moderator(
        username=username,
        full_name=full_name,
        password_hash=password_hash,
        priority=priority
    )
    session.add(mod)
    await session.flush()
    return mod


async def delete_moderator(mod_id: int, session: AsyncSession) -> bool:
    mod = await get_moderator_by_id(mod_id, session)
    if mod:
        await session.delete(mod)
        await session.flush()
        return True
    return False
