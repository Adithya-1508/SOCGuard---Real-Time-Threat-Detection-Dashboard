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
        await create_and_notify(event, severity, extra={"enrich": enrich})
        print("[ALERT] Alert created!")
    else:
        print("ℹ️ [INFO] Event below threshold.")

