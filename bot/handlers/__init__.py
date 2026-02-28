"""
All routers are imported here and exposed as a single list.
bot/main.py includes them in order — earlier routers have higher priority.
"""
from .start import router as start_router
from .profile import router as profile_router
from .employment import router as employment_router
from .stats import router as stats_router
from .privacy import router as privacy_router
from .achievements import router as achievements_router
from .events import router as events_router
from .help import router as help_router

all_routers = [
    start_router,      # /start + onboarding FSM — must be first
    employment_router, # /update FSM
    profile_router,
    stats_router,
    privacy_router,
    achievements_router,
    events_router,
    help_router,
]

__all__ = ["all_routers"]
