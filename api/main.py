import logging
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot.config import get_settings
from db.base import init_db

from api.routers import stats, users, events

cfg = get_settings()
bot = Bot(token=cfg.bot_token)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await bot.session.close()

app = FastAPI(title="AlmaTrack API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")
app.include_router(stats.router, prefix="/api/stats")
app.include_router(events.router, prefix="/api/events")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "db": "ok", "bot": "running"}
