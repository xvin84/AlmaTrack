"""
Keyboards for the onboarding flow.

Faculty tree navigation:
  - Loaded from data/faculties.json
  - path + page live in FSM data (avoids 64-byte callback limit)
  - Callbacks only carry action + optional index/direction
"""
from __future__ import annotations

import json
from pathlib import Path

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_FACULTIES_PATH = Path(__file__).parent.parent.parent / "data" / "faculties.json"
_faculty_tree_cache: list[dict] | None = None


# ---------------------------------------------------------------------------
# Faculty tree helpers
# ---------------------------------------------------------------------------

def load_faculty_tree() -> list[dict]:
    global _faculty_tree_cache
    if _faculty_tree_cache is None:
        with open(_FACULTIES_PATH, encoding="utf-8") as f:
            _faculty_tree_cache = json.load(f)
    return _faculty_tree_cache


def _navigate_to(tree: list[dict], path: list[int]) -> list[dict]:
    current = tree
    for idx in path:
        current = current[idx]["children"]
    return current


def _build_breadcrumb(tree: list[dict], path: list[int]) -> str:
    if not path:
        return "📚 Выбери факультет"
    parts: list[str] = []
    current = tree
    for idx in path:
        parts.append(current[idx]["name"])
        current = current[idx].get("children", [])
    return "📚 " + " › ".join(parts)


def get_faculty_breadcrumb_text(path: list[int], tree: list[dict] | None = None) -> str:
    if tree is None:
        tree = load_faculty_tree()
    return _build_breadcrumb(tree, path)


# ---------------------------------------------------------------------------
# CallbackData schemas
# ---------------------------------------------------------------------------

class FacNavCB(CallbackData, prefix="fac"):
    """
    action: enter | select | back | page | root | noop
    """
    action: str
    index: int = -1
    direction: int = 0


class YearCB(CallbackData, prefix="year"):
    action: str       # select | page
    value: int = 0
    direction: int = 0


class RoleCB(CallbackData, prefix="role"):
    role: str         # student | alumni


class EmploymentStatusCB(CallbackData, prefix="emp_status"):
    status: str       # working | searching | none


class WorkCityCB(CallbackData, prefix="city"):
    city: str


class WorkFormatCB(CallbackData, prefix="fmt"):
    fmt: str          # office | remote | hybrid


class PositionLevelCB(CallbackData, prefix="lvl"):
    level: str        # intern | junior | middle | senior | lead | cto


class ConfirmCB(CallbackData, prefix="confirm"):
    answer: str       # yes | edit


class EditFieldCB(CallbackData, prefix="edit_fld"):
    field: str        # full_name | role | faculty | enrollment_year | graduation_year |
                      # employment_status | company_name | work_city |
                      # work_format | position_title | position_level


class CancelEditCB(CallbackData, prefix="cancel_edit"):
    pass


# ---------------------------------------------------------------------------
# Faculty tree keyboard
# ---------------------------------------------------------------------------

ITEMS_PER_PAGE: int = 5
YEAR_PER_PAGE: int = 6


def get_faculty_keyboard(
    path: list[int],
    page: int,
    tree: list[dict] | None = None,
    *,
    is_editing: bool = False,
) -> InlineKeyboardMarkup:
    if tree is None:
        tree = load_faculty_tree()

    current_level = _navigate_to(tree, path)
    total = len(current_level)
    total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    visible = current_level[start: start + ITEMS_PER_PAGE]

    builder = InlineKeyboardBuilder()

    for local_i, item in enumerate(visible):
        real_idx = start + local_i
        has_children = bool(item.get("children"))
        if has_children:
            builder.button(
                text=f"📁  {item['name']}",
                callback_data=FacNavCB(action="enter", index=real_idx),
            )
        else:
            builder.button(
                text=f"✅  {item['name']}",
                callback_data=FacNavCB(action="select", index=real_idx),
            )
    builder.adjust(1)

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="◀️", callback_data=FacNavCB(action="page", direction=-1).pack()
        ))
    if len(path) == 1:
        nav.append(InlineKeyboardButton(
            text="🏠 В начало", callback_data=FacNavCB(action="root").pack()
        ))
    elif len(path) > 1:
        nav.append(InlineKeyboardButton(
            text="⬆️ Назад", callback_data=FacNavCB(action="back").pack()
        ))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            text="▶️", callback_data=FacNavCB(action="page", direction=1).pack()
        ))
    if nav:
        builder.row(*nav)

    if total_pages > 1:
        builder.row(InlineKeyboardButton(
            text=f"· {page + 1} / {total_pages} ·",
            callback_data=FacNavCB(action="noop").pack(),
        ))

    # Cancel button when editing a single field
    if is_editing:
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена", callback_data=CancelEditCB().pack()
        ))

    return builder.as_markup()


# ---------------------------------------------------------------------------
# Year keyboard
# ---------------------------------------------------------------------------

def get_year_keyboard(
    page: int,
    *,
    year_min: int,
    year_max: int,
    is_editing: bool = False,
) -> InlineKeyboardMarkup:
    years = list(range(year_max, year_min - 1, -1))
    total = len(years)
    total_pages = max(1, (total + YEAR_PER_PAGE - 1) // YEAR_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * YEAR_PER_PAGE
    visible = years[start: start + YEAR_PER_PAGE]

    builder = InlineKeyboardBuilder()
    for year in visible:
        builder.button(text=str(year), callback_data=YearCB(action="select", value=year))
    builder.adjust(3)

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="◀️ Раньше", callback_data=YearCB(action="page", direction=-1).pack()
        ))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            text="Позже ▶️", callback_data=YearCB(action="page", direction=1).pack()
        ))
    if nav:
        builder.row(*nav)

    if is_editing:
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена", callback_data=CancelEditCB().pack()
        ))

    return builder.as_markup()


# ---------------------------------------------------------------------------
# Simple keyboards
# ---------------------------------------------------------------------------

def role_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎓  Я студент", callback_data=RoleCB(role="student"))
    builder.button(text="📋  Я выпускник", callback_data=RoleCB(role="alumni"))
    builder.adjust(2)
    return builder.as_markup()


def employment_status_keyboard(*, is_editing: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅  Да, работаю", callback_data=EmploymentStatusCB(status="working"))
    builder.button(text="🔍  Ищу работу", callback_data=EmploymentStatusCB(status="searching"))
    builder.button(text="❌  Нет", callback_data=EmploymentStatusCB(status="none"))
    builder.adjust(1)
    if is_editing:
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена", callback_data=CancelEditCB().pack()
        ))
    return builder.as_markup()


def work_city_keyboard(*, is_editing: bool = False) -> InlineKeyboardMarkup:
    cities = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург", "Другой"]
    builder = InlineKeyboardBuilder()
    for city in cities:
        builder.button(text=city, callback_data=WorkCityCB(city=city))
    builder.adjust(2)
    if is_editing:
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена", callback_data=CancelEditCB().pack()
        ))
    return builder.as_markup()


def work_format_keyboard(*, is_editing: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏢  Офис", callback_data=WorkFormatCB(fmt="office"))
    builder.button(text="🏠  Удалёнка", callback_data=WorkFormatCB(fmt="remote"))
    builder.button(text="🔀  Гибрид", callback_data=WorkFormatCB(fmt="hybrid"))
    builder.adjust(3)
    if is_editing:
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена", callback_data=CancelEditCB().pack()
        ))
    return builder.as_markup()


def position_level_keyboard(*, is_editing: bool = False) -> InlineKeyboardMarkup:
    levels = [
        ("👶  Стажёр", "intern"),
        ("🌱  Junior", "junior"),
        ("⚡  Middle", "middle"),
        ("🔥  Senior", "senior"),
        ("👑  Lead", "lead"),
        ("🚀  CTO / C-level", "cto"),
    ]
    builder = InlineKeyboardBuilder()
    for label, value in levels:
        builder.button(text=label, callback_data=PositionLevelCB(level=value))
    builder.adjust(2)
    if is_editing:
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена", callback_data=CancelEditCB().pack()
        ))
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Single cancel button — used during free-text input steps in edit mode."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✖️ Отмена", callback_data=CancelEditCB())
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅  Всё верно!", callback_data=ConfirmCB(answer="yes"))
    builder.button(text="✏️  Изменить поле", callback_data=ConfirmCB(answer="edit"))
    builder.adjust(1)
    return builder.as_markup()


def edit_fields_keyboard(data: dict) -> InlineKeyboardMarkup:
    """
    Show only the fields that are actually filled in FSM data.
    User picks one field to re-enter.
    """
    ROLE_LABELS = {"student": "Студент 🎓", "alumni": "Выпускник 📋"}
    FORMAT_LABELS = {"office": "Офис 🏢", "remote": "Удалёнка 🏠", "hybrid": "Гибрид 🔀"}
    LEVEL_LABELS = {
        "intern": "Стажёр", "junior": "Junior", "middle": "Middle",
        "senior": "Senior", "lead": "Lead", "cto": "CTO",
    }

    builder = InlineKeyboardBuilder()

    if data.get("full_name"):
        builder.button(
            text=f"👤  ФИО: {data['full_name']}",
            callback_data=EditFieldCB(field="full_name"),
        )
    if data.get("role"):
        builder.button(
            text=f"🎭  Роль: {ROLE_LABELS.get(data['role'], data['role'])}",
            callback_data=EditFieldCB(field="role"),
        )
    if data.get("faculty"):
        builder.button(
            text=f"🎓  Факультет: {data['faculty']}",
            callback_data=EditFieldCB(field="faculty"),
        )
    if data.get("enrollment_year"):
        builder.button(
            text=f"📅  Год поступления: {data['enrollment_year']}",
            callback_data=EditFieldCB(field="enrollment_year"),
        )
    if data.get("graduation_year"):
        builder.button(
            text=f"🏁  Год выпуска: {data['graduation_year']}",
            callback_data=EditFieldCB(field="graduation_year"),
        )
    if data.get("employment_status"):
        status_map = {"working": "Работаю ✅", "searching": "Ищу работу 🔍", "none": "Не работаю ❌"}
        builder.button(
            text=f"💼  Занятость: {status_map.get(data['employment_status'], '')}",
            callback_data=EditFieldCB(field="employment_status"),
        )
    if data.get("company_name"):
        builder.button(
            text=f"🏢  Компания: {data['company_name']}",
            callback_data=EditFieldCB(field="company_name"),
        )
    if data.get("work_city"):
        builder.button(
            text=f"🌆  Город: {data['work_city']}",
            callback_data=EditFieldCB(field="work_city"),
        )
    if data.get("work_format"):
        builder.button(
            text=f"🔀  Формат: {FORMAT_LABELS.get(data['work_format'], '')}",
            callback_data=EditFieldCB(field="work_format"),
        )
    if data.get("position_title"):
        builder.button(
            text=f"👔  Должность: {data['position_title']}",
            callback_data=EditFieldCB(field="position_title"),
        )
    if data.get("position_level"):
        builder.button(
            text=f"📈  Уровень: {LEVEL_LABELS.get(data['position_level'], '')}",
            callback_data=EditFieldCB(field="position_level"),
        )

    builder.adjust(1)
    builder.row(InlineKeyboardButton(
        text="↩️  Назад к проверке", callback_data=CancelEditCB().pack()
    ))
    return builder.as_markup()
