# app/routes/auth.py
import os
import random
import string
import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_session
from app.models import User
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user, get_admin_user
from pydantic import BaseModel
from datetime import timedelta
from email.message import EmailMessage
import aiosmtplib

router = APIRouter(prefix="/auth", tags=["auth"])

# Environment Variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Redis Connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str = None
    is_active: bool

    class Config:
        orm_mode = True

class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

async def send_email(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
        # In dev, we might want to just log it if SMTP fails
        pass

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, session: AsyncSession = Depends(get_session)):
    stmt = select(User).where(User.email == user.email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw, full_name=user.full_name)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    stmt = select(User).where(User.email == form_data.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=list[UserResponse])
async def list_users(session: AsyncSession = Depends(get_session), admin_user: User = Depends(get_admin_user)):
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return users

# --- Google OAuth ---
@router.get("/google/login")
async def google_login():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

@router.get("/google/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_session)):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        access_token = response.json().get("access_token")
        
        user_info_response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_info_response.json()
        
    email = user_info.get("email")
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Create user if not exists (random password since they use Google)
        import secrets
        random_pw = secrets.token_urlsafe(16)
        hashed_pw = get_password_hash(random_pw)
        user = User(email=email, hashed_password=hashed_pw, full_name=user_info.get("name"))
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    # Create JWT
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Redirect to frontend with token
    return RedirectResponse(url=f"http://localhost:5173/login?token={access_token}")

# --- Forgot Password (OTP) ---
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    # Simple Rate Limiting
    ip = "unknown" # In a real scenario, use request.client.host
    rate_key = f"rate:forgot:{request.email}"
    count = await redis_client.get(rate_key)
    if count and int(count) > 5:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    await redis_client.incr(rate_key)
    await redis_client.expire(rate_key, 600) # 10 mins window

    stmt = select(User).where(User.email == request.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if user exists
        return {"message": "If email exists, OTP sent."}
    
    otp = "".join(random.choices(string.digits, k=6))
    await redis_client.setex(f"otp:{request.email}", 600, otp) # 10 mins expiry
    
    await send_email(request.email, "Your SOC Dashboard OTP", f"Your OTP is: {otp}")
    
    return {"message": "OTP sent"}

@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest, session: AsyncSession = Depends(get_session)):
    rate_key = f"rate:verify:{request.email}"
    count = await redis_client.get(rate_key)
    if count and int(count) > 5:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    await redis_client.incr(rate_key)
    await redis_client.expire(rate_key, 600)

    stored_otp = await redis_client.get(f"otp:{request.email}")
    
    if not stored_otp or stored_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # OTP valid, log them in
    stmt = select(User).where(User.email == request.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
         raise HTTPException(status_code=400, detail="User not found")

    await redis_client.delete(f"otp:{request.email}")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
