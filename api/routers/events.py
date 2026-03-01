from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import get_session
from db.models import Event, EventsAttendance
from pydantic import BaseModel
from datetime import datetime
from bot.notifiers import notify_new_event, notify_event_update
from datetime import datetime
from typing import Optional
import asyncio

router = APIRouter()

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    event_type: Optional[str] = None
    min_level: int = 1

async def get_db_session():
    async with get_session() as session:
        yield session

@router.get("/")
async def get_events(session: AsyncSession = Depends(get_db_session)):
    query = (
        select(Event, func.count(EventsAttendance.user_id).label('participants_count'))
        .outerjoin(EventsAttendance, Event.id == EventsAttendance.event_id)
        .group_by(Event.id)
        .order_by(Event.event_date.desc())
    )
    result = await session.execute(query)
    
    events = []
    for event_obj, count in result:
        e = event_obj.__dict__.copy()
        e.pop("_sa_instance_state", None)
        e["participants_count"] = count
        events.append(e)
        
    return events

@router.post("/")
async def create_event(event: EventCreate, session: AsyncSession = Depends(get_db_session)):
    new_event = Event(
        title=event.title,
        description=event.description,
        event_date=event.event_date.replace(tzinfo=None) if event.event_date else None,
        event_type=event.event_type,
        min_level=event.min_level
    )
    session.add(new_event)
    await session.commit()
    try:
        asyncio.create_task(notify_new_event(new_event.id))
    except Exception as e:
        print("Note: Failed to notify about new event:", e)
    return {"status": "ok", "id": new_event.id}

@router.delete("/{event_id}")
async def delete_event(event_id: int, session: AsyncSession = Depends(get_db_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await session.execute(delete(EventsAttendance).where(EventsAttendance.event_id == event_id))
    await session.delete(event)
    await session.flush()
    return {"status": "ok"}

@router.put("/{event_id}")
async def update_event(event_id: int, event_update: EventCreate, session: AsyncSession = Depends(get_db_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    new_date = event_update.event_date.replace(tzinfo=None) if event_update.event_date else None
        
    changes_desc = []
    if event.event_date != new_date:
        changes_desc.append("Дата/время изменены")
    if event.description != event_update.description:
        changes_desc.append("Описание изменено")
    if event.min_level != event_update.min_level:
        changes_desc.append("Изменен минимальный уровень")
    if event.title != event_update.title:
        changes_desc.append("Изменено название")
        
    event.title = event_update.title
    event.description = event_update.description
    event.event_date = new_date
    event.event_type = event_update.event_type
    event.min_level = event_update.min_level
    
    await session.commit()
    
    if changes_desc:
        try:
            asyncio.create_task(notify_event_update(event.id, ", ".join(changes_desc)))
        except Exception as e:
            print("Note: Failed to notify about updated event:", e)
            
    return {"status": "ok", "id": event.id}
