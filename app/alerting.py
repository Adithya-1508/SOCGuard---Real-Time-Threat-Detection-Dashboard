# app/alerting.py
import os
import json
import datetime
import asyncio
from email.message import EmailMessage
import aiosmtplib
import httpx

# SQLAlchemy synch engine for worker thread
from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from .models import Alert


# -----------------------
# ENV VARS
# -----------------------
ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

DATABASE_SYNC_URL = os.getenv(
    "DATABASE_SYNC_URL",
    "postgresql://threatuser:threatpass@localhost:5432/threatdb"
)


# Sync engine (used only in worker thread)
sync_engine = create_engine(DATABASE_SYNC_URL, future=True)


# ------------------------------------------------------------
# 1) Store alert in DB — SYNC — runs inside worker thread
# ------------------------------------------------------------
def _store_alert_sync(alert: dict):
    """Store alert in PostgreSQL using synchronous SQLAlchemy.

    This avoids async-loop issues in the worker thread.
    """

    try:
        # Convert Python dict → valid JSON for PostgreSQL
        details_json = json.dumps(alert["details"], default=str)

        with sync_engine.connect() as conn:
            stmt = (
                insert(Alert)
                .values(
                    created_at=datetime.datetime.utcnow(),
                    severity=alert["severity"],
                    source=alert["source"],
                    summary=alert["summary"],
                    details=details_json,
                    ip=alert["ip"],
                    status="open",
                    reputation_score=alert.get("reputation_score"),
                    threat_tags=alert.get("threat_tags"),
                    latitude=alert.get("latitude"),
                    longitude=alert.get("longitude"),
                    explanation=alert.get("explanation"),
                    agent_report=alert.get("agent_report"),
                )
                .returning(Alert.id)
            )

            result = conn.execute(stmt)
            conn.commit()

            aid = result.scalar()
            print(f"[ALERT] Stored alert ID={aid}")
            return aid

    except Exception as e:
        print(f"[DB-sync ERROR] {e}")
        return None


# ------------------------------------------------------------
# 2) Async wrapper — runs sync DB insert inside worker thread
# ------------------------------------------------------------
async def store_alert(alert: dict):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _store_alert_sync, alert)


# ------------------------------------------------------------
# 3) Send webhook
# ------------------------------------------------------------
async def send_webhook(alert: dict):
    if not ALERT_WEBHOOK:
        return

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            await client.post(ALERT_WEBHOOK, json=alert)
            print("[WEBHOOK] Sent")
    except Exception as e:
        print("[WEBHOOK ERROR]", e)


# ------------------------------------------------------------
# 4) Send email alert (optional)
# ------------------------------------------------------------
async def send_email(subject: str, body: str, to_addrs: list):
    if not SMTP_HOST or not SMTP_USER:
        print("[EMAIL] SMTP disabled — skipping")
        return

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
            start_tls=True,
        )
        print("[EMAIL] Sent!")

    except Exception as e:
        print("[EMAIL ERROR]", e)


# ------------------------------------------------------------
# 5) Main entry for creating + delivering alerts
# ------------------------------------------------------------
async def create_and_notify(event: dict, severity: float, extra: dict):
    from .utils import summarize_event

    summary = summarize_event(event)

    enrich_data = extra.get("enrich", {})
    
    alert = {
        "severity": severity,
        "source": event.get("source"),
        "summary": summary,
        "details": {"event": event, "extra": extra},
        "ip": str(event.get("ip")),
        "reputation_score": enrich_data.get("reputation"),
        "threat_tags": json.dumps(enrich_data.get("tags")) if enrich_data.get("tags") else None,
        "latitude": enrich_data.get("latitude"),
        "longitude": enrich_data.get("longitude"),
        "explanation": extra.get("explanation"),
        "agent_report": extra.get("agent_report"),
    }

    # store alert
    aid = await store_alert(alert)
    alert["id"] = aid

    if aid is None:
        print("[ALERT] Failed to save alert (aid=None)")
    else:
        print(f"[ALERT] Alert created: ID {aid} — Sev={severity}")

    # notify parallel
    from app.websockets import manager
    broadcast_data = {"type": "new_alert", "payload": alert}
    await asyncio.gather(
        send_webhook(alert),
        manager.broadcast(broadcast_data),
        send_email(
            f"Security Alert [{severity:.2f}]",
            summary,
            ["soc@example.com"],
        ),
    )

    return alert
