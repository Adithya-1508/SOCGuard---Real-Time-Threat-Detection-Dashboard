from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import SystemSettings, User
from app.auth import get_admin_user
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

@router.get("/")
async def get_settings(session: AsyncSession = Depends(get_session), admin_user: User = Depends(get_admin_user)):
    stmt = select(SystemSettings)
    result = await session.execute(stmt)
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}

@router.post("/")
async def update_settings(update_data: SettingsUpdate, session: AsyncSession = Depends(get_session), admin_user: User = Depends(get_admin_user)):
    for key, value in update_data.settings.items():
        # Check if exists
        stmt = select(SystemSettings).where(SystemSettings.key == key)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = str(value)
        else:
            new_setting = SystemSettings(key=key, value=str(value))
            session.add(new_setting)
    
    await session.commit()
    return {"status": "updated"}
