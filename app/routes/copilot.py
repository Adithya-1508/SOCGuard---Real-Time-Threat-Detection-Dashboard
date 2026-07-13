# app/routes/copilot.py
import os
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from app.db import get_session
from app.models import Alert, Playbook, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

class ChatRequest(BaseModel):
    alert_id: int
    message: str
    history: Optional[List[dict]] = []

def cosine_similarity(v1: list, v2: list) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = sum(x * x for x in v1) ** 0.5
    norm_v2 = sum(x * x for x in v2) ** 0.5
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

async def generate_embedding(text: str) -> List[float]:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key or api_key == "your_nvidia_api_key_here":
        return [0.0] * 1024 # Dummy 1024-dim vector

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": [text],
        "model": "nvidia/embeddings-nv-embed-qa-4",
        "input_type": "query",
        "encoding_format": "float"
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post("https://integrate.api.nvidia.com/v1/embeddings", json=payload, headers=headers)
            if r.status_code == 200:
                return r.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"[-] Embedding Generation Failed: {e}")
    return [0.0] * 1024

async def seed_playbooks_if_empty(session: AsyncSession):
    stmt = select(Playbook)
    result = await session.execute(stmt)
    if result.scalars().first() is not None:
        return

    print("[COPILOT] Seeding security playbooks...")
    default_playbooks = [
        {
            "name": "Port Scan Mitigation Playbook",
            "description": "Guides analysts on handling high-frequency distributed port scanning alerts.",
            "steps": "1. Identify the scanning source IP.\n2. Correlate with firewall block logs to confirm traffic was dropped.\n3. Search subnet activity for secondary scans.\n4. Apply a temporary perimeter firewall block rule if scan continues."
        },
        {
            "name": "Brute Force Authentication Triage",
            "description": "Steps for triaging repeated authentication and login failures.",
            "steps": "1. Identify target accounts (e.g., admin, root).\n2. Review source IP against known Tor exit nodes or hosting networks.\n3. If localized to one account, recommend password rotation or lock.\n4. Enable multi-factor authentication (MFA) enforcement."
        },
        {
            "name": "Suspicious Process Remediation",
            "description": "Remediation protocols for endpoint command-line anomalies (e.g. netcat, reverse shell).",
            "steps": "1. Isolate the affected host from the local network segment.\n2. Dump the active process execution tree.\n3. Terminate the anomalous process PID.\n4. Perform threat hunt for startup registry key hooks or cron jobs."
        }
    ]

    for p in default_playbooks:
        text_to_embed = f"{p['name']}\n{p['description']}\n{p['steps']}"
        embedding = await generate_embedding(text_to_embed)
        playbook = Playbook(
            name=p["name"],
            description=p["description"],
            steps=p["steps"],
            embedding=json.dumps(embedding)
        )
        session.add(playbook)
    await session.commit()

@router.get("/playbooks")
async def list_playbooks(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    await seed_playbooks_if_empty(session)
    stmt = select(Playbook)
    result = await session.execute(stmt)
    playbooks = result.scalars().all()
    return [{"id": p.id, "name": p.name, "description": p.description, "steps": p.steps} for p in playbooks]

@router.post("/chat")
async def copilot_chat(
    req: ChatRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    # Ensure playbooks exist
    await seed_playbooks_if_empty(session)

    # 1. Fetch Alert Context
    stmt = select(Alert).where(Alert.id == req.alert_id)
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # 2. Embed user message to retrieve relevant playbook
    msg_embedding = await generate_embedding(req.message)

    # 3. Retrieve and calculate cosine similarity
    stmt_playbooks = select(Playbook)
    res_playbooks = await session.execute(stmt_playbooks)
    playbooks = res_playbooks.scalars().all()

    best_playbook = None
    best_similarity = -1.0

    for p in playbooks:
        if p.embedding:
            p_embed = json.loads(p.embedding)
            sim = cosine_similarity(msg_embedding, p_embed)
            if sim > best_similarity:
                best_similarity = sim
                best_playbook = p

    playbook_context = ""
    if best_playbook and best_similarity > 0.1: # Threshold similarity
        playbook_context = (
            f"Matching Playbook: {best_playbook.name}\n"
            f"Playbook Description: {best_playbook.description}\n"
            f"Remediation Steps:\n{best_playbook.steps}"
        )
    else:
        playbook_context = "No highly matching playbook found. Use standard threat response strategies."

    # 4. Formulate LLM query to NVIDIA NIM
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key or api_key == "your_nvidia_api_key_here":
        return {"response": "NVIDIA API Key not configured. Copilot unavailable."}

    system_message = (
        "You are an expert Security Copilot integrated into a SOC Dashboard. "
        "Your goal is to guide the security analyst through investigating and remediating the alert. "
        "Use the provided playbook context and alert details to formulate a precise, actionable response."
    )

    alert_details = (
        f"Alert Summary: {alert.summary}\n"
        f"Source: {alert.source}\n"
        f"Severity Score: {alert.severity}\n"
        f"IP Address: {alert.ip}\n"
        f"Status: {alert.status}\n"
        f"Threat Intel Score: {alert.reputation_score}\n"
        f"AI Explanation: {alert.explanation or 'Not available'}"
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "system", "content": f"--- ALERT DETAILS ---\n{alert_details}"},
        {"role": "system", "content": f"--- SECURITY PLAYBOOK CONTEXT ---\n{playbook_context}"}
    ]

    # Append chat history
    for item in req.history:
        messages.append(item)

    # Append new user message
    messages.append({"role": "user", "content": req.message})

    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 400
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post("https://integrate.api.nvidia.com/v1/chat/completions", json=payload, headers=headers)
            if r.status_code == 200:
                reply = r.json()["choices"][0]["message"]["content"]
                return {"response": reply, "playbook": best_playbook.name if best_playbook else None}
            else:
                return {"response": f"NVIDIA API Error: {r.status_code} - {r.text}"}
    except Exception as e:
        return {"response": f"Copilot execution failed: {e}"}
