"""
ORM models for AlmaTrack.
All tables match the schema defined in the TZ.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    faculty: Mapped[str | None] = mapped_column(String(256))
    department: Mapped[str | None] = mapped_column(String(256))
    enrollment_year: Mapped[int | None] = mapped_column(Integer)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_alumni: Mapped[bool] = mapped_column(Boolean, default=False)
    city: Mapped[str | None] = mapped_column(String(128))
    privacy_level: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    employment: Mapped[list[Employment]] = relationship(back_populates="user", cascade="all, delete-orphan")
    progress: Mapped[UserProgress | None] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    achievements: Mapped[list[Achievement]] = relationship(back_populates="user", cascade="all, delete-orphan")
    events_attendance: Mapped[list[EventsAttendance]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Employment(Base):
    __tablename__ = "employment"
    __table_args__ = (
        CheckConstraint(
            "work_format IN ('office','remote','hybrid')", name="chk_work_format"
        ),
        CheckConstraint(
            "position_level IN ('intern','junior','middle','senior','lead','cto')",
            name="chk_position_level",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    company_domain: Mapped[str | None] = mapped_column(String(64))
    city: Mapped[str | None] = mapped_column(String(128))
    work_format: Mapped[str | None] = mapped_column(String(16))
    position_title: Mapped[str] = mapped_column(String(256), nullable=False)
    position_level: Mapped[str | None] = mapped_column(String(16))
    started_at: Mapped[str] = mapped_column(String(10), nullable=False)  # DATE as ISO string
    ended_at: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="employment")


class UserProgress(Base):
    __tablename__ = "user_progress"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id"), primary_key=True
    )
    xp_points: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_xp_gain: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_updates: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="progress")


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("user_id", "badge_code", name="uq_user_badge"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False)
    badge_code: Mapped[str] = mapped_column(String(64), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="achievements")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(32))
    min_level: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    attendance: Mapped[list[EventsAttendance]] = relationship(back_populates="event")


class EventsAttendance(Base):
    __tablename__ = "events_attendance"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="events_attendance")
    event: Mapped[Event] = relationship(back_populates="attendance")


class Moderator(Base):
    __tablename__ = "moderators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1 = Top Admin, 2 = Regular Admin
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
