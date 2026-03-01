"""
Main navigation keyboards.

All navigation is now inline — no persistent ReplyKeyboard.
NavCB drives the entire app shell: home → section → back.
"""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ---------------------------------------------------------------------------
# Navigation CallbackData
# ---------------------------------------------------------------------------

class NavCB(CallbackData, prefix="nav"):
    """
    page:
        home         — main hub
        profile      — career card
        stats        — faculty stats
        achievements — badges screen
        events       — events list
        privacy      — privacy settings
        help         — help screen
        update_job   — triggers UpdateEmploymentFSM
    """
    page: str
    subpage: int = 0


class PrivacyToggleCB(CallbackData, prefix="privacy"):
    level: int  # 1 = standard, 2 = max privacy


class EventActionCB(CallbackData, prefix="event"):
    action: str    # register | unregister
    event_id: int


class DeleteAccountCB(CallbackData, prefix="del_acc"):
    action: str    # confirm | cancel
# Home / main hub
# ---------------------------------------------------------------------------

def home_keyboard() -> InlineKeyboardMarkup:
    """Main hub shown after onboarding and on /menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👤  Профиль",      callback_data=NavCB(page="profile"))
    builder.button(text="📊  Статистика",   callback_data=NavCB(page="stats"))
    builder.button(text="🏆  Достижения",   callback_data=NavCB(page="achievements"))
    builder.button(text="📅  Мероприятия",  callback_data=NavCB(page="events"))
    builder.button(text="🔒  Приватность",  callback_data=NavCB(page="privacy"))
    builder.button(text="❓  Помощь",       callback_data=NavCB(page="help"))
    builder.button(text="❌  Удалить аккаунт", callback_data=NavCB(page="delete_acc"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def _back_row(builder: InlineKeyboardBuilder) -> None:
    """Append a standard back-to-home row."""
    builder.row()
    builder.button(text="← Главная", callback_data=NavCB(page="home"))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️  Обновить работу",   callback_data=NavCB(page="update_job"))
    builder.button(text="🏆  Мои достижения",    callback_data=NavCB(page="achievements"))
    _back_row(builder)
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------

def achievements_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _back_row(builder)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def stats_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _back_row(builder)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------

def privacy_keyboard(current_level: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_level != 1:
        builder.button(
            text="🔓  Стандартная приватность",
            callback_data=PrivacyToggleCB(level=1),
        )
    if current_level != 2:
        builder.button(
            text="🔒  Максимальная приватность",
            callback_data=PrivacyToggleCB(level=2),
        )
    _back_row(builder)
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def events_keyboard(
    events: list[dict],
    user_registered_ids: set[int],
    page: int = 0,
    has_next: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for event in events:
        registered = event["id"] in user_registered_ids
        label = f"{'✅' if registered else '📌'}  {event['title']}"
        builder.button(
            text=label,
            callback_data=EventActionCB(action="view", event_id=event["id"]),
        )
    
    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=NavCB(page="events", subpage=page-1).pack())
        )
    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=NavCB(page="events", subpage=page+1).pack())
        )
    
    builder.adjust(1)
    if nav_buttons:
        builder.row(*nav_buttons)
        
    _back_row(builder)
    return builder.as_markup()


def event_details_keyboard(event_id: int, registered: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    action = "unregister" if registered else "register"
    label = "Отменить запись ❌" if registered else "Записаться ✅"
    builder.button(
        text=label,
        callback_data=EventActionCB(action=action, event_id=event_id)
    )
    builder.row(InlineKeyboardButton(text="⬅️ К списку", callback_data=NavCB(page="events").pack()))
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

def help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _back_row(builder)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Delete Account
# ---------------------------------------------------------------------------

def delete_account_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⚠️ Да, удалить навсегда", callback_data=DeleteAccountCB(action="confirm"))
    builder.button(text="Отмена", callback_data=DeleteAccountCB(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()
