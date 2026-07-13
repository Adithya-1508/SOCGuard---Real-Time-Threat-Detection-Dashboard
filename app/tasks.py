# app/tasks.py

import os
import json
import threading
import asyncio
from redis import Redis

from .detector import add_and_maybe_train, score_event
from .enricher import enrich_ip
from .alerting import create_and_notify

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL, decode_responses=True)

EVENT_LIST = "events_queue"

# ------------------------------
# WORKER EVENT LOOP (CORRECT FIX)
# ------------------------------

# Create ONE event loop for worker thread
worker_loop = asyncio.new_event_loop()

def start_worker_loop():
    asyncio.set_event_loop(worker_loop)
    worker_loop.run_forever()

# Start loop in background thread
def start_worker_in_thread():
    t = threading.Thread(target=start_worker_loop, daemon=True)
    t.start()
    print("[WORKER] Async worker loop started...")

# ------------------------------
# REDIS LISTENER
# ------------------------------

def redis_listener():
    print("[WORKER] Redis listener started")
    while True:
        item = redis.blpop(EVENT_LIST, timeout=5)
        if not item:
            continue

        _, raw = item
        print(f"[WORKER] Pulled event: {raw}")

        event = json.loads(raw)

        # Submit async processing into worker loop
        asyncio.run_coroutine_threadsafe(process_event(event), worker_loop)

def start_redis_listener():
    t = threading.Thread(target=redis_listener, daemon=True)
    t.start()

# ------------------------------
# EVENT PROCESSING LOGIC
# ------------------------------
# AI & MULTI-AGENT SEC-OPS SERVICES
# ------------------------------
import hashlib
import httpx
from sqlalchemy import select
from .models import Alert

async def get_ai_explanation(event: dict) -> str:
    message = event.get("message", "")
    h = hashlib.md5(message.encode()).hexdigest()
    cache_key = f"explain:{h}"
    
    # Try getting from Redis cache
    try:
        cached = redis.get(cache_key)
        if cached:
            print("[CACHE HIT] Returning cached explanation")
            return cached
    except Exception as e:
        print(f"[CACHE ERROR] Redis get failed: {e}")
        
    # Cache miss: generate explanation
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key or api_key == "your_nvidia_api_key_here":
        return "NVIDIA API Key not configured. AI explanation unavailable."
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert security analyst. Briefly explain in 2-3 sentences "
                    "why this system log indicates a threat or anomaly. Keep it technical and concise."
                )
            },
            {
                "role": "user",
                "content": f"Source: {event.get('source')} | IP: {event.get('ip')} | User: {event.get('user')} | Message: {message}"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 150
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post("https://integrate.api.nvidia.com/v1/chat/completions", json=payload, headers=headers)
            if r.status_code == 200:
                explanation = r.json()["choices"][0]["message"]["content"]
                # Save to cache for 24h
                try:
                    redis.setex(cache_key, 86400, explanation)
                except Exception as e:
                    print(f"[CACHE ERROR] Redis set failed: {e}")
                return explanation
            else:
                return f"NVIDIA API Error: {r.status_code}"
    except Exception as e:
        return f"Failed to generate explanation: {e}"

async def get_recent_alerts_context() -> str:
    try:
        from .alerting import sync_engine
        with sync_engine.connect() as conn:
            stmt = select(Alert.summary, Alert.created_at, Alert.severity).order_by(Alert.created_at.desc()).limit(10)
            res = conn.execute(stmt).all()
            lines = [f"- [{r[1]}] {r[0]} (Severity: {r[2]})" for r in res]
            return "\n".join(lines) if lines else "No prior alerts in database."
    except Exception as e:
        return f"Failed to retrieve database context: {e}"

async def run_multi_agent_investigation(event: dict, database_context: str) -> str:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key or api_key == "your_nvidia_api_key_here":
        return "NVIDIA API Key not configured. Multi-agent investigation report unavailable."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 1. Spawn Intel Agent to check IP
    ip = event.get("ip", "")
    intel_report = "No reputation details."
    if ip and ip != "127.0.0.1":
        intel_prompt = f"Analyze this IP address for potential reputation risks or known blocklists: {ip}."
        payload_intel = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [
                {"role": "system", "content": "You are a Threat Intel Agent. Report known risks of the IP."},
                {"role": "user", "content": intel_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 200
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post("https://integrate.api.nvidia.com/v1/chat/completions", json=payload_intel, headers=headers)
                if r.status_code == 200:
                    intel_report = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            intel_report = f"Intel Agent failed: {e}"

    # 2. Spawn Correlation Agent to check historical logs
    correlation_prompt = (
        f"Correlate the new event with this recent alerts history context:\n"
        f"New Event: {event}\n"
        f"Recent History: {database_context}\n"
        f"Find correlation patterns like lateral movement, brute force, or repeated attacks."
    )
    payload_corr = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a Correlation and Threat Hunter Agent. Analyze logs context."},
            {"role": "user", "content": correlation_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 250
    }
    correlation_report = "No correlation context."
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post("https://integrate.api.nvidia.com/v1/chat/completions", json=payload_corr, headers=headers)
            if r.status_code == 200:
                correlation_report = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        correlation_report = f"Correlation Agent failed: {e}"

    # 3. Supervisor Agent orchestrates and compiles the final report
    supervisor_prompt = (
        f"Ingest the following sub-agent investigation findings and compile a cohesive "
        f"Incident Investigation Report (markdown format) with Recommendations:\n\n"
        f"Original Event: {event}\n\n"
        f"--- Threat Intel Agent Findings ---\n{intel_report}\n\n"
        f"--- Correlation Agent Findings ---\n{correlation_report}\n\n"
        f"Write a final executive summary, analysis, and concrete remediation steps."
    )
    payload_super = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "messages": [
            {"role": "system", "content": "You are the Lead Incident Supervisor Agent. Compile unified SOC reports."},
            {"role": "user", "content": supervisor_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post("https://integrate.api.nvidia.com/v1/chat/completions", json=payload_super, headers=headers)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            else:
                return f"Supervisor Agent Error: {r.status_code}"
    except Exception as e:
        return f"Supervisor Agent failed: {e}"

async def enqueue_event(event: dict):
    print("[QUEUE] Received event, pushing into Redis")
    redis.rpush(EVENT_LIST, json.dumps(event))

async def process_event(event: dict):
    print("[PROCESS] Processing event...")

    # 1. Enrichment
    enrich = await enrich_ip(event.get("ip"))
    print(f"[ENRICH RESULT] {enrich}")

    # 2. ML featurization & training
    await add_and_maybe_train(event)

    # 3. anomaly score
    severity = await score_event(event)

    # 4. Rule-based override for known attacks
    if "port scan" in event.get("message", "").lower():
        severity = max(severity, 0.9)

    if "failed login" in event.get("message", "").lower():
        severity = max(severity, 0.7)

    # Real-time Agent Rules
    if "suspicious process" in event.get("message", "").lower():
        severity = max(severity, 0.9)
    
    if "new network connection" in event.get("message", "").lower():
        severity = max(severity, 0.5)

    if "system event" in event.get("message", "").lower():
        severity = max(severity, 0.6)

    # Threat Intelligence Override
    if enrich and enrich.get("reputation", 0) > 0:
        # Normalize 0-100 score to 0.0-1.0 and boost
        ti_score = enrich["reputation"] / 100.0
        severity = max(severity, ti_score)
        print(f"⚠️ [TI BOOST] Severity boosted to {severity} by Threat Intel")

    print(f"⚠️ [SEVERITY] Score = {severity}")

    # 5. alert only if threshold exceeded
    if severity >= 0.3:
        # A. Explainable AI & Caching
        explanation = await get_ai_explanation(event)
        
        # B. Multi-Agent Investigation Report (if critical)
        agent_report = None
        if severity >= 0.6:
            db_context = await get_recent_alerts_context()
            agent_report = await run_multi_agent_investigation(event, db_context)
            
        await create_and_notify(
            event, 
            severity, 
            extra={
                "enrich": enrich, 
                "explanation": explanation, 
                "agent_report": agent_report
            }
        )
        print("[ALERT] Alert created with AI and Multi-Agent reports!")
    else:
        print("ℹ️ [INFO] Event below threshold.")

