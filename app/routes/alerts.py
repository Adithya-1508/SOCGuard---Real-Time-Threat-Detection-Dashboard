# app/routes/alerts.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Alert, Comment, User
from app.auth import get_current_user
from datetime import datetime, timedelta
from app.websockets import manager

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f"🔌 [WS] Connection attempt from {websocket.client}")
    try:
        await manager.connect(websocket)
        print("✅ [WS] Client connected successfully")
        while True:
            # Keep connection alive, maybe listen for client pings
            data = await websocket.receive_text()
            print(f"📩 [WS] Received: {data}")
    except WebSocketDisconnect:
        print("⚠️ [WS] Client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ [WS] Error: {e}")
        manager.disconnect(websocket)

@router.get("/")
async def list_alerts(
    skip: int = 0, 
    limit: int = 10, 
    severity: str = None,
    status: str = None,
    source: str = None,
    search: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(Alert).order_by(desc(Alert.created_at))

    # Apply filters
    if severity:
        if severity == "critical": query = query.where(Alert.severity >= 0.8)
        elif severity == "high": query = query.where(Alert.severity >= 0.6, Alert.severity < 0.8)
        elif severity == "medium": query = query.where(Alert.severity >= 0.4, Alert.severity < 0.6)
        elif severity == "low": query = query.where(Alert.severity < 0.4)
    
    if status:
        query = query.where(Alert.status == status)
    
    if source:
        query = query.where(Alert.source == source)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Alert.summary.ilike(search_term)) | 
            (Alert.source.ilike(search_term)) | 
            (Alert.ip.ilike(search_term))
        )
    
    if start_time:
        query = query.where(Alert.created_at >= start_time)
    
    if end_time:
        query = query.where(Alert.created_at <= end_time)

    # Get total count (inefficient but simple for now)
    # Ideally we'd clone the query and replace select with count
    # For now, let's just execute and count (not scalable for millions of rows)
    # Better approach:
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Pagination
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    alerts = result.scalars().all()
    
    # Map severity float to string label for frontend
    def map_severity(score):
        if score >= 0.8: return "critical"
        if score >= 0.6: return "high"
        if score >= 0.4: return "medium"
        return "low"

    return {
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "items": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "severity": map_severity(a.severity),
                "severity_score": a.severity,
                "source": a.source,
                "summary": a.summary,
                "details": a.details,
                "ip": a.ip,
                "status": a.status,
                "reputation_score": a.reputation_score,
                "threat_tags": a.threat_tags,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "explanation": a.explanation,
                "agent_report": a.agent_report,
            }
            for a in alerts
        ]
    }

from datetime import datetime, timedelta, timezone

# ... imports ...

@router.get("/chart/")
async def get_chart_data(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Align to the start of the current hour in UTC
    now = datetime.now(timezone.utc)
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    
    # We want 24 hours of data: from (current_hour - 23h) to (current_hour + 1h)
    # Actually, usually we show last 24h. So [current_hour - 23h, current_hour]
    start_time = current_hour - timedelta(hours=23)
    
    stmt = select(Alert.created_at).where(Alert.created_at >= start_time)
    result = await session.execute(stmt)
    dates = result.scalars().all()

    # Initialize buckets for the last 24 hours
    # Map timestamp (hour start) to count
    buckets = {}
    for i in range(24):
        t = start_time + timedelta(hours=i)
        buckets[t] = 0

    for d in dates:
        if d:
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            
            # Truncate to hour
            d_hour = d.replace(minute=0, second=0, microsecond=0)
            
            if d_hour in buckets:
                buckets[d_hour] += 1
    
    # Format for frontend
    chart_data = []
    for i in range(24):
        t = start_time + timedelta(hours=i)
        chart_data.append({
            "name": t.strftime("%H:00"),
            "alerts": buckets[t],
            "timestamp": t.isoformat()
        })
    return chart_data

@router.get("/stats/")
async def get_stats(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Total Active Alerts (status != 'closed')
    total_stmt = select(func.count(Alert.id)).where(Alert.status != "closed")
    total_result = await session.execute(total_stmt)
    total_active = total_result.scalar() or 0

    # Alerts in last 24h
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_stmt = select(func.count(Alert.id)).where(Alert.created_at >= yesterday)
    recent_result = await session.execute(recent_stmt)
    recent_count = recent_result.scalar() or 0

    # High Severity Count
    high_sev_stmt = select(func.count(Alert.id)).where(Alert.severity >= 0.6)
    high_sev_result = await session.execute(high_sev_stmt)
    high_sev_count = high_sev_result.scalar() or 0

    return {
        "active_alerts": total_active,
        "recent_alerts": recent_count,
        "high_severity": high_sev_count,
        "system_health": 98 # Mock value for now
    }

class AlertUpdate(BaseModel):
    status: str | None = None
    assigned_to: int | None = None

class CommentCreate(BaseModel):
    content: str

@router.patch("/{alert_id}")
async def update_alert(alert_id: int, update: AlertUpdate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # IDOR Protection: Check if user is admin or assigned to this alert
    if user.role != "admin" and alert.assigned_to != user.id:
        # If it's not assigned to anyone yet, we might allow an analyst to "claim" it
        if alert.assigned_to is not None:
             raise HTTPException(status_code=403, detail="Not authorized to modify this alert")
    
    if update.status:
        alert.status = update.status
    if update.assigned_to is not None:
        alert.assigned_to = update.assigned_to
        
    await session.commit()
    await session.refresh(alert)
    return alert

@router.post("/{alert_id}/comments")
async def add_comment(alert_id: int, comment: CommentCreate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    new_comment = Comment(alert_id=alert_id, user_id=user.id, content=comment.content)
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    return new_comment

@router.get("/{alert_id}/comments")
async def get_comments(alert_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Join with User to get commenter name
    stmt = select(Comment, User.full_name).join(User).where(Comment.alert_id == alert_id).order_by(Comment.created_at.asc())
    result = await session.execute(stmt)
    
    comments = []
    for comment, user_name in result:
        comments.append({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "user_name": user_name
        })
    return comments
from app.actions import execute_action

class ActionRequest(BaseModel):
    action: str

@router.post("/{alert_id}/actions")
async def trigger_action(alert_id: int, request: ActionRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    try:
        message = await execute_action(alert, request.action, user, session)
        await session.commit()
        return {"status": "success", "message": message}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Action failed: {e}")
        raise HTTPException(status_code=500, detail="Action execution failed")

import csv
import io
from fastapi.responses import StreamingResponse

@router.get("/export", response_class=StreamingResponse)
async def export_alerts(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Fetch all alerts
    stmt = select(Alert).order_by(desc(Alert.created_at))
    result = await session.execute(stmt)
    alerts = result.scalars().all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Created At", "Severity", "Source", "IP", "Summary", "Status", "Reputation Score", "Threat Tags"])
    
    # Rows
    for alert in alerts:
        writer.writerow([
            alert.id,
            alert.created_at,
            alert.severity,
            alert.source,
            alert.ip,
            alert.summary,
            alert.status,
            alert.reputation_score,
            alert.threat_tags
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alerts.csv"}
    )
