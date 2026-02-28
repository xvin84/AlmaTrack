"""
Premium emoji helper.

Usage:
    from core.emoji import em
    from bot.config import get_settings

    cfg = get_settings()
    text = f"{em(cfg.emoji_star, '⭐')} {xp} XP"

If the emoji_id is empty the plain fallback character is returned.
If it is set the Telegram custom emoji tag is used — this requires
parse_mode=HTML and the bot must be running in a chat where the user
has Telegram Premium (or the emoji is from the bot's sticker pack).
"""
from __future__ import annotations


def em(emoji_id: str, fallback: str) -> str:
    """
    Return a premium emoji tag if emoji_id is set, otherwise the plain fallback.

    Args:
        emoji_id:  Telegram custom emoji ID (e.g. "5368324170671202286")
                   Empty string → use fallback.
        fallback:  Regular Unicode emoji used as display text and as fallback.
    """
    if emoji_id:
        return f'<tg-emoji emoji_id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback


# ---------------------------------------------------------------------------
# Pre-built shortcut object so callers don't have to pass cfg manually
# ---------------------------------------------------------------------------

class _EmojiSet:
    """
    Lazy wrapper that reads settings once and exposes named emoji helpers.

    Usage:
        from core.emoji import E
        text = f"{E.star} {xp} XP"
    """

    _cfg = None

    @classmethod
    def _get(cls):
        if cls._cfg is None:
            from bot.config import get_settings
            cls._cfg = get_settings()
        return cls._cfg

    @property
    def star(self) -> str:
        return em(self._get().emoji_star, "⭐")

    @property
    def fire(self) -> str:
        return em(self._get().emoji_fire, "🔥")

    @property
    def trophy(self) -> str:
        return em(self._get().emoji_trophy, "🏆")

    @property
    def crown(self) -> str:
        return em(self._get().emoji_crown, "👑")

    @property
    def rocket(self) -> str:
        return em(self._get().emoji_rocket, "🚀")

    @property
    def chart(self) -> str:
        return em(self._get().emoji_chart, "📈")

    @property
    def lock(self) -> str:
        return em(self._get().emoji_lock, "🔒")

    @property
    def sparkles(self) -> str:
        return em(self._get().emoji_sparkles, "✨")

    @property
    def medal(self) -> str:
        return em(self._get().emoji_medal, "🎖")

    @property
    def diamond(self) -> str:
        return em(self._get().emoji_diamond, "💎")


E = _EmojiSet()
