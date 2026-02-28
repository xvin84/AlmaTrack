"""
/start handler + onboarding FSM.

Bug fixes vs v2:
  - "Continue" restores the exact current FSM screen instead of showing
    a dead-end message.
  - Switching employment_status back to "working" in edit mode after it was
    cleared no longer shows None values — re-enters job detail flow.

After onboarding the "home" inline message is sent (no ReplyKeyboard).
"""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.base import get_session
from db.crud import add_xp, award_badge, create_employment, create_user, get_user

def normalize_text(val: str) -> str:
    if not val:
        return val
    val = val.strip().title()
    mapping = {
        "Yandex": "Яндекс", "Яндекс": "Яндекс",
        "Vk": "Vk", "Вконтакте": "Vk", "Vk.Com": "Vk", "Вк": "Vk",
        "Тинькофф": "Т-Банк", "Tinkoff": "Т-Банк", "Тбанк": "Т-Банк", "Т Банк": "Т-Банк",
        "Сбербанк": "Сбер", "Sber": "Сбер", "Сбер": "Сбер",
        "Ростов": "Ростов-на-Дону", "Ростов-На-Дону": "Ростов-на-Дону",
        "Питер": "Санкт-Петербург", "Спб": "Санкт-Петербург",
        "Мск": "Москва"
    }
    return mapping.get(val, val)

from bot.config import get_settings
from bot.keyboards import (
    CancelEditCB,
    ConfirmCB,
    EditFieldCB,
    EmploymentStatusCB,
    FacNavCB,
    PositionLevelCB,
    RoleCB,
    WorkCityCB,
    WorkFormatCB,
    YearCB,
    cancel_keyboard,
    confirm_keyboard,
    edit_fields_keyboard,
    employment_status_keyboard,
    get_faculty_breadcrumb_text,
    get_faculty_keyboard,
    get_year_keyboard,
    home_keyboard,
    load_faculty_tree,
    position_level_keyboard,
    role_keyboard,
    work_city_keyboard,
    work_format_keyboard,
)
from bot.states import OnboardingFSM
from core.emoji import E

router = Router(name="onboarding")
cfg = get_settings()

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

ROLE_LABELS    = {"student": "Студент 🎓", "alumni": "Выпускник 📋"}
FORMAT_LABELS  = {"office": "Офис 🏢", "remote": "Удалёнка 🏠", "hybrid": "Гибрид 🔀"}
LEVEL_LABELS   = {
    "intern": "Стажёр 👶", "junior": "Junior 🌱", "middle": "Middle ⚡",
    "senior": "Senior 🔥", "lead": "Lead 👑",   "cto": "CTO/C-level 🚀",
}

# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------


async def _delete(bot: Bot, chat_id: int, msg_id: int | None) -> None:
    if not msg_id:
        return
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


async def _set_main(
    bot: Bot, chat_id: int, state: FSMContext, text: str, keyboard=None
) -> None:
    """Edit tracked bot message, or send a new one if editing fails."""
    data = await state.get_data()
    msg_id: int | None = data.get("bot_msg_id")
    try:
        if not msg_id:
            raise ValueError
        await bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id,
            text=text, reply_markup=keyboard, parse_mode="HTML",
        )
    except Exception:
        sent = await bot.send_message(
            chat_id=chat_id, text=text,
            reply_markup=keyboard, parse_mode="HTML",
        )
        await state.update_data(bot_msg_id=sent.message_id)


# ---------------------------------------------------------------------------
# /start guard
# ---------------------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        user = await get_user(message.from_user.id, session)
        if user:
            await _delete(message.bot, message.chat.id, message.message_id)
            if user.status == "pending":
                await message.answer("⏳ <i>Твоя анкета находится на проверке у администратора.</i>", parse_mode="HTML")
            else:
                await message.answer("🏠 <b>Главное меню</b>", reply_markup=home_keyboard(), parse_mode="HTML")
            return

    current_state = await state.get_state()

    if current_state and current_state.startswith("OnboardingFSM:"):
        data = await state.get_data()
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄  Начать заново", callback_data="restart:yes")
        builder.button(text="↩️  Продолжить",    callback_data="restart:no")
        builder.adjust(2)

        # Delete old main message, send guard prompt
        await _delete(message.bot, message.chat.id, data.get("bot_msg_id"))
        await _delete(message.bot, message.chat.id, message.message_id)
        sent = await message.answer(
            "⚠️ <b>Регистрация уже идёт.</b>\n\n"
            "Начать заново или продолжить?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
        await state.update_data(bot_msg_id=sent.message_id)
        return

    await _launch_onboarding(message, state)


@router.callback_query(F.data.in_({"restart:yes", "restart:no"}))
async def process_restart(call: CallbackQuery, state: FSMContext) -> None:
    if call.data == "restart:no":
        # ✅ FIX: restore the actual current screen instead of dead-end message
        current_state = await state.get_state()
        await call.answer("Продолжаем 👍")
        await _restore_screen(call.bot, call.message.chat.id, state, current_state)
        return

    await call.answer("Начинаем заново 🔄")
    await _launch_onboarding(call.message, state, edit=True)


async def _restore_screen(
    bot: Bot, chat_id: int, state: FSMContext, state_name: str | None
) -> None:
    """Re-render the UI for whichever FSM state is currently active."""
    if state_name is None:
        return

    data = await state.get_data()
    is_editing: bool = data.get("is_editing", False)

    match state_name.removeprefix("OnboardingFSM:"):
        case "role":
            await _set_main(bot, chat_id, state,
                "👤 Выбери роль:\n\n<i>Шаг 1 из 5</i>",
                role_keyboard())

        case "faculty_browse":
            tree = load_faculty_tree()
            path = data.get("fac_path", [])
            page = data.get("fac_page", 0)
            await _set_main(bot, chat_id, state,
                f"{get_faculty_breadcrumb_text(path, tree)}\n\n<i>Шаг 2 из 5</i>",
                get_faculty_keyboard(path, page, tree, is_editing=is_editing))

        case "enrollment_year":
            await _set_main(bot, chat_id, state,
                "📅 Год поступления?\n\n<i>Шаг 3 из 5</i>",
                get_year_keyboard(data.get("year_page", 0),
                    year_min=cfg.enrollment_year_min,
                    year_max=cfg.enrollment_year_max,
                    is_editing=is_editing))

        case "graduation_year":
            await _set_main(bot, chat_id, state,
                "🏁 Год выпуска?\n\n<i>Шаг 3б из 5</i>",
                get_year_keyboard(data.get("year_page", 0),
                    year_min=cfg.enrollment_year_min,
                    year_max=cfg.enrollment_year_max,
                    is_editing=is_editing))

        case "employment_status":
            await _set_main(bot, chat_id, state,
                "💼 Ты сейчас работаешь?\n\n<i>Шаг 4 из 5</i>",
                employment_status_keyboard(is_editing=is_editing))

        case "company_name":
            await _set_main(bot, chat_id, state,
                "🏢 Название компании?\n\n<i>Шаг 5 из 5  ·  введи текстом</i>",
                cancel_keyboard() if is_editing else None)

        case "work_city":
            await _set_main(bot, chat_id, state,
                "🌆 Город?\n\n<i>Шаг 5 из 5</i>",
                work_city_keyboard(is_editing=is_editing))

        case "work_format":
            await _set_main(bot, chat_id, state,
                "🔀 Формат работы?\n\n<i>Шаг 5 из 5</i>",
                work_format_keyboard(is_editing=is_editing))

        case "position_title":
            await _set_main(bot, chat_id, state,
                "👔 Должность?\n\n<i>Шаг 5 из 5  ·  введи текстом</i>",
                cancel_keyboard() if is_editing else None)

        case "position_level":
            await _set_main(bot, chat_id, state,
                "📈 Уровень?\n\n<i>Шаг 5 из 5</i>",
                position_level_keyboard(is_editing=is_editing))

        case "confirm":
            await _show_confirm(bot, chat_id, state)

        case "editing_field":
            await _set_main(bot, chat_id, state,
                "✏️ <b>Что хочешь изменить?</b>",
                edit_fields_keyboard(data))


async def _launch_onboarding(
    message: Message, state: FSMContext, *, edit: bool = False
) -> None:
    await state.clear()
    await state.set_state(OnboardingFSM.role)

    text = (
        f"👋 Привет! Я <b>AlmaTrack</b> — карьерный дневник студента.\n\n"
        "Помогаю отслеживать прогресс и сравнивать себя с однокурсниками.\n\n"
        f"{E.lock} <b>Вуз НЕ видит:</b> имя, username, зарплату\n"
        "📊 <b>Вуз видит:</b> только обезличенную статистику\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "<i>Шаг 1 из 5 · Кто ты?</i>"
    )
    if edit:
        try:
            await message.edit_text(text, reply_markup=role_keyboard(), parse_mode="HTML")
            await state.update_data(bot_msg_id=message.message_id)
            return
        except Exception:
            pass

    await _delete(message.bot, message.chat.id, message.message_id)
    sent = await message.answer(text, reply_markup=role_keyboard(), parse_mode="HTML")
    await state.update_data(bot_msg_id=sent.message_id)


# ---------------------------------------------------------------------------
# Step 1 — Role
# ---------------------------------------------------------------------------


@router.callback_query(OnboardingFSM.role, RoleCB.filter())
async def process_role(call: CallbackQuery, callback_data: RoleCB, state: FSMContext) -> None:
    await state.update_data(role=callback_data.role, fac_path=[], fac_page=0)
    await state.set_state(OnboardingFSM.faculty_browse)

    tree = load_faculty_tree()
    await _set_main(
        call.bot, call.message.chat.id, state,
        f"{get_faculty_breadcrumb_text([], tree)}\n\n"
        "📁 Папка — категория   ✅ — конкретный факультет\n\n"
        "<i>Шаг 2 из 5</i>",
        get_faculty_keyboard([], 0, tree),
    )
    await call.answer(ROLE_LABELS[callback_data.role])


# ---------------------------------------------------------------------------
# Step 2 — Faculty tree
# ---------------------------------------------------------------------------


@router.callback_query(OnboardingFSM.faculty_browse, FacNavCB.filter())
async def process_faculty_nav(
    call: CallbackQuery, callback_data: FacNavCB, state: FSMContext
) -> None:
    data = await state.get_data()
    path: list[int] = data.get("fac_path", [])
    page: int = data.get("fac_page", 0)
    is_editing: bool = data.get("is_editing", False)
    tree = load_faculty_tree()

    if callback_data.action == "noop":
        await call.answer()
        return
    elif callback_data.action == "enter":
        path, page = path + [callback_data.index], 0
    elif callback_data.action == "back":
        path, page = path[:-1], 0
    elif callback_data.action == "root":
        path, page = [], 0
    elif callback_data.action == "page":
        page += callback_data.direction
    elif callback_data.action == "select":
        current = tree
        for idx in path:
            current = current[idx]["children"]
        selected = current[callback_data.index]["name"]
        await state.update_data(faculty=selected, fac_path=[], fac_page=0)
        await call.answer(f"✅ {selected}")
        if is_editing:
            await _show_confirm(call.bot, call.message.chat.id, state)
        else:
            await _go_enrollment_year(call.bot, call.message.chat.id, state)
        return

    await state.update_data(fac_path=path, fac_page=page)
    await _set_main(
        call.bot, call.message.chat.id, state,
        f"{get_faculty_breadcrumb_text(path, tree)}\n\n"
        "📁 Папка — категория   ✅ — конкретный факультет\n\n"
        "<i>Шаг 2 из 5</i>",
        get_faculty_keyboard(path, page, tree, is_editing=is_editing),
    )
    await call.answer()


async def _go_enrollment_year(bot: Bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(OnboardingFSM.enrollment_year)
    await state.update_data(year_page=0)
    await _set_main(
        bot, chat_id, state,
        f"✅ Факультет: <b>{data['faculty']}</b>\n\n"
        "📅 Год поступления?\n\n<i>Шаг 3 из 5</i>",
        get_year_keyboard(0, year_min=cfg.enrollment_year_min, year_max=cfg.enrollment_year_max),
    )


# ---------------------------------------------------------------------------
# Step 3 — Enrollment year
# ---------------------------------------------------------------------------


@router.callback_query(OnboardingFSM.enrollment_year, YearCB.filter())
async def process_enrollment_year(
    call: CallbackQuery, callback_data: YearCB, state: FSMContext
) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)

    if callback_data.action == "page":
        page = data.get("year_page", 0) + callback_data.direction
        await state.update_data(year_page=page)
        await call.message.edit_reply_markup(reply_markup=get_year_keyboard(
            page, year_min=cfg.enrollment_year_min,
            year_max=cfg.enrollment_year_max, is_editing=is_editing,
        ))
        await call.answer()
        return

    await state.update_data(enrollment_year=callback_data.value)
    await call.answer(f"📅 {callback_data.value}")

    if is_editing:
        await _show_confirm(call.bot, call.message.chat.id, state)
        return

    if data.get("role") == "alumni":
        await state.set_state(OnboardingFSM.graduation_year)
        await state.update_data(year_page=0)
        await _set_main(
            call.bot, call.message.chat.id, state,
            f"✅ Поступление: <b>{callback_data.value}</b>\n\n"
            "🏁 Год выпуска?\n\n<i>Шаг 3б из 5</i>",
            get_year_keyboard(0, year_min=cfg.enrollment_year_min, year_max=cfg.enrollment_year_max),
        )
    else:
        await _go_employment_status(call.bot, call.message.chat.id, state)


# ---------------------------------------------------------------------------
# Step 3б — Graduation year (alumni)
# ---------------------------------------------------------------------------


@router.callback_query(OnboardingFSM.graduation_year, YearCB.filter())
async def process_graduation_year(
    call: CallbackQuery, callback_data: YearCB, state: FSMContext
) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)

    if callback_data.action == "page":
        page = data.get("year_page", 0) + callback_data.direction
        await state.update_data(year_page=page)
        await call.message.edit_reply_markup(reply_markup=get_year_keyboard(
            page, year_min=cfg.enrollment_year_min,
            year_max=cfg.enrollment_year_max, is_editing=is_editing,
        ))
        await call.answer()
        return

    await state.update_data(graduation_year=callback_data.value)
    await call.answer(f"🏁 {callback_data.value}")
    if is_editing:
        await _show_confirm(call.bot, call.message.chat.id, state)
    else:
        await _go_employment_status(call.bot, call.message.chat.id, state)


async def _go_employment_status(bot: Bot, chat_id: int, state: FSMContext) -> None:
    await state.set_state(OnboardingFSM.employment_status)
    await _set_main(bot, chat_id, state,
        "💼 Ты сейчас работаешь?\n\n<i>Шаг 4 из 5</i>",
        employment_status_keyboard(),
    )


# ---------------------------------------------------------------------------
# Step 4 — Employment status
# ---------------------------------------------------------------------------


@router.callback_query(OnboardingFSM.employment_status, EmploymentStatusCB.filter())
async def process_employment_status(
    call: CallbackQuery, callback_data: EmploymentStatusCB, state: FSMContext
) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    await state.update_data(employment_status=callback_data.status)

    labels = {"working": "Работаю ✅", "searching": "Ищу работу 🔍", "none": "Не работаю ❌"}
    await call.answer(labels[callback_data.status])

    if callback_data.status == "working":
        # ✅ FIX: if job fields were cleared (None), always re-enter them
        job_fields_empty = not data.get("company_name")
        if is_editing and not job_fields_empty:
            await _show_confirm(call.bot, call.message.chat.id, state)
        else:
            # Go through job input flow (fresh or re-entering after clear)
            await state.set_state(OnboardingFSM.company_name)
            await _set_main(
                call.bot, call.message.chat.id, state,
                "🏢 Название компании?\n\n<i>Шаг 5 из 5  ·  введи текстом</i>",
                cancel_keyboard() if is_editing else None,
            )
    else:
        # Clear job fields when switching away from "working"
        await state.update_data(
            company_name=None, work_city=None, work_format=None,
            position_title=None, position_level=None,
        )
        if is_editing:
            await _show_confirm(call.bot, call.message.chat.id, state)
        else:
            await _show_confirm(call.bot, call.message.chat.id, state)


# ---------------------------------------------------------------------------
# Step 5 — Job details
# ---------------------------------------------------------------------------


@router.message(OnboardingFSM.company_name, F.text)
async def process_company_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    val = normalize_text(message.text)
    await state.update_data(company_name=val)
    await state.set_state(OnboardingFSM.work_city)
    await _delete(message.bot, message.chat.id, message.message_id)
    await _set_main(
        message.bot, message.chat.id, state,
        f"✅ Компания: <b>{val}</b>\n\n"
        "🌆 Город?\n\n<i>Шаг 5 из 5</i>",
        work_city_keyboard(is_editing=is_editing),
    )


@router.callback_query(OnboardingFSM.work_city, WorkCityCB.filter())
async def process_work_city(
    call: CallbackQuery, callback_data: WorkCityCB, state: FSMContext
) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)

    if callback_data.city == "Другой":
        await state.update_data(_awaiting_custom_city=True)
        await _set_main(call.bot, call.message.chat.id, state,
            "✏️ Введи название города:\n\n<i>Шаг 5 из 5  ·  введи текстом</i>",
            cancel_keyboard() if is_editing else None,
        )
        await call.answer()
        return

    await state.update_data(work_city=callback_data.city)
    await call.answer(f"🌆 {callback_data.city}")
    if is_editing:
        await _show_confirm(call.bot, call.message.chat.id, state)
    else:
        await _go_work_format(call.bot, call.message.chat.id, state)


@router.message(OnboardingFSM.work_city, F.text)
async def process_custom_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("_awaiting_custom_city"):
        return
    is_editing = data.get("is_editing", False)
    val = normalize_text(message.text)
    await state.update_data(work_city=val, _awaiting_custom_city=False)
    await _delete(message.bot, message.chat.id, message.message_id)
    if is_editing:
        await _show_confirm(message.bot, message.chat.id, state)
    else:
        await _go_work_format(message.bot, message.chat.id, state)


async def _go_work_format(bot: Bot, chat_id: int, state: FSMContext) -> None:
    await state.set_state(OnboardingFSM.work_format)
    await _set_main(bot, chat_id, state,
        "🔀 Формат работы?\n\n<i>Шаг 5 из 5</i>",
        work_format_keyboard(),
    )


@router.callback_query(OnboardingFSM.work_format, WorkFormatCB.filter())
async def process_work_format(
    call: CallbackQuery, callback_data: WorkFormatCB, state: FSMContext
) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    await state.update_data(work_format=callback_data.fmt)
    await call.answer(FORMAT_LABELS[callback_data.fmt])
    if is_editing:
        await _show_confirm(call.bot, call.message.chat.id, state)
    else:
        await state.set_state(OnboardingFSM.position_title)
        await _set_main(call.bot, call.message.chat.id, state,
            "👔 Твоя должность?\n<i>Например: Python-разработчик…</i>\n\n"
            "<i>Шаг 5 из 5  ·  введи текстом</i>",
        )


@router.message(OnboardingFSM.position_title, F.text)
async def process_position_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    await state.update_data(position_title=title)
    await _delete(message.bot, message.chat.id, message.message_id)
    if is_editing:
        await _show_confirm(message.bot, message.chat.id, state)
    else:
        await state.set_state(OnboardingFSM.position_level)
        await _set_main(message.bot, message.chat.id, state,
            f"✅ Должность: <b>{title}</b>\n\n"
            "📈 Твой уровень?\n\n<i>Шаг 5 из 5</i>",
            position_level_keyboard(),
        )


@router.callback_query(OnboardingFSM.position_level, PositionLevelCB.filter())
async def process_position_level(
    call: CallbackQuery, callback_data: PositionLevelCB, state: FSMContext
) -> None:
    await state.update_data(position_level=callback_data.level)
    await call.answer(LEVEL_LABELS[callback_data.level])
    await _show_confirm(call.bot, call.message.chat.id, state)


# ---------------------------------------------------------------------------
# Confirm screen
# ---------------------------------------------------------------------------


async def _show_confirm(bot: Bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(OnboardingFSM.confirm)
    await state.update_data(is_editing=False, current_edit_field=None)
    await _set_main(bot, chat_id, state, _build_summary_card(data), confirm_keyboard())


@router.callback_query(OnboardingFSM.confirm, ConfirmCB.filter())
async def process_confirm(
    call: CallbackQuery, callback_data: ConfirmCB, state: FSMContext
) -> None:
    if callback_data.answer == "edit":
        data = await state.get_data()
        await state.set_state(OnboardingFSM.editing_field)
        await _set_main(
            call.bot, call.message.chat.id, state,
            "✏️ <b>Что хочешь изменить?</b>\n\nВыбери поле:",
            edit_fields_keyboard(data),
        )
        await call.answer()
    else:
        await call.answer(f"{E.sparkles} Отлично!")
        await _finalize_onboarding(call, state)


# ---------------------------------------------------------------------------
# Edit mode
# ---------------------------------------------------------------------------


@router.callback_query(OnboardingFSM.editing_field, EditFieldCB.filter())
async def process_edit_field_select(
    call: CallbackQuery, callback_data: EditFieldCB, state: FSMContext
) -> None:
    field = callback_data.field
    await state.update_data(is_editing=True, current_edit_field=field)
    await call.answer()

    match field:
        case "role":
            await state.set_state(OnboardingFSM.role)
            await _set_main(call.bot, call.message.chat.id, state,
                "👤 Выбери роль:", role_keyboard())

        case "faculty":
            await state.set_state(OnboardingFSM.faculty_browse)
            await state.update_data(fac_path=[], fac_page=0)
            tree = load_faculty_tree()
            await _set_main(call.bot, call.message.chat.id, state,
                f"{get_faculty_breadcrumb_text([], tree)}\n\n📁 Выбери новый факультет:",
                get_faculty_keyboard([], 0, tree, is_editing=True))

        case "enrollment_year":
            await state.set_state(OnboardingFSM.enrollment_year)
            await state.update_data(year_page=0)
            await _set_main(call.bot, call.message.chat.id, state,
                "📅 Год поступления:",
                get_year_keyboard(0, year_min=cfg.enrollment_year_min,
                    year_max=cfg.enrollment_year_max, is_editing=True))

        case "graduation_year":
            await state.set_state(OnboardingFSM.graduation_year)
            await state.update_data(year_page=0)
            await _set_main(call.bot, call.message.chat.id, state,
                "🏁 Год выпуска:",
                get_year_keyboard(0, year_min=cfg.enrollment_year_min,
                    year_max=cfg.enrollment_year_max, is_editing=True))

        case "employment_status":
            await state.set_state(OnboardingFSM.employment_status)
            await _set_main(call.bot, call.message.chat.id, state,
                "💼 Занятость:", employment_status_keyboard(is_editing=True))

        case "company_name":
            await state.set_state(OnboardingFSM.company_name)
            await _set_main(call.bot, call.message.chat.id, state,
                "🏢 Новое название компании:\n\n<i>введи текстом</i>",
                cancel_keyboard())

        case "work_city":
            await state.set_state(OnboardingFSM.work_city)
            await _set_main(call.bot, call.message.chat.id, state,
                "🌆 Новый город:", work_city_keyboard(is_editing=True))

        case "work_format":
            await state.set_state(OnboardingFSM.work_format)
            await _set_main(call.bot, call.message.chat.id, state,
                "🔀 Формат работы:", work_format_keyboard(is_editing=True))

        case "position_title":
            await state.set_state(OnboardingFSM.position_title)
            await _set_main(call.bot, call.message.chat.id, state,
                "👔 Новая должность:\n\n<i>введи текстом</i>",
                cancel_keyboard())

        case "position_level":
            await state.set_state(OnboardingFSM.position_level)
            await _set_main(call.bot, call.message.chat.id, state,
                "📈 Уровень:", position_level_keyboard(is_editing=True))


@router.callback_query(CancelEditCB.filter())
async def process_cancel_edit(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer("↩️ Отмена")
    await state.update_data(is_editing=False, current_edit_field=None)
    await _show_confirm(call.bot, call.message.chat.id, state)


# ---------------------------------------------------------------------------
# Finalize
# ---------------------------------------------------------------------------


async def _finalize_onboarding(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")

    user_id = call.from_user.id
    full_name = call.from_user.full_name
    username = call.from_user.username
    
    try:
        async with get_session() as session:
            from db.crud import get_user
            existing_user = await get_user(user_id, session)
            if existing_user:
                await state.clear()
                await _delete(call.bot, call.message.chat.id, bot_msg_id)
                await call.message.answer("✅ Твоя анкета уже зарегистрирована в системе.")
                return

            # Create user
            user = await create_user(
                telegram_id=user_id,
                full_name=full_name,
                username=username,
                faculty=data.get("faculty"),
                enrollment_year=data.get("enrollment_year"),
                graduation_year=data.get("graduation_year"),
                is_alumni=(data.get("role") == "alumni"),
                session=session
            )

            status = data.get("employment_status")
            if status == "working":
                await create_employment(
                    user_id=user_id,
                    company_name=data.get("company_name"),
                    city=data.get("work_city"),
                    work_format=data.get("work_format"),
                    position_title=data.get("position_title"),
                    position_level=data.get("position_level"),
                    session=session
                )
                
            # Award initial XP and badge
            await add_xp(user_id, 50, session)
            await award_badge(user_id, "FIRST_STEP", session)
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Failed to create user during onboarding")
        await call.answer("Произошла ошибка при сохранении данных", show_alert=True)
        return

    await state.clear()
    await _delete(call.bot, call.message.chat.id, bot_msg_id)

    await call.message.answer(
        f"{E.sparkles} <b>Твоя анкета отправлена на проверку!</b>\n\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{E.medal}  Бейдж <b>«Первый шаг»</b> получен!\n"
        f"{E.star}  <b>+50 XP</b>\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "⏳ <i>Ожидай одобрения администратором. Пока заявка проверяется, функционал бота ограничен.</i>",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_summary_card(data: dict) -> str:
    role   = ROLE_LABELS.get(data.get("role", ""), "—")
    status = data.get("employment_status", "none")
    lines  = [
        "📋 <b>Проверь данные перед сохранением</b>",
        "━━━━━━━━━━━━━━━━",
        f"👤  Роль:          {role}",
        f"🎓  Факультет:    {data.get('faculty') or '—'}",
        f"📅  Поступление:  {data.get('enrollment_year') or '—'}",
    ]
    if data.get("graduation_year"):
        lines.append(f"🏁  Выпуск:        {data['graduation_year']}")

    if status == "working":
        lines += [
            "━━━━━━━━━━━━━━━━",
            f"🏢  Компания:     {data.get('company_name') or '—'}",
            f"🌆  Город:        {data.get('work_city') or '—'}",
            f"🔀  Формат:       {FORMAT_LABELS.get(data.get('work_format', ''), '—')}",
            f"👔  Должность:    {data.get('position_title') or '—'}",
            f"📈  Уровень:      {LEVEL_LABELS.get(data.get('position_level', ''), '—')}",
        ]
    else:
        status_str = "Ищу работу 🔍" if status == "searching" else "Не работаю ❌"
        lines += ["━━━━━━━━━━━━━━━━", f"💼  Занятость:    {status_str}"]

    lines.append("━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
