"""Stats screen."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NavCB, stats_keyboard

router = Router(name="stats")


def _stats_text() -> str:
    # TODO: fetch from DB
    faculty     = "Информационные технологии"
    user_level  = "junior"
    dist = {"intern": 10, "junior": 18, "middle": 9, "senior": 4, "lead": 1}
    dist_lines = "\n".join(
        f"  {'→' if k == user_level else ' '} {k.capitalize()}: {v} чел."
        for k, v in dist.items()
    )
    return (
        f"📊 <b>Статистика по факультету</b>\n"
        f"🎓 {faculty}\n\n"
        f"👥 Всего с данными: 42\n\n"
        f"📈 <b>По уровням:</b>\n{dist_lines}\n\n"
        "🏢 <b>Топ компании:</b> Яндекс, Сбер, VK\n"
        "🌆 <b>Топ города:</b> Москва, СПб\n"
        "⏱ <b>Среднее до Junior:</b> 8 мес.\n\n"
        "🔒 Данные обезличены."
    )


async def _show(target) -> None:
    text = _stats_text()
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=stats_keyboard(), parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=stats_keyboard(), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=stats_keyboard(), parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await _show(message)


@router.callback_query(NavCB.filter(F.page == "stats"))
async def nav_stats(call: CallbackQuery) -> None:
    await _show(call)
