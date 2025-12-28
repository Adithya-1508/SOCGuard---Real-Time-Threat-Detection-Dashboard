# app/collector.py
from fastapi import APIRouter
from .schemas import EventIn
from .tasks import enqueue_event
from .auth import get_current_user
from .models import User
from fastapi import Depends

router = APIRouter()

@router.post("/ingest")
async def ingest_event(evt: EventIn, user: User = Depends(get_current_user)):
    data = evt.dict()

    # FIX: Convert IPv4Address → string
    if data.get("ip"):
        data["ip"] = str(data["ip"])

    await enqueue_event(data)
    return {"status": "queued"}
