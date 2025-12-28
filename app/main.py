import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
from .tasks import start_worker_in_thread, start_redis_listener

app = FastAPI(title="Threat Detection Agent")

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],   # Restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:;"
    return response


@app.on_event("startup")
async def on_startup():
    print("🚀 [APP] Running database migrations...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("⚙️ [APP] Starting worker thread now...")
    start_worker_in_thread()
    start_redis_listener()

from .collector import router as collector_router
app.include_router(collector_router, prefix="/api")
from app.routes.alerts import router as alerts_router
app.include_router(alerts_router)
from app.routes.auth import router as auth_router
app.include_router(auth_router)
from app.routes.settings import router as settings_router
app.include_router(settings_router)
