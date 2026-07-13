# app/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_session
from app.models import User
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENV") == "production":
        raise RuntimeError("SECRET_KEY environment variable is required in production mode!")
    import warnings
    warnings.warn("SECRET_KEY is not set. Using insecure fallback secret key for development.")
    SECRET_KEY = "fallback-insecure-key-do-not-use-in-production"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

COLLECTOR_TOKEN = os.getenv("COLLECTOR_TOKEN")
if not COLLECTOR_TOKEN:
    if os.getenv("ENV") == "production":
        raise RuntimeError("COLLECTOR_TOKEN environment variable is required in production mode!")
    import warnings
    warnings.warn("COLLECTOR_TOKEN is not set. Using insecure fallback collector token for development.")
    COLLECTOR_TOKEN = "super-secret-collector-token"

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)
api_key_header = APIKeyHeader(name="X-Collector-Token", auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user

async def get_ingestion_auth(
    token: Optional[str] = Depends(oauth2_scheme), 
    api_key: Optional[str] = Depends(api_key_header),
    session: AsyncSession = Depends(get_session)
):
    # Check for Collector API Key first
    if api_key and api_key == COLLECTOR_TOKEN:
        return "collector_agent"
    
    # Otherwise, try standard user authentication
    if token:
        try:
            return await get_current_user(token, session)
        except HTTPException:
            pass
            
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid User Token or Collector Key (X-Collector-Token) required"
    )
