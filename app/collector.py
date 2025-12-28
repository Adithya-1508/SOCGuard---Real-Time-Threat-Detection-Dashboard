from fastapi import APIRouter, Depends
from .schemas import EventIn
from .tasks import enqueue_event
from .auth import get_ingestion_auth

router = APIRouter()

@router.post("/ingest")
async def ingest_event(evt: EventIn, auth: any = Depends(get_ingestion_auth)):
    data = evt.dict()

    # FIX: Convert IPv4Address → string
    if data.get("ip"):
        data["ip"] = str(data["ip"])

    await enqueue_event(data)
    return {"status": "queued"}
